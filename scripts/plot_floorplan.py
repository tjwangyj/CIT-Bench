"""Export benchmark floorplans as PNG files without launching the Qt panel."""
import argparse
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

ROOT = Path(__file__).resolve().parents[1]


def plot_floorplan(source, destination):
    with source.open(encoding='utf-8') as stream:
        data = json.load(stream)
    width, height = data['width'], data['height']
    fig, ax = plt.subplots(figsize=(10, 8))
    try:
        ax.add_patch(Rectangle((0, 0), width, height, linewidth=2,
                               edgecolor='black', facecolor='none'))
        for inst in data['instances']:
            x, y = inst['instance_x_coord'], inst['instance_y_coord']
            w, h = inst['width'], inst['height']
            ax.add_patch(Rectangle((x, y), w, h, edgecolor='black', facecolor='#9E9E9E'))
            ax.text(x + w / 2, y + h / 2, inst['chiplet_instance_name'],
                    ha='center', va='center', color='white', weight='bold', fontsize=9)
        ax.set(xlim=(-width * .05, width * 1.05), ylim=(-height * .05, height * 1.05),
               xlabel='x (μm)', ylabel='y (μm)', title=source.parent.name.upper(), aspect='equal')
        destination.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(destination, dpi=200, bbox_inches='tight')
    finally:
        plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--benchmark-dir', type=Path, default=ROOT / 'benchmark' / 'v1.0')
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'exports' / 'floorplans')
    parser.add_argument('--case', help='Optional uppercase case name, e.g. G1M4')
    args = parser.parse_args()
    root = args.benchmark_dir
    sources = [root / 'floorplan.json'] if (root / 'floorplan.json').is_file() else sorted(root.glob('*/floorplan.json'))
    if args.case:
        sources = [p for p in sources if p.parent.name.upper() == args.case.upper()]
    if not sources:
        parser.error('No matching floorplan.json found')
    for source in sources:
        destination = args.output_dir / f'{source.parent.name.upper()}.png'
        plot_floorplan(source, destination)
        print(destination)


if __name__ == '__main__':
    main()
