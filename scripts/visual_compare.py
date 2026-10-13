#!/usr/bin/env python3
"""Produce comparison evidence, never an automatic fidelity score."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source')
    parser.add_argument('preview')
    parser.add_argument('--out-dir', required=True)
    parser.add_argument('--inventory')
    args = parser.parse_args()
    from PIL import Image, ImageChops, ImageDraw, ImageStat
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    source = Image.open(args.source).convert('RGB')
    preview = Image.open(args.preview).convert('RGB')
    aspect_error = abs((source.width / source.height) / (preview.width / preview.height) - 1)
    if aspect_error > 0.01:
        raise SystemExit('Source and preview aspect ratios differ by more than 1%; resolve canvas treatment first.')
    resampling = getattr(Image, 'Resampling', Image)
    preview = preview.resize(source.size, resampling.LANCZOS)
    pair = Image.new('RGB', (source.width * 2, source.height))
    pair.paste(source, (0, 0))
    pair.paste(preview, (source.width, 0))
    pair.save(out / 'side_by_side.png')
    Image.blend(source, preview, 0.5).save(out / 'overlay.png')
    diff = ImageChops.difference(source, preview)
    channel = diff.convert('L').point(lambda value: min(255, value * 4))
    Image.merge('RGB', (channel, Image.new('L', source.size), Image.new('L', source.size))).save(out / 'heatmap.png')
    if args.inventory:
        inventory = json.loads(Path(args.inventory).read_text(encoding='utf-8'))
        if inventory['source_size'] != list(source.size):
            raise SystemExit('Inventory source_size does not match source image.')
        boxes = source.copy()
        draw = ImageDraw.Draw(boxes)
        for element in inventory['elements']:
            draw.rectangle(element['bbox'], outline='red', width=2)
            draw.text(element['bbox'][:2], element['id'].encode('ascii', 'replace').decode(), fill='red')
        boxes.save(out / 'source_boxes.png')
    report = {'source_size': source.size, 'mean_absolute_channel_difference': ImageStat.Stat(diff).mean,
              'note': 'Diagnostic difference only; inspect text, icons, layer registration, and source fidelity manually.'}
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
