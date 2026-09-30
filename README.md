# CIT-Bench v1.0

本项目提供 CIT-Bench v1.0 的 6 个 case：`C2IO1`、`C8IO1`、`C12IO1`、`C4M4`、`G1M4` 和 `G2M8`，并随附用于查看与调整布局的可视化工具。

## 目录

| 目录                      | 功能                                       |
| ------------------------- | ------------------------------------------ |
| `benchmark/v1.0/`         | 6 个 case 及指定显示顺序的 `manifest.json` |
| core/data_manager.py      | case 加载、校验和导出                      |
| models/project_model.py   | 当前可视化状态                             |
| scripts/plot_floorplan.py | 静态 case 布局绘图                         |
| ui/                       | 窗口、交互与画布                           |
| scripts/requirements.txt  | GUI 和静态绘图的 Python 依赖               |

## 功能

- **Floorplan**：显示中介层和芯粒布局；拖动芯粒可调整位置，释放时按画布坐标中的 100 μm 网格吸附，并检查芯粒重叠及中介层边界；贴近边界时优先限制在中介层内。
  - 支持滚轮缩放、空白处拖动画布、Fit in View 自适应缩放。
- **Local**：选择某个芯粒或 INTERPOSER，查看其实际 bump 分布，其他芯粒以轮廓显示。
- **Connectivity**：显示网表中 signal 类型网络的引脚间飞线，可筛选 All、D2D（Die to Die）或 Fanout（芯粒到中介层的扇出）。
- **Bump**：查看全部、C4 Bump（中介层）或 uBump（芯粒）引脚；可调整显示直径，悬停查看引脚名称和类型。
- **Legality Check**：检查芯粒矩形的重叠和中介层边界。此检查不包含布线或电气规则。
- **Export Case**：布局检查通过后，将当前布局、网表及随附功耗报告导出到所选父目录下的 `<CASE>/` 子目录；拒绝覆盖当前 case 源目录或已有非空目标目录。功耗报告按原样复制，不重新计算。

### Benchmark组织

每个 case 包含：

- `floorplan.json`：`width`、`height` 为中介层尺寸；`instances` 中包含芯粒尺寸、期望功耗（`power`，单位 W）、位置和局部 bump 坐标；`interposer_bumps` 为中介层 bump 的全局坐标。
- `netlist.json`：`net_count` 与 `nets`；每个网络通过 `chiplet_instance_name` 和 `chiplet_bump_name` 引用具体引脚。
- `power_report.json`：按电源域组织的电压、电流、bump 数量及功耗统计。加载外部 case 时该文件可省略。

长度及坐标单位为 **μm**。物理坐标原点位于左下，Y 轴向上；面板会转换为屏幕坐标。芯粒 bump 的全局坐标为芯粒位置加 `rel_x` / `rel_y`，中介层 bump 使用 `bump_x_coord` / `bump_y_coord`。

### 功耗统计

`floorplan.json` 中各芯粒的 `power` 是建模时的期望功耗。`power_report.json` 则根据最终网表中各芯粒侧供电 bump 的电压和分配电流计算功耗：`P (W) = Σ[net_v (V) × bump_current (mA)] / 1000`，包含核心及接口供电；中介层侧的供电电流不重复计入。

最终统计值取决于生成的供电 bump 数量及其电流配置，不一定等于期望功耗之和。

## 环境与安装

使用 Python **3.10 或更高版本**，依赖 `PySide6>=6.5,<7` 和 `matplotlib>=3.7,<4`。GUI 需要可用的图形桌面及 Qt 平台运行库；Linux 桌面环境需具备对应的 X11/XCB 或 Wayland 支持。
已在 WSL Ubuntu 上测试；运行 GUI 需要配置可用的图形显示环境。

进入项目根目录后安装依赖：

```bash
python -m pip install -r scripts/requirements.txt
```

## 使用

启动面板：

```bash
python main.py
```

默认自动发现 `benchmark/v1.0/` 下的 case，通过 **Choose Case** 切换。

指定另一份 benchmark 或单个 case：

```bash
python main.py --benchmark-dir /path/to/benchmark/v1.0
python main.py --benchmark-dir benchmark/v1.0/G1M4
```

多 case 目录应直接包含各 case 子目录（例如 `benchmark/v1.0/`），程序不会递归查找更深层目录。也可通过 **Load → Open Benchmark Directory...** 或 **Open Case Directory...** 加载数据。

静态布局绘图无需启动 GUI，默认将全部 case 输出为 `exports/floorplans/<CASE>.png`：

```bash
python scripts/plot_floorplan.py
python scripts/plot_floorplan.py --case G1M4 --output-dir exports/floorplans
```

## 引用本工作

如果您在研究中使用了 CIT-Bench 数据集或相关工具，请引用以下论文：

> X. Lin et al., “CIT-Bench1.0: Open-Source Benchmark Suite for Chiplet-based Advanced Packaging,” in _2026 27th International Conference on Electronic Packaging Technology (ICEPT)_, Xi'an, China, 2026, pp. 1–5. DOI: [10.1109/ICEPT71373.2026.11690286](https://doi.org/10.1109/ICEPT71373.2026.11690286).

BibTeX（作者姓名使用缩写）：

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
