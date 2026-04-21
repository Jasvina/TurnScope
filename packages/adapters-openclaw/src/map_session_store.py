#!/usr/bin/env python3
"""Map an OpenClaw session store snapshot into TurnScope events."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


def load_store(path: Path) -> Dict[str, Dict[str, Any]]:
    payload = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(payload, dict):
        raise ValueError('session store snapshot must be a JSON object map')
    return payload


def build_attributes(entry: Dict[str, Any]) -> Dict[str, Any]:
    return {
        'input_tokens': entry.get('inputTokens'),
        'output_tokens': entry.get('outputTokens'),
        'total_tokens': entry.get('totalTokens'),
        'context_tokens': entry.get('contextTokens'),
        'display_name': entry.get('displayName'),
        'channel': entry.get('channel'),
    }


def map_store(store: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []

    for session_key in sorted(store):
        entry = store[session_key]
        session_id = entry['sessionId']
        started_at = entry.get('createdAt') or entry.get('updatedAt')
        updated_at = entry.get('updatedAt') or started_at
        origin = entry.get('origin', {})
        attributes = build_attributes(entry)

        events.append(
            {
                'version': '0.1.0',
                'id': f'session_started_{session_id}',
                'type': 'session.started',
                'occurred_at': started_at,
                'session_id': session_id,
                'turn_id': None,
                'agent_id': 'openclaw',
                'parent_id': None,
                'source': {
                    'runtime': 'openclaw',
                    'component': 'session-store',
                    'origin': 'adapter-openclaw-session-store',
                },
                'payload': {
                    'status': 'snapshot',
                    'session_key': session_key,
                    'origin': origin,
                    'label': origin.get('label') or entry.get('displayName'),
                    'provider': origin.get('provider') or entry.get('channel'),
                },
                'attributes': attributes,
            }
        )
        events.append(
            {
                'version': '0.1.0',
                'id': f'session_finished_{session_id}',
                'type': 'session.finished',
                'occurred_at': updated_at,
                'session_id': session_id,
                'turn_id': None,
                'agent_id': 'openclaw',
                'parent_id': None,
                'source': {
                    'runtime': 'openclaw',
                    'component': 'session-store',
                    'origin': 'adapter-openclaw-session-store',
                },
                'payload': {
                    'status': 'active_snapshot',
                    'session_key': session_key,
                    'origin': origin,
                },
                'attributes': attributes,
            }
        )

    type_order = {'session.started': 0, 'session.finished': 1}
    events.sort(key=lambda event: (event['occurred_at'], type_order.get(event['type'], 99), event['id']))
    return events


def main() -> int:
    parser = argparse.ArgumentParser(description='Map an OpenClaw session store snapshot into TurnScope NDJSON')
    parser.add_argument('--input', required=True, help='Path to sessions.json-style snapshot')
    parser.add_argument('--output', required=True, help='Path to write TurnScope NDJSON')
    args = parser.parse_args()

    store = load_store(Path(args.input))
    events = map_store(store)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open('w', encoding='utf-8') as handle:
        for event in events:
            handle.write(json.dumps(event, ensure_ascii=True) + '\n')

    print(f'Loaded {len(store)} session entries')
    print(f'Wrote {len(events)} TurnScope events to {output_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
