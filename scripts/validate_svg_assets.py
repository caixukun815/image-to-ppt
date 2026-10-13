#!/usr/bin/env python3
"""Inspect self-contained SVG icons; semantic transparency needs visual review."""
import argparse
import json
import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path


def inspect(path):
    errors = []
    try:
        root = ET.parse(path).getroot()
        if root.tag != '{http://www.w3.org/2000/svg}svg':
            errors.append('Expected an SVG root with the SVG namespace')
        box = [float(x) for x in re.split(r'[\s,]+', root.get('viewBox', '').strip()) if x]
        if len(box) != 4 or not all(math.isfinite(x) for x in box) or box[2] <= 0 or box[3] <= 0:
            errors.append('viewBox must have four finite numbers and positive dimensions')
        for element in root.iter():
            name = element.tag.split('}')[-1]
            if name in {'text', 'tspan', 'textPath', 'image', 'script', 'foreignObject', 'animate', 'animateTransform', 'set'}:
                errors.append('Disallowed element: ' + name)
            for key, value in element.attrib.items():
                name_key = key.split('}')[-1]
                if name_key.lower().startswith('on'):
                    errors.append('Event handler attributes are not allowed')
                if name_key == 'href' and not value.strip().startswith('#'):
                    errors.append('Only local fragment references are allowed')
                for target in re.findall(r'url\((.*?)\)', value, flags=re.I):
                    if not target.strip(' \t\"\x27').startswith('#'):
                        errors.append('External URL in SVG attribute')
            style = element.get('style', '')
            if element is root and re.search(r'(^|;)\s*background(?:-color)?\s*:', style, re.I):
                errors.append('Canvas background styling is not allowed')
            if name == 'style':
                errors.append('Use explicit presentation attributes instead of stylesheet elements')
        return {'path': str(path), 'errors': sorted(set(errors)), 'viewBox': root.get('viewBox')}
    except (OSError, ET.ParseError, ValueError) as exc:
        return {'path': str(path), 'errors': [str(exc)]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('paths', nargs='+')
    parser.add_argument('--json-out')
    args = parser.parse_args()
    files, missing = set(), []
    for item in args.paths:
        path = Path(item)
        if path.is_dir():
            files.update(path.rglob('*.svg'))
        elif path.is_file() and path.suffix.lower() == '.svg':
            files.add(path)
        else:
            missing.append(item)
    results = [inspect(path) for path in sorted(files)]
    report = {'files': results, 'invalid_paths': missing,
              'error_count': sum(len(x['errors']) for x in results) + len(missing),
              'note': 'Geometry, icon fidelity, and the absence of unwanted background shapes require visual inspection.'}
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.json_out:
        Path(args.json_out).write_text(rendered + '\n', encoding='utf-8')
    return int(bool(report['error_count']) or not results)


if __name__ == '__main__':
    raise SystemExit(main())
