#!/usr/bin/env python3
"""Check source exclusion and SVG/text actually used by slide objects."""
import argparse
import hashlib
import json
import posixpath
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

P = 'http://schemas.openxmlformats.org/presentationml/2006/main'
A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
REL = 'http://schemas.openxmlformats.org/package/2006/relationships'


def inspect(pptx, sources, require_svg, require_text):
    errors, hits, used_svg, unused_svg, pages = [], [], set(), [], []
    source_hashes = {hashlib.sha256(Path(x).read_bytes()).hexdigest(): x for x in sources}
    with zipfile.ZipFile(pptx) as package:
        corrupt = package.testzip()
        if corrupt:
            errors.append('Corrupt ZIP member: ' + corrupt)
        names = set(package.namelist())
        if 'ppt/presentation.xml' not in names:
            raise ValueError('Missing ppt/presentation.xml')
        svg = {n for n in names if n.startswith('ppt/media/') and n.lower().endswith('.svg')}
        for name in sorted(n for n in names if n.startswith('ppt/media/') and not n.endswith('/')):
            digest = hashlib.sha256(package.read(name)).hexdigest()
            if digest in source_hashes:
                hits.append({'media': name, 'source': source_hashes[digest]})

        def relationships(part):
            relpath = posixpath.join(posixpath.dirname(part), '_rels', posixpath.basename(part) + '.rels')
            if relpath not in names:
                return {}
            result = {}
            for rel in ET.fromstring(package.read(relpath)).findall('{' + REL + '}Relationship'):
                if rel.get('TargetMode') == 'External':
                    continue
                target = rel.get('Target', '')
                resolved = target.lstrip('/') if target.startswith('/') else posixpath.normpath(posixpath.join(posixpath.dirname(part), target))
                result[rel.get('Id')] = resolved
            return result

        deck = ET.fromstring(package.read('ppt/presentation.xml'))
        deck_rels = relationships('ppt/presentation.xml')
        for slide_id in deck.findall('.//{' + P + '}sldId'):
            part = deck_rels.get(slide_id.get('{' + R + '}id'))
            if not part or part not in names:
                errors.append('Slide relationship is missing or unresolved')
                continue
            root = ET.fromstring(package.read(part))
            rels = relationships(part)
            referenced = set()
            for node in root.iter():
                for key, value in node.attrib.items():
                    if key.startswith('{' + R + '}') and value in rels:
                        target = rels[value]
                        if target not in names:
                            errors.append('Missing target: ' + target)
                        if target in svg:
                            referenced.add(target)
            used_svg.update(referenced)
            runs = [n.text for n in root.findall('.//{' + A + '}t') if n.text and n.text.strip()]
            pages.append({'slide': part, 'native_text_runs': len(runs), 'used_svg': sorted(referenced)})
        unused_svg = sorted(svg - used_svg)
    text_count = sum(p['native_text_runs'] for p in pages)
    if hits:
        errors.append('Original full-page image bytes are embedded')
    if len(used_svg) < require_svg:
        errors.append('Too few SVG resources actually referenced by slide objects')
    if text_count < require_text:
        errors.append('Too few nonempty native text runs')
    if not pages:
        errors.append('No slides found')
    return {'errors': errors, 'source_hash_hits': hits, 'slide_count': len(pages),
            'used_svg_count': len(used_svg), 'unused_svg': unused_svg,
            'native_text_runs': text_count, 'slides': pages,
            'note': 'Does not detect re-encoded source images or text remaining in raster backgrounds; inspect layer previews visually.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pptx')
    parser.add_argument('--source', action='append', default=[])
    parser.add_argument('--require-svg', type=int, default=0)
    parser.add_argument('--require-native-text', type=int, default=1)
    parser.add_argument('--json-out')
    args = parser.parse_args()
    try:
        report = inspect(args.pptx, args.source, args.require_svg, args.require_native_text)
    except (OSError, zipfile.BadZipFile, ET.ParseError, ValueError) as exc:
        report = {'errors': [str(exc)]}
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.json_out:
        Path(args.json_out).write_text(rendered + '\n', encoding='utf-8')
    return int(bool(report['errors']))


if __name__ == '__main__':
    raise SystemExit(main())
