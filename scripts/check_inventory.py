#!/usr/bin/env python3
"""Validate source dimensions and element geometry recorded for a page."""
import argparse
import json
import math
from pathlib import Path


def inspect(path):
    from PIL import Image
    data = json.loads(path.read_text(encoding='utf-8'))
    errors, warnings, seen = [], [], set()
    with Image.open(path.parent / data['source']) as source:
        width, height = source.size
    if data.get('source_size') != [width, height]:
        errors.append('Recorded source_size differs from actual image dimensions')
    kinds = {'native_text', 'native_shape', 'svg_icon', 'svg_illustration', 'brand_asset',
             'transparent_png', 'background_raster', 'native_chart', 'native_table'}
    for element in data.get('elements', []):
        label = element.get('id', '')
        if not label or label in seen:
            errors.append('Missing or duplicate id: ' + label)
        seen.add(label)
        if element.get('kind') not in kinds:
            errors.append(label + ': unknown kind')
        box = element.get('bbox', [])
        valid = (len(box) == 4 and all(isinstance(x, (int, float)) and math.isfinite(x) for x in box)
                 and 0 <= box[0] < box[2] <= width and 0 <= box[1] < box[3] <= height)
        if not valid:
            errors.append(label + ': invalid or out-of-bounds bbox')
        if element.get('status') != 'ready':
            errors.append(label + ': element is not ready')
        if element.get('kind') == 'native_text' and not str(element.get('text', '')).strip():
            errors.append(label + ': missing text')
        asset = element.get('asset')
        if asset:
            asset_path = path.parent / asset
            if not asset_path.is_file():
                errors.append(label + ': missing asset')
            elif asset_path.suffix.lower() in {'.png', '.jpg', '.jpeg', '.webp'} and valid:
                with Image.open(asset_path) as bitmap:
                    aw, ah = bitmap.size
                if element.get('placement') == 'registered':
                    if (aw, ah) != (width, height):
                        errors.append(label + ': registered asset canvas differs from source')
                else:
                    ratio = (box[2] - box[0]) / (box[3] - box[1])
                    if abs((aw / ah) / ratio - 1) > 0.03:
                        warnings.append(label + ': aspect differs; verify transparent margins and contain placement')
        elif element.get('kind') in {'svg_icon', 'svg_illustration', 'brand_asset', 'transparent_png', 'background_raster'}:
            errors.append(label + ': image asset not recorded')
    if not seen:
        errors.append('No elements recorded')
    return {'errors': errors, 'warnings': warnings, 'element_count': len(seen), 'source_size': [width, height]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('inventory')
    parser.add_argument('--json-out')
    args = parser.parse_args()
    try:
        report = inspect(Path(args.inventory))
    except (ImportError, OSError, KeyError, ValueError, TypeError) as exc:
        report = {'errors': [str(exc)]}
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.json_out:
        Path(args.json_out).write_text(rendered + '\n', encoding='utf-8')
    return int(bool(report['errors']))


if __name__ == '__main__':
    raise SystemExit(main())
