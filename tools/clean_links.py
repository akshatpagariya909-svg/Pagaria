#!/usr/bin/env python3
"""Re-check the links already found, without searching again: drops any architecture-site link whose
address doesn't spell out the building's name (see slug_names_building in find_links.py).
Links that come from Wikidata (official website, map, archINFORM, Structurae...) are kept as they are."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_images import load  # noqa: E402
from find_links import read_links, write_links, slug_names_building, FROM_WIKIDATA  # noqa: E402


def main():
    _, items = load()
    by_id = {b['id']: b for b in items}
    data = read_links()
    dropped = []
    for i, entry in data.items():
        b = by_id.get(i)
        if not b:
            continue
        keep = []
        for link in entry.get('links', []):
            if link['site'] in FROM_WIKIDATA or slug_names_building(b, link['url']):
                keep.append(link)
            else:
                dropped.append(f"{b['name']} | {link['site']} | {link['url']}")
        entry['links'] = keep
    write_links(data)
    print(f'{len(dropped)} links dropped')
    print('\n'.join(dropped))


if __name__ == '__main__':
    main()
