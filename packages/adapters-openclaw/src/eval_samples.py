#!/usr/bin/env python3
"""Evaluate OpenClaw adapter output against golden samples."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

from map_session_store import load_store, map_store


def load_ndjson(path: Path) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
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


def main() -> int:
    parser = argparse.ArgumentParser(description='Run sample-driven precision checks for the OpenClaw adapter')
    parser.add_argument('--fixtures-dir', default='packages/adapters-openclaw/fixtures', help='Directory containing session-store fixtures')
    parser.add_argument('--golden-dir', default='packages/adapters-openclaw/golden', help='Directory containing expected NDJSON files')
    args = parser.parse_args()

    failures = 0
    for fixture in sorted(Path(args.fixtures_dir).glob('*.json')):
        expected_path = Path(args.golden_dir) / f'{fixture.stem}.expected.ndjson'
        if not expected_path.exists():
            print(f'[missing] {fixture.name} has no golden file')
            failures += 1
            continue

        actual = map_store(load_store(fixture))
        expected = load_ndjson(expected_path)
        problems = compare_records(actual, expected)
        if problems:
          print(f'[fail] {fixture.name}')
          for problem in problems:
              print(f'  - {problem}')
          failures += 1
        else:
          print(f'[pass] {fixture.name} -> {len(actual)} events')

    if failures:
        print(f'Precision checks failed: {failures}')
        return 1

    print('All precision checks passed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
