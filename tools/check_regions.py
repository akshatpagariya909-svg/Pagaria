#!/usr/bin/env python3
"""Check that every building's region matches its country (one region per country).

  python tools/check_regions.py         list the buildings whose region doesn't match
  python tools/check_regions.py --fix   set them from REGIONS in tools/merge_1000.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_images import load, save  # noqa: E402
from merge_1000 import region  # noqa: E402


def main():
    head, items = load()
    wrong = [(b, region(b['place'].rsplit(', ', 1)[-1])) for b in items]
    wrong = [(b, r) for b, r in wrong if b['region'] != r]
    for b, r in wrong:
        print(f"{b['id']} ({b['place']}): {b['region']} -> {r}")
        b['region'] = r
    if '--fix' in sys.argv and wrong:
        save(head, items)
    print(f'{len(wrong)} buildings in the wrong region' + (', fixed' if '--fix' in sys.argv else ''))
    return 1 if wrong and '--fix' not in sys.argv else 0


if __name__ == '__main__':
    sys.exit(main())
