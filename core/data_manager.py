import copy
import json
import math
from pathlib import Path

DEFAULT_BENCHMARK = Path(__file__).resolve().parents[1] / 'benchmark' / 'v1.0'


def read_json(path):
    with Path(path).open(encoding='utf-8') as stream:
        return json.load(stream)


class DataManager:
    def __init__(self, model):
        self.model = model
        self.case_paths = {}

    def discover_cases(self, directory):
        root = Path(directory).resolve()
        directories = [root] if (root / 'floorplan.json').is_file() else sorted(root.iterdir())
        cases = {p.name.upper(): p for p in directories
                 if p.is_dir() and (p / 'floorplan.json').is_file()
                 and (p / 'netlist.json').is_file()}
        if not cases:
            raise ValueError(f'No cases with floorplan.json and netlist.json found in {root}')
        if len(cases) != sum(p.is_dir() and (p / 'floorplan.json').is_file()
                             and (p / 'netlist.json').is_file() for p in directories):
            raise ValueError('Case names must be unique ignoring letter case.')
        manifest_path = root / 'manifest.json'
        if directories != [root] and manifest_path.is_file():
            manifest = read_json(manifest_path)
            if not isinstance(manifest, dict) or not isinstance(manifest.get('cases'), list) or not all(
                    isinstance(name, str) for name in manifest['cases']):
                raise ValueError('manifest.json must contain a cases list of names.')
            ordered = {name.upper(): cases[name.upper()] for name in manifest['cases']
                       if name.upper() in cases}
            ordered.update(cases)
            cases = ordered
        self.case_paths = cases
        return list(cases)

    def set_active_case(self, name):
        directory = self.case_paths[name]
        floorplan = read_json(directory / 'floorplan.json')
        netlist = read_json(directory / 'netlist.json')
        power_file = directory / 'power_report.json'
        power = read_json(power_file) if power_file.exists() else None
        sizes = {'INTERPOSER': (floorplan['width'], floorplan['height'])}
        positions = {'INTERPOSER': {'x': 0, 'y': 0}}
        bumps = {}

        def add_bump(chip, bump, x_key, y_key):
            key = (chip, bump['bump_name'])
            if key in bumps:
                raise ValueError(f'Duplicate bump: {key}')
            x, y = bump[x_key], bump[y_key]
            if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in (x, y)):
                raise ValueError(f'Invalid bump coordinates: {key}')
            bumps[key] = (x, y, bump.get('type', ''))

        for inst in floorplan['instances']:
            chip = inst['chiplet_instance_name']
            if chip in sizes:
                raise ValueError(f'Duplicate or reserved chiplet name: {chip}')
            sizes[chip] = (inst['width'], inst['height'])
            positions[chip] = {'x': inst['instance_x_coord'], 'y': inst['instance_y_coord']}
            for bump in inst.get('bumps', []):
                add_bump(chip, bump, 'rel_x', 'rel_y')
        for bump in floorplan.get('interposer_bumps', []):
            add_bump('INTERPOSER', bump, 'bump_x_coord', 'bump_y_coord')
        for chip, size in sizes.items():
            if not all(isinstance(v, (int, float)) and math.isfinite(v) and v > 0 for v in size):
                raise ValueError(f'Invalid dimensions: {chip}')
            if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in positions[chip].values()):
                raise ValueError(f'Invalid placement coordinates: {chip}')
        for net in netlist['nets']:
            for conn in net['connections']:
                key = (conn['chiplet_instance_name'], conn['chiplet_bump_name'])
                if key not in bumps:
                    raise ValueError(f"Net {net['net_name']} references missing bump {key}")
        m = self.model
        m.clear_layout_data()
        m.case_name = name
        m.floorplan, m.netlist, m.power_report = floorplan, netlist, power
        m.source_directory = directory
        m.chiplet_sizes, m.chiplet_global_pos, m.bumps = sizes, positions, bumps

    def export_case(self, directory):
        if not self.model.case_name:
            raise ValueError('Load a case before exporting.')
        parent = Path(directory).resolve()
        target = (parent / self.model.case_name).resolve()
        if parent == self.model.source_directory or target == self.model.source_directory:
            raise ValueError('Choose another export directory to preserve benchmark source files.')
        if target.exists() and (not target.is_dir() or any(target.iterdir())):
            raise ValueError(f'Export destination already exists and is not empty: {target}')
        floorplan = copy.deepcopy(self.model.floorplan)
        for inst in floorplan['instances']:
            position = self.model.chiplet_global_pos[inst['chiplet_instance_name']]
            inst['instance_x_coord'] = position['x']
            inst['instance_y_coord'] = position['y']
        target.mkdir(parents=True, exist_ok=True)
        files = {'floorplan.json': floorplan, 'netlist.json': self.model.netlist}
        if self.model.power_report is not None:
            files['power_report.json'] = self.model.power_report
        for filename, data in files.items():
            with (target / filename).open('w', encoding='utf-8') as stream:
                json.dump(data, stream, ensure_ascii=False, indent=2)
                stream.write('\n')
        return target
