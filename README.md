# CIT-Bench

This project provides six CIT-Bench cases: `C2IO1`, `C8IO1`, `C12IO1`, `C4M4`, `G1M4`, and `G2M8`, together with a visualization tool for inspecting and adjusting their layouts.

## Directory Structure

| Path | Description |
| --- | --- |
| `benchmark/vx.x/` | Six cases and a `manifest.json` file specifying their display order |
| core/data_manager.py | Case loading, validation, and export |
| models/project_model.py | Current visualization state |
| scripts/plot_floorplan.py | Static floorplan plotting |
| ui/ | Window, interaction, and canvas components |
| scripts/requirements.txt | Python dependencies for the GUI and static plotting |

## Features

- **Floorplan**: Displays the interposer and chiplet layout. Drag chiplets to adjust their positions; on release, they snap to a 100 μm grid in canvas coordinates, followed by checks for chiplet overlap and interposer boundary violations. Near the boundary, keeping chiplets inside the interposer takes precedence over grid snapping.
  - Supports mouse-wheel zoom, canvas panning by dragging empty space, and automatic scaling with **Fit in View**.
- **Local**: Select a chiplet or INTERPOSER to view its actual bump distribution, with other chiplets shown as outlines.
- **Connectivity**: Displays flylines between pins on signal nets, with filters for All, D2D (die-to-die), and Fanout (chiplet-to-interposer connections).
- **Bump**: Displays all bumps, C4 Bump (interposer), or uBump (chiplets). Adjust the display diameter and hover over a bump to see its name and type.
- **Legality Check**: Checks chiplet rectangles for overlaps and interposer boundary violations. Routing and electrical rules are not checked.
- **Export Case**: After the placement passes the legality check, exports the current floorplan, netlist, and accompanying power report to a `<CASE>/` subdirectory under the selected parent directory. Exporting to the current case's source directory or an existing nonempty destination directory is rejected. The power report is copied as is, without recalculation.

### Case Statistics

| Case | Chiplets | Total Nets | D2D Nets | Fanout Nets | Power Nets | Ground Nets | uBumps | C4 Bumps | Chiplet Dimensions (mm) | Target Power per Chiplet (W) | Interposer Dimensions (mm) | Total Target Power (W) | Power-Domain Voltages (V) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C2IO1 | 3 | 723 | 148 | 568 | 5 | 2 | 6,350 | 1,949 | COMPUTE × 2: 10.12 × 6.551<br>IOD × 1: 12.4 × 9.5 | COMPUTE: 60<br>IOD: 50 | 22.8 × 19.2 | 170 | 0, 0.5, 0.9, 1.2, 1.8 |
| C8IO1 | 9 | 3,383 | 592 | 2,784 | 5 | 2 | 23,598 | 6,665 | COMPUTE × 8: 7.202 × 10.135<br>IOD × 1: 15.6 × 24.8 | COMPUTE: 35<br>IOD: 80 | 49.4 × 30.8 | 360 | 0, 0.5, 0.9, 1.2, 1.8 |
| C12IO1 | 13 | 3,775 | 888 | 2,880 | 5 | 2 | 23,708 | 6,597 | IOD × 1: 15.6 × 24.8<br>COMPUTE × 12: 6.551 × 10.12 | IOD: 80<br>COMPUTE: 24 | 61 × 30.8 | 368 | 0, 0.5, 0.9, 1, 1.2, 1.8 |
| C4 | 4 | 394 | 296 | 92 | 4 | 2 | 4,978 | 1,948 | CHIP × 4: 7 × 7 | CHIP: 50 | 23 × 23 | 200 | 0, 0.5, 0.9, 1.2, 1.8 |
| C4M4 | 8 | 3,149 | 2,792 | 352 | 3 | 2 | 21,276 | 3,487 | MEMORY × 4: 7 × 3<br>COMPUTE × 4: 14 × 10 | MEMORY: 5<br>COMPUTE: 100 | 35 × 33 | 420 | 0, 0.5, 0.9, 1.4 |
| G1M4 | 5 | 7,720 | 7,568 | 145 | 5 | 2 | 44,930 | 5,040 | MEM × 4: 5 × 12.5<br>GPU × 1: 23 × 27 | MEM: 10<br>GPU: 500 | 37 × 28 | 540 | 0, 0.9, 1.2, 1.8, 2.5 |
| G2M8 | 10 | 17,984 | 17,632 | 344 | 6 | 2 | 105,671 | 16,591 | HBM × 8: 9.44 × 12.4<br>GPU × 2: 32.26 × 25.57 | HBM: 10<br>GPU: 560 | 57.75 × 52.51 | 1,200 | 0, 0.5, 0.9, 1.2, 1.8, 2.5 |

### Benchmark Organization

Each case is stored in `benchmark/<version>/<CASE>/` and contains the following three JSON files. The top-level `case_name` field in each file identifies the case.

#### floorplan.json

Stores interposer dimensions, chiplet placement, and bump geometry. The top-level fields are `case_name`, `width`, `height`, `instances`, and `interposer_bumps`.

| Field | Structure and Definition |
| --- | --- |
| `width`, `height` | Interposer width and height. |
| `instances` | Array of chiplet instances. Each entry contains the instance name `chiplet_instance_name`, chiplet dimensions `width` / `height`, target power `power` (W), position `instance_x_coord` / `instance_y_coord`, and a `bumps` array. |
| `instances[].bumps` | Array of bumps on the chiplet. Each entry contains a name `bump_name`, a type `type`, and chiplet-local coordinates `rel_x` / `rel_y`. |
| `interposer_bumps` | Array of interposer bumps. Each entry contains a name `bump_name`, a type `type`, and global coordinates `bump_x_coord` / `bump_y_coord`. |

