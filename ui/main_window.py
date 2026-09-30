"""Standalone benchmark visualization panel, adapted from the original UI."""
import html
from pathlib import Path
from PySide6.QtWidgets import (QMainWindow, QDockWidget, QTextEdit, QToolBar,
    QFileDialog, QComboBox, QSpinBox, QLabel)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction
from ui.canvas_view import EDACanvasView
from models.project_model import ProjectModel
from core.data_manager import DataManager, DEFAULT_BENCHMARK

class PhysicalDesignPlatform(QMainWindow):
    def __init__(self, benchmark_dir=DEFAULT_BENCHMARK):
        super().__init__()
        self.resize(1600, 1000)
        self.setWindowTitle("Chiplet Benchmark Viewer")
        self.model = ProjectModel()
        self.data_manager = DataManager(self.model)
        self.init_ui()
        self.load_benchmark(benchmark_dir)

    def _setup_menus(self):
        menu = self.menuBar().addMenu("Load")
        action = menu.addAction("Open Benchmark Directory...")
        action.triggered.connect(self.action_load_benchmark)
        action = menu.addAction("Open Case Directory...")
        action.triggered.connect(self.action_load_case)
        menu = self.menuBar().addMenu("Legality Check")
        menu.addAction("Check Chiplet Placement", self.run_all_drc)
        menu = self.menuBar().addMenu("View")
        action = QAction("Show Console", self, checkable=True)
        action.setChecked(True)
        action.triggered.connect(lambda visible: self.dock_bottom.setVisible(visible))
        menu.addAction(action)

    def load_benchmark(self, directory):
        try:
            names = self.data_manager.discover_cases(directory)
            self.combo_choose_case.blockSignals(True)
            self.combo_choose_case.clear()
            self.combo_choose_case.addItems(names)
            self.combo_choose_case.setEnabled(bool(names))
            self.combo_choose_case.blockSignals(False)
            self.on_choose_case_changed(names[0])
        except (OSError, ValueError, KeyError, TypeError) as exc:
            self.log_msg("ERROR", str(exc))

    def action_load_benchmark(self):
        directory = QFileDialog.getExistingDirectory(self, "Open Benchmark Directory", str(DEFAULT_BENCHMARK))
        if directory:
            self.load_benchmark(directory)

    def action_load_case(self):
        directory = QFileDialog.getExistingDirectory(self, "Open Case Directory", str(DEFAULT_BENCHMARK))
        if directory:
            path = Path(directory)
            if not all((path / filename).is_file() for filename in ('floorplan.json', 'netlist.json')):
                self.log_msg("ERROR", "Choose a single case directory containing floorplan.json and netlist.json. "
                             "For a directory containing multiple cases, use Open Benchmark Directory.")
                return
            self.load_benchmark(directory)

    def on_choose_case_changed(self, case_name):
        if not case_name:
            return
        try:
            self.data_manager.set_active_case(case_name)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            self.log_msg("ERROR", str(exc))
            self.combo_choose_case.blockSignals(True)
            self.combo_choose_case.setCurrentText(self.model.case_name)
            self.combo_choose_case.blockSignals(False)
            return
        self.setWindowTitle(f"Chiplet Benchmark Viewer — {case_name}")
        self.on_view_mode_changed()
        self.log_msg("SUCCESS", f"Loaded {case_name}: {len(self.model.floorplan['instances'])} chiplets, "
                     f"{len(self.model.netlist['nets'])} nets. Coordinates: μm.")
        QTimer.singleShot(0, self.canvas.fit_in_view)

    def action_save_floorplan(self):
        self.check_global_drc()
        if self.model.chip_conflicts:
            self.log_msg("ERROR", "Export aborted: resolve placement conflicts first.")
            return
        directory = QFileDialog.getExistingDirectory(self, "Choose Parent Directory for Case Export")
        if directory:
            try:
                target = self.data_manager.export_case(directory)
                self.log_msg("SUCCESS", f"Exported {self.model.case_name} to {target}")
            except (OSError, ValueError) as exc:
                self.log_msg("ERROR", str(exc))

    def run_all_drc(self):
        self.check_global_drc()
        self.trigger_canvas_update()

    def init_ui(self):
        self.canvas = EDACanvasView(self)
        self.setCentralWidget(self.canvas)
        self._setup_menus()
        self._setup_view_toolbar()
        self._setup_docks()

    def _setup_view_toolbar(self):
        toolbar = QToolBar("View Controls")
        toolbar.setMovable(False)
        self.addToolBar(Qt.TopToolBarArea, toolbar)

        toolbar.addWidget(QLabel(" Choose Case: "))
        self.combo_choose_case = QComboBox()
        self.combo_choose_case.setEnabled(False)
        self.combo_choose_case.currentTextChanged.connect(self.on_choose_case_changed)
        toolbar.addWidget(self.combo_choose_case)
        toolbar.addSeparator()

        toolbar.addWidget(QLabel(" View Mode: "))
        self.combo_view_mode = QComboBox()
        self.combo_view_mode.addItems(["Floorplan", "Local", "Connectivity", "Bump"])
        self.combo_view_mode.currentIndexChanged.connect(self.on_view_mode_changed)
        toolbar.addWidget(self.combo_view_mode)

        toolbar.addWidget(QLabel(" Option: "))
        self.combo_sub_option = QComboBox(SizeAdjustPolicy=QComboBox.AdjustToContents)
        self.combo_sub_option.currentIndexChanged.connect(self.trigger_canvas_update)
        toolbar.addWidget(self.combo_sub_option)

        self.lbl_bump = QLabel(" Bump Size: ")
        toolbar.addWidget(self.lbl_bump)
        self.spin_bump_size = QSpinBox()
        self.spin_bump_size.setRange(10, 500)
        self.spin_bump_size.setValue(100)
        self.spin_bump_size.setSingleStep(10)
        self.spin_bump_size.valueChanged.connect(self.trigger_canvas_update)
        toolbar.addWidget(self.spin_bump_size)

        toolbar.addSeparator()

        act_zoom_in = QAction("Zoom In (+)", self)
        act_zoom_in.triggered.connect(self.canvas.zoom_in)
        toolbar.addAction(act_zoom_in)

        act_zoom_out = QAction("Zoom Out (-)", self)
        act_zoom_out.triggered.connect(self.canvas.zoom_out)
        toolbar.addAction(act_zoom_out)

        toolbar.addSeparator()
        act_fit_view = QAction("Fit in View", self)
        act_fit_view.triggered.connect(self.canvas.fit_in_view)
        toolbar.addAction(act_fit_view)

        toolbar.addSeparator()
        act_save_floorplan = QAction("Export Case...", self)
        act_save_floorplan.triggered.connect(self.action_save_floorplan)
        toolbar.addAction(act_save_floorplan)

        self.on_view_mode_changed()

    def _setup_docks(self):
        self.dock_bottom = QDockWidget("Console / DRC Logs", self)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("background-color: #fafafa; color: #000000; font-family: Consolas, monospace; font-size: 13px; border: 1px solid #ccc;")
        self.dock_bottom.setWidget(self.log_text)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.dock_bottom)

    def on_view_mode_changed(self):
        mode = self.combo_view_mode.currentText()
        self.combo_sub_option.blockSignals(True)
        self.combo_sub_option.clear()
        self.combo_sub_option.setEnabled(True)
        self.lbl_bump.setVisible(False)
        self.spin_bump_size.setVisible(False)

        if mode == "Floorplan":
            self.combo_sub_option.setEnabled(False)
        elif mode == "Local":
            chips = list(self.model.chiplet_sizes.keys())
            if "INTERPOSER" in chips:
                chips.remove("INTERPOSER")
                chips.insert(0, "INTERPOSER")
            self.combo_sub_option.addItems(chips)
        elif mode == "Connectivity":
            self.combo_sub_option.addItems(["All", "D2D", "Fanout"])
        elif mode == "Bump":
            self.combo_sub_option.addItems(["All", "C4 Bump", "uBump"])
            self.lbl_bump.setVisible(True)
            self.spin_bump_size.setVisible(True)

        self.combo_sub_option.blockSignals(False)
        self.trigger_canvas_update()

    def trigger_canvas_update(self):
        mode = self.combo_view_mode.currentText()
        sub_opt = self.combo_sub_option.currentText()
        b_size = self.spin_bump_size.value()
        self.canvas.render_layout(self.model, mode, sub_opt, b_size, self)

    def check_global_drc(self):
        self.model.chip_conflicts.clear()
        errors = []
        chip_names = [name for name in self.model.chiplet_global_pos.keys() if name != "INTERPOSER"]
        iw, ih = self.model.chiplet_sizes.get("INTERPOSER", (40000, 40000))

        for i in range(len(chip_names)):
            c1 = chip_names[i]
            x1, y1 = self.model.chiplet_global_pos[c1]['x'], self.model.chiplet_global_pos[c1]['y']
            w1, h1 = self.model.chiplet_sizes.get(c1, (0,0))

            # 边界检查
            if x1 < 0 or y1 < 0 or x1 + w1 > iw or y1 + h1 > ih:
                self.model.chip_conflicts.add(c1)
                errors.append(f"Boundary Violation: Chiplet '{c1}' is outside the INTERPOSER limits.")

            # 碰撞检查
            for j in range(i+1, len(chip_names)):
                c2 = chip_names[j]
                x2, y2 = self.model.chiplet_global_pos[c2]['x'], self.model.chiplet_global_pos[c2]['y']
                w2, h2 = self.model.chiplet_sizes.get(c2, (0,0))

                if not (x1 + w1 <= x2 or x2 + w2 <= x1 or y1 + h1 <= y2 or y2 + h2 <= y1):
                    self.model.chip_conflicts.add(c1)
                    self.model.chip_conflicts.add(c2)
                    errors.append(f"Chiplet Collision: '{c1}' overlaps with '{c2}'")

        if errors:
            self.log_msg("ERROR", f"Global DRC Failed: {len(errors)} issues detected!", is_drc=True)
            for e in errors: self.log_msg("ERROR", "  -> " + e, is_drc=True)
        else:
            self.log_msg("SUCCESS", "Global DRC Passed: All chiplets are legally placed.")

    def log_msg(self, level, msg, is_drc=False):
        color_map = {"INFO": "#333333", "WARNING": "#d97706", "ERROR": "#dc2626", "SUCCESS": "#16a34a"}
        c = color_map.get(level.upper(), "#000")

        prefix = "🔴 " if level == "ERROR" else "🟢 " if level == "SUCCESS" else "👉 "

        msg = html.escape(str(msg))
        html_msg = f"<span style='color: {c};'>{prefix}<b>[{level}]</b> {msg}</span>"
        self.log_text.append(html_msg)
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())
