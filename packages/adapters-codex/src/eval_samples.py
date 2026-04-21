#!/usr/bin/env python3
"""Evaluate Codex adapter output against golden samples."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Set

from map_app_server import load_messages, map_messages_with_report


def load_ndjson(path: Path) -> List[Dict[str, Any]]:
    records = []
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    return records


def compare_records(actual: List[Dict[str, Any]], expected: List[Dict[str, Any]]) -> List[str]:
    problems: List[str] = []
    if len(actual) != len(expected):
        problems.append(f'event count mismatch: actual={len(actual)} expected={len(expected)}')
    for index, (a, e) in enumerate(zip(actual, expected), start=1):
        if a != e:
            problems.append(f'mismatch at event {index}: actual={json.dumps(a, ensure_ascii=True)} expected={json.dumps(e, ensure_ascii=True)}')
            break
    return problems


def load_allowed_gaps(path: Path) -> Set[str]:
    if not path.exists():
        return set()
    payload = json.loads(path.read_text(encoding='utf-8'))
    return set(payload.get('allowed_unmapped_methods', []))


def main() -> int:
    parser = argparse.ArgumentParser(description='Run sample-driven precision checks for the Codex adapter')
    parser.add_argument('--fixtures-dir', default='packages/adapters-codex/fixtures', help='Directory containing raw fixture JSONL files')
    parser.add_argument('--golden-dir', default='packages/adapters-codex/golden', help='Directory containing expected NDJSON files')
    parser.add_argument('--allowed-gaps', default='packages/adapters-codex/expected_gaps.json', help='JSON file listing expected unmapped method keys')
    args = parser.parse_args()

    fixtures_dir = Path(args.fixtures_dir)
    golden_dir = Path(args.golden_dir)
    allowed_gaps = load_allowed_gaps(Path(args.allowed_gaps))
    failures = 0

    for fixture in sorted(fixtures_dir.glob('*.jsonl')):
        expected_path = golden_dir / f'{fixture.stem}.expected.ndjson'
        if not expected_path.exists():
            print(f'[missing] {fixture.name} has no golden file')
            failures += 1
            continue

        messages = load_messages(fixture)
        actual, report = map_messages_with_report(messages)
        expected = load_ndjson(expected_path)
        problems = compare_records(actual, expected)
        unexpected_unmapped = sorted(set(report['unmapped_methods']) - allowed_gaps)
        if problems or unexpected_unmapped:
            print(f'[fail] {fixture.name}')
            for problem in problems:
                print(f'  - {problem}')
            if unexpected_unmapped:
                print(f'  - unexpected unmapped methods: {json.dumps(unexpected_unmapped, ensure_ascii=True)}')
            failures += 1
        else:
            print(f'[pass] {fixture.name} -> {len(actual)} events')
        if report['unmapped_methods']:
            print(f"  unmapped methods: {json.dumps(report['unmapped_methods'], ensure_ascii=True)}")

    if failures:
        print(f'Precision checks failed: {failures}')
        return 1

    print('All precision checks passed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