All lengths and coordinates are in **μm**. The global origin is at the lower-left corner of the interposer, with the X-axis pointing right and the Y-axis pointing up. `instance_x_coord` / `instance_y_coord` specify the global coordinates of the chiplet's lower-left corner. Chiplet-local coordinates use that corner as their origin and follow the same axis directions as the global coordinate system. A chiplet bump's global coordinates are therefore:

```text
x = instance_x_coord + rel_x
y = instance_y_coord + rel_y
```

Interposer bumps use global coordinates directly. The viewer converts these physical coordinates to screen coordinates without changing the coordinate definitions in the JSON files. `power` is the target power used during modeling and may differ from the power calculated from bump voltages and currents in `power_report.json`.

#### netlist.json

Stores nets and their connections. The top-level fields are `case_name`, the net count `net_count`, and the net array `nets`.

| Field | Structure and Definition |
| --- | --- |
| `nets[]` | Each entry contains a net name `net_name`, a type `net_type` (`signal`, `power`, or `ground`), voltage `net_v` (V), the number of connected bumps `bump_count`, and a `connections` array. |
| `connections[].chiplet_instance_name` | Instance name of the chiplet containing the bump. The interposer uses the reserved name `INTERPOSER`. |
| `connections[].chiplet_bump_name` | References `bump_name` in `floorplan.json`. Together with the instance name, it identifies a bump. |
| `connections[].bump_type` | `chiplet_bump` denotes a chiplet-side bump; `interposer_bump` denotes an interposer-side bump. |
| `connections[].bump_current` | Current assigned to the bump (mA). |

The netlist references bumps by name without duplicating their geometric coordinates. Coordinates are determined from the corresponding chiplet placement and bump coordinates in `floorplan.json`.

#### power_report.json

Stores supply and power statistics grouped by power domain. The top level contains `case_name`, objects keyed by power-domain names (such as `1.20V` and `VSS (0V)`), and a summary. This file is optional when loading an external case.

| Field Within a Power Domain | Definition |
| --- | --- |
| `voltage_V` | Voltage of the power domain (V). |
| `ubump_count`, `c4_count` | Number of chiplet-side uBumps and interposer-side C4 bumps, respectively. |
| `ubump_demand_mA`, `c4_capacity_mA` | Total chiplet-side current demand and total configured interposer-side supply current (mA), respectively. |
| `ubump_max_mA_per_bump`, `c4_max_mA_per_bump` | Maximum configured current per bump on each side (mA). |
| `power_W` | Power of the domain (W), calculated as `voltage_V × ubump_demand_mA / 1000`. |

`Summary.Total_Power_W` is the sum of `power_W` across all power domains. Power is calculated from chiplet-side supply bumps as `Σ[net_v (V) × bump_current (mA)] / 1000`, including both core and interface supplies. Interposer-side currents are not counted again. The resulting power depends on the number of generated supply bumps and their current configurations, and may differ from the sum of chiplet target powers in `floorplan.json`.

## Requirements and Installation

Use Python **3.10 or later** with `PySide6>=6.5,<7` and `matplotlib>=3.7,<4`. The GUI requires a working graphical desktop and Qt platform libraries. Linux desktop environments need the corresponding X11/XCB or Wayland support.
The application has been tested on Ubuntu under WSL; a working graphical display environment is required to run the GUI.

From the project root, install the dependencies:

```bash
python -m pip install -r scripts/requirements.txt
```

## Usage

Launch the viewer:

```bash
python main.py
```

By default, the viewer discovers cases under `benchmark/v1.1/`. Use **Choose Case** to switch between them.

Specify another benchmark directory or a single case:

```bash
python main.py --benchmark-dir /path/to/benchmark/v1.1
python main.py --benchmark-dir benchmark/v1.1/G1M4
```

A directory containing multiple cases must contain the case subdirectories directly, as in `benchmark/v1.1/`; the viewer does not search recursively through deeper directories. You can also load data through **Load → Open Benchmark Directory...** or **Open Case Directory...**.

```bash
python scripts/plot_floorplan.py
python scripts/plot_floorplan.py --case G1M4 --output-dir exports/floorplans
```

## Citation

If you use the CIT-Bench dataset or related tools in your research, please cite the following paper:

> X. Lin et al., “CIT-Bench1.0: Open-Source Benchmark Suite for Chiplet-based Advanced Packaging,” in _2026 27th International Conference on Electronic Packaging Technology (ICEPT)_, Xi'an, China, 2026, pp. 1–5. DOI: [10.1109/ICEPT71373.2026.11690286](https://doi.org/10.1109/ICEPT71373.2026.11690286).

BibTeX (author names are abbreviated):

```bibtex
@inproceedings{lin2026citbench,
  author    = {Lin, X. and Zhu, J. and Wang, Y. and Wang, X. and Song, Z. and Yue, Z. and Yin, L. and Wang, Y. and Han, Y.},
  title     = {{CIT-Bench1.0}: Open-Source Benchmark Suite for Chiplet-based Advanced Packaging},
  booktitle = {2026 27th International Conference on Electronic Packaging Technology (ICEPT)},
  year      = {2026},
  pages     = {1--5},
  address   = {Xi'an, China},
  doi       = {10.1109/ICEPT71373.2026.11690286},
  url       = {https://doi.org/10.1109/ICEPT71373.2026.11690286}
}
```

# CIT-Bench Updates

## v1.1
- Improved the C4M4 layout. 
  - Pending: Bump layout bug fix needed.
- Improved the placement of power bumps in the cases.
- New Case: C4
