#!/usr/bin/env python3
"""Map Codex app-server JSONL messages into TurnScope events."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

BASE_TIME = datetime(2026, 1, 1, tzinfo=timezone.utc)
SUPPORTED_TOOL_ITEMS = {'mcpToolCall', 'dynamicToolCall', 'webSearch'}
APPROVAL_METHODS = {
    'item/commandExecution/requestApproval',
    'item/fileChange/requestApproval',
    'item/permissions/requestApproval',
}


class TimestampSynthesizer:
    def __init__(self) -> None:
        self._offset = 0

    def next(self) -> str:
        timestamp = BASE_TIME + timedelta(seconds=self._offset)
        self._offset += 1
        return timestamp.isoformat().replace('+00:00', 'Z')


def load_messages(path: Path) -> List[Dict[str, Any]]:
    messages: List[Dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            messages.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f'invalid JSON on line {line_number}: {exc}') from exc
    return messages


def extract_session_id(message: Dict[str, Any]) -> str:
    params = message.get('params', {})
    turn = params.get('turn', {})
    item = params.get('item', {})
    return (
        params.get('threadId')
        or turn.get('threadId')
        or item.get('threadId')
        or params.get('senderThreadId')
        or params.get('receiverThreadId')
        or 'unknown-thread'
    )


def extract_turn_id(message: Dict[str, Any]) -> Optional[str]:
    params = message.get('params', {})
    turn = params.get('turn', {})
    return params.get('turnId') or turn.get('id')


def select_timestamp(message: Dict[str, Any], synthesizer: TimestampSynthesizer) -> str:
    for key in ('receivedAt', 'timestamp'):
        if isinstance(message.get(key), str) and message[key]:
            return message[key]

    params = message.get('params', {})
    turn = params.get('turn')
    item = params.get('item')
    for candidate in (turn, item):
        if isinstance(candidate, dict):
            for key in ('startedAt', 'completedAt', 'updatedAt'):
                if isinstance(candidate.get(key), str) and candidate[key]:
                    return candidate[key]
    return synthesizer.next()


def event_id(prefix: str, value: Optional[str], index: int) -> str:
    if value:
        return f'{prefix}_{value}'
    return f'{prefix}_{index:04d}'


def to_event(
    index: int,
    message: Dict[str, Any],
    synthesizer: TimestampSynthesizer,
    event_type: str,
    session_id: str,
    payload: Dict[str, Any],
    turn_id: Optional[str] = None,
    agent_id: Optional[str] = 'codex',
    parent_id: Optional[str] = None,
    component: str = 'adapter',
    event_id_value: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None,
    occurred_at: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        'version': '0.1.0',
        'id': event_id(event_type.replace('.', '_'), event_id_value, index),
        'type': event_type,
        'occurred_at': occurred_at or select_timestamp(message, synthesizer),
        'session_id': session_id,
        'turn_id': turn_id,
        'agent_id': agent_id,
        'parent_id': parent_id,
        'source': {
            'runtime': 'codex',
            'component': component,
            'origin': 'adapter-codex-app-server',
        },
        'payload': payload,
        'attributes': attributes or {},
    }


def collect_session_meta(messages: Iterable[Dict[str, Any]], synthesizer: TimestampSynthesizer) -> Dict[str, Dict[str, Any]]:
    meta: Dict[str, Dict[str, Any]] = {}
    for message in messages:
        session_id = extract_session_id(message)
        occurred_at = select_timestamp(message, synthesizer)
        session = meta.setdefault(
            session_id,
            {
                'first_timestamp': occurred_at,
                'last_timestamp': occurred_at,
                'status': 'running',
            },
        )
        session['first_timestamp'] = min(session['first_timestamp'], occurred_at)
        session['last_timestamp'] = max(session['last_timestamp'], occurred_at)

        method = message.get('method')
        params = message.get('params', {})
        turn = params.get('turn', {})
        if method == 'turn/completed':
            session['status'] = turn.get('status', session['status'])
        elif method == 'error':
            session['status'] = 'failed'
    return meta


def method_key(message: Dict[str, Any]) -> str:
    method = message.get('method', 'unknown')
    params = message.get('params', {})
    item = params.get('item', {})
    item_type = item.get('type')
    if method in {'item/started', 'item/completed'} and item_type:
        return f'{method}:{item_type}'
    return method


def map_messages_with_report(messages: Iterable[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    messages = list(messages)
    timestamp_synthesizer = TimestampSynthesizer()
    session_meta = collect_session_meta(messages, timestamp_synthesizer)

    event_synthesizer = TimestampSynthesizer()
    approval_requests: Dict[Any, Dict[str, Any]] = {}
    timeline: List[Tuple[Tuple[str, int], Dict[str, Any]]] = []
    unmapped_methods: Counter[str] = Counter()
    mapped_methods: Counter[str] = Counter()
    session_started_emitted = set()
    session_finished_candidates: Dict[str, Dict[str, Any]] = {}

    def add_event(sort_key: Tuple[str, int], event: Dict[str, Any]) -> None:
        timeline.append((sort_key, event))

    for index, message in enumerate(messages, start=1):
        method = message.get('method')
        metric_key = method_key(message)
        params = message.get('params', {})
        turn = params.get('turn', {})
        item = params.get('item', {})
        session_id = extract_session_id(message)
        turn_id = extract_turn_id(message)
        occurred_at = select_timestamp(message, event_synthesizer)

        if session_id not in session_started_emitted:
            session_started_emitted.add(session_id)
            session_start = to_event(
                0,
                message,
                event_synthesizer,
                'session.started',
                session_id=session_id,
                turn_id=None,
                payload={'status': 'running'},
                component='session',
                event_id_value=session_id,
                occurred_at=session_meta[session_id]['first_timestamp'],
            )
            add_event((session_start['occurred_at'], -1), session_start)

        handled = False

        if method == 'turn/started':
            add_event(
                (occurred_at, index),
                to_event(
                    index,
                    message,
                    event_synthesizer,
                    'turn.started',
                    session_id=session_id,
                    turn_id=turn.get('id'),
                    payload={'status': turn.get('status', 'inProgress')},
                    component='turn',
                    event_id_value=turn.get('id'),
                    occurred_at=occurred_at,
                ),
            )
            handled = True
        elif method == 'turn/completed':
            payload = {'status': turn.get('status', 'completed')}
            if isinstance(turn.get('error'), dict):
                payload['error'] = turn['error']
            add_event(
                (occurred_at, index),
                to_event(
                    index,
                    message,
                    event_synthesizer,
                    'turn.finished',
                    session_id=session_id,
                    turn_id=turn.get('id'),
                    payload=payload,
                    component='turn',
                    event_id_value=turn.get('id'),
                    occurred_at=occurred_at,
                ),
            )
            handled = True
        elif method == 'item/started' and item.get('type') == 'commandExecution':
            add_event(
                (occurred_at, index),
                to_event(
                    index,
                    message,
                    event_synthesizer,
                    'shell.started',
                    session_id=session_id,
                    turn_id=turn_id,
                    payload={
                        'shell_id': item.get('id'),
                        'command': item.get('command'),
                        'cwd': item.get('cwd'),
                    },
                    component='shell',
                    event_id_value=item.get('id'),
                    attributes={'status': item.get('status')},
                    occurred_at=occurred_at,
                ),
            )
            handled = True
        elif method == 'item/commandExecution/outputDelta':
            add_event(
                (occurred_at, index),
                to_event(
                    index,
                    message,
                    event_synthesizer,
                    'shell.output',
                    session_id=session_id,
                    turn_id=turn_id,
                    payload={
                        'shell_id': params.get('itemId'),
                        'stream': params.get('stream', 'stdout'),
                        'delta': params.get('delta', ''),
                    },
                    component='shell',
                    event_id_value=params.get('itemId'),
                    occurred_at=occurred_at,
                ),
            )
            handled = True
        elif method == 'item/completed' and item.get('type') == 'commandExecution':
            add_event(
                (occurred_at, index),
                to_event(
                    index,
                    message,
                    event_synthesizer,
                    'shell.finished',
                    session_id=session_id,
                    turn_id=turn_id,
                    payload={
                        'shell_id': item.get('id'),
                        'command': item.get('command'),
                        'cwd': item.get('cwd'),
                        'exit_code': item.get('exitCode'),
                        'output': item.get('aggregatedOutput'),
                        'status': item.get('status'),
                    },
                    component='shell',
                    event_id_value=item.get('id'),
                    attributes={'duration_ms': item.get('durationMs')},
                    occurred_at=occurred_at,
                ),
            )
            handled = True
        elif method == 'item/completed' and item.get('type') == 'fileChange':
            changes = item.get('changes', [])
            primary_path = changes[0].get('path') if changes else None
            add_event(
                (occurred_at, index),
                to_event(
                    index,
                    message,
                    event_synthesizer,
                    'file.changed',
                    session_id=session_id,
                    turn_id=turn_id,
                    payload={
                        'path': primary_path,
                        'change_kind': changes[0].get('kind') if changes else None,
                        'changes': changes,
                        'status': item.get('status'),
                    },
                    component='diff',
                    event_id_value=item.get('id'),
                    attributes={'change_count': len(changes)},
                    occurred_at=occurred_at,
                ),
            )
            handled = True
        elif method == 'item/started' and item.get('type') in SUPPORTED_TOOL_ITEMS:
            add_event(
                (occurred_at, index),
                to_event(
                    index,
                    message,
                    event_synthesizer,
                    'tool.called',
                    session_id=session_id,
                    turn_id=turn_id,
                    payload={
                        'tool': item.get('tool') or item.get('query') or item.get('id'),
                        'arguments': item.get('arguments'),
                        'server': item.get('server'),
                        'item_type': item.get('type'),
                    },
                    component='tool',
                    event_id_value=item.get('id'),
                    attributes={'status': item.get('status')},
                    occurred_at=occurred_at,
                ),
            )
            handled = True
        elif method == 'item/completed' and item.get('type') in SUPPORTED_TOOL_ITEMS:
            add_event(
                (occurred_at, index),
                to_event(
                    index,
                    message,
                    event_synthesizer,
                    'tool.finished',
                    session_id=session_id,
                    turn_id=turn_id,
                    payload={
                        'tool': item.get('tool') or item.get('query') or item.get('id'),
                        'server': item.get('server'),
                        'item_type': item.get('type'),
                        'result': item.get('result'),
                        'error': item.get('error'),
                        'status': item.get('status'),
                    },
                    component='tool',
                    event_id_value=item.get('id'),
                    occurred_at=occurred_at,
                ),
            )
            handled = True
        elif method == 'item/completed' and item.get('type') == 'collabToolCall' and item.get('tool') == 'spawn_agent':
            add_event(
                (occurred_at, index),
                to_event(
                    index,
                    message,
                    event_synthesizer,
                    'subagent.spawned',
                    session_id=session_id,
                    turn_id=turn_id,
                    payload={
                        'child_agent_id': item.get('newThreadId') or item.get('receiverThreadId'),
                        'tool': item.get('tool'),
                        'sender_thread_id': item.get('senderThreadId'),
                        'status': item.get('status'),
                    },
                    component='agent',
                    event_id_value=item.get('id'),
                    occurred_at=occurred_at,
                ),
            )
            handled = True
        elif method in APPROVAL_METHODS:
            request_id = message.get('id')
            approval_kind = method.split('/')[1]
            approval_requests[request_id] = {
                'kind': approval_kind,
                'item_id': params.get('itemId'),
                'turn_id': turn_id,
            }
            add_event(
                (occurred_at, index),
                to_event(
                    index,
                    message,
                    event_synthesizer,
                    'approval.requested',
                    session_id=session_id,
                    turn_id=turn_id,
                    payload={
                        'kind': approval_kind,
                        'item_id': params.get('itemId'),
                        'reason': params.get('reason'),
                        'command': params.get('command'),
                        'cwd': params.get('cwd'),
                        'permissions': params.get('permissions'),
                    },
                    component='approval',
                    event_id_value=str(request_id),
                    occurred_at=occurred_at,
                ),
            )
            handled = True
        elif method == 'serverRequest/resolved':
            request_id = params.get('requestId')
            request = approval_requests.get(request_id, {})
            add_event(
                (occurred_at, index),
                to_event(
                    index,
                    message,
                    event_synthesizer,
                    'approval.resolved',
                    session_id=session_id,
                    turn_id=request.get('turn_id'),
                    payload={
                        'request_id': request_id,
                        'kind': request.get('kind'),
                        'item_id': request.get('item_id'),
                    },
                    component='approval',
                    event_id_value=str(request_id),
                    occurred_at=occurred_at,
                ),
            )
            handled = True
        elif method == 'error':
            error_payload = params.get('error', params)
            payload = error_payload if isinstance(error_payload, dict) else {'message': str(error_payload)}
            add_event(
                (occurred_at, index),
                to_event(
                    index,
                    message,
                    event_synthesizer,
                    'error.raised',
                    session_id=session_id,
                    turn_id=turn_id,
                    payload=payload,
                    component='runtime',
                    event_id_value=str(index),
                    occurred_at=occurred_at,
                ),
            )
            handled = True

        if handled:
            mapped_methods[metric_key] += 1
        else:
            unmapped_methods[metric_key] += 1

        session_finished_candidates[session_id] = {
            'message': message,
            'status': session_meta[session_id]['status'],
            'timestamp': session_meta[session_id]['last_timestamp'],
        }

    for session_id, candidate in session_finished_candidates.items():
        finish_event = to_event(
            999999,
            candidate['message'],
            event_synthesizer,
            'session.finished',
            session_id=session_id,
            turn_id=None,
            payload={'status': candidate['status']},
            component='session',
            event_id_value=session_id,
            occurred_at=candidate['timestamp'],
        )
        add_event((finish_event['occurred_at'], 10**9), finish_event)

    events = [event for _, event in sorted(timeline, key=lambda pair: pair[0])]
    report = {
        'message_count': len(messages),
        'event_count': len(events),
        'mapped_methods': dict(mapped_methods),
        'unmapped_methods': dict(unmapped_methods),
    }
    return events, report


def map_messages(messages: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return map_messages_with_report(messages)[0]


def main() -> int:
    parser = argparse.ArgumentParser(description='Map Codex app-server JSONL messages into TurnScope NDJSON')
    parser.add_argument('--input', required=True, help='Path to Codex app-server JSONL capture')
    parser.add_argument('--output', required=True, help='Path to write TurnScope NDJSON')
    parser.add_argument('--report', help='Optional path to write a mapping coverage report as JSON')
    args = parser.parse_args()

    messages = load_messages(Path(args.input))
    events, report = map_messages_with_report(messages)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open('w', encoding='utf-8') as handle:
        for event in events:
            handle.write(json.dumps(event, ensure_ascii=True) + '\n')

    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=True) + '\n', encoding='utf-8')
        print(f'Wrote report to {report_path}')

    print(f'Loaded {len(messages)} Codex messages')
    print(f'Wrote {len(events)} TurnScope events to {output_path}')
    if report['unmapped_methods']:
        print(f"Unmapped methods: {', '.join(sorted(report['unmapped_methods']))}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
