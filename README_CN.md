# CIT-Bench

本项目提供 CIT-Bench 的 6 个 case：`C2IO1`、`C8IO1`、`C12IO1`、`C4M4`、`G1M4` 和 `G2M8`，并随附用于查看与调整布局的可视化工具。

## 目录

| 目录                      | 功能                                       |
| ------------------------- | ------------------------------------------ |
| `benchmark/vx.x/`         | 6 个 case 及指定显示顺序的 `manifest.json` |
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

### Benchmark 组织

每个 case 存放在 `benchmark/<版本>/<CASE>/` 目录下，包含以下三个 JSON 文件。各文件顶层的 `case_name` 标识所属 case。

#### floorplan.json

存储中介层尺寸、芯粒布局及 bump 几何信息，顶层包含 `case_name`、`width`、`height`、`instances` 和 `interposer_bumps`。

| 字段 | 存储结构与定义 |
| --- | --- |
| `width`、`height` | 中介层的宽度和高度。 |
| `instances` | 芯粒实例数组；每项包含实例名称 `chiplet_instance_name`、芯粒尺寸 `width` / `height`、期望功耗 `power`（W）、位置 `instance_x_coord` / `instance_y_coord` 及 `bumps` 数组。 |
| `instances[].bumps` | 该芯粒的 bump 数组；每项包含名称 `bump_name`、类型 `type` 和芯粒局部坐标 `rel_x` / `rel_y`。 |
| `interposer_bumps` | 中介层 bump 数组；每项包含名称 `bump_name`、类型 `type` 和全局坐标 `bump_x_coord` / `bump_y_coord`。 |

所有长度及坐标的单位均为 **μm**。全局坐标原点为中介层左下角，X 轴向右、Y 轴向上；`instance_x_coord` / `instance_y_coord` 表示芯粒左下角的全局坐标。芯粒局部坐标以该芯粒左下角为原点，轴方向与全局坐标一致，因此芯粒 bump 的全局坐标为：

```text
x = instance_x_coord + rel_x
y = instance_y_coord + rel_y
```

中介层 bump 直接使用其全局坐标。可视化面板将上述物理坐标转换为屏幕坐标，不改变 JSON 中的坐标定义。`power` 表示建模时的期望功耗，不一定等于 `power_report.json` 中按 bump 电压、电流统计的功耗。

#### netlist.json

存储网络及其连接关系，顶层包含 `case_name`、网络数量 `net_count` 和网络数组 `nets`。

| 字段 | 存储结构与定义 |
| --- | --- |
| `nets[]` | 每项包含网络名称 `net_name`、类型 `net_type`（`signal`、`power` 或 `ground`）、电压 `net_v`（V）、连接的 bump 数量 `bump_count` 和连接数组 `connections`。 |
| `connections[].chiplet_instance_name` | bump 所属芯粒的Instance名称；中介层使用保留名称 `INTERPOSER`。 |
| `connections[].chiplet_bump_name` | 对应 `floorplan.json` 中的 `bump_name`，与Instance名称共同定位一个 bump。 |
| `connections[].bump_type` | `chiplet_bump` 表示芯粒侧 bump，`interposer_bump` 表示中介层侧 bump。 |
| `connections[].bump_current` | 分配给该 bump 的电流（mA） |

网表通过名称引用 bump，不重复存储几何坐标；坐标由 `floorplan.json` 中对应的芯粒位置和 bump 坐标确定。

#### power_report.json

存储按电源域汇总的供电及功耗统计，顶层包含 `case_name`、以电源域名称为键的对象（如 `1.20V`、`VSS (0V)`），以及总计。加载外部 case 时，该文件可省略。

| 电源域内字段 | 定义 |
| --- | --- |
| `voltage_V` | 该电源域的电压（V）。 |
| `ubump_count`、`c4_count` | 芯粒侧 uBump 和中介层侧 C4 bump 的数量。 |
| `ubump_demand_mA`、`c4_capacity_mA` | 芯粒侧总电流需求和中介层侧配置的总供电电流（mA）。 |
| `ubump_max_mA_per_bump`、`c4_max_mA_per_bump` | 两侧各自的最大单 bump 配置电流（mA）。 |
| `power_W` | 该电源域的功耗（W），按 `voltage_V × ubump_demand_mA / 1000` 计算。 |

`Summary.Total_Power_W` 为各电源域 `power_W` 之和。功耗按芯粒侧供电 bump 的 `Σ[net_v (V) × bump_current (mA)] / 1000` 统计，包含核心及接口供电，中介层侧电流不重复计入。最终统计值取决于生成的供电 bump 数量及其电流配置，不一定等于 `floorplan.json` 中各芯粒期望功耗之和。

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

默认自动发现 `benchmark/v1.1/` 下的 case，通过 **Choose Case** 切换。

指定另一份 benchmark 或单个 case：

```bash
python main.py --benchmark-dir /path/to/benchmark/v1.1
python main.py --benchmark-dir benchmark/v1.1/G1M4
```

多 case 目录应直接包含各 case 子目录（例如 `benchmark/v1.1/`），程序不会递归查找更深层目录。也可通过 **Load → Open Benchmark Directory...** 或 **Open Case Directory...** 加载数据。

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

# CIT-Bench v1.1 更新内容：

- 优化C4M4的布局
- 优化Case中电源类Bump的布局
