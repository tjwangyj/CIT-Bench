# ui/canvas_view.py
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsItem, QGraphicsLineItem, QGraphicsEllipseItem
from PySide6.QtCore import Qt, QPointF, QTimer
from PySide6.QtGui import QColor, QPen, QBrush, QPainter, QFont


THEME = {
    "bg": QColor(245, 245, 245),              # 画布背景: 亮灰
    "interposer_bg": QColor(225, 225, 225),   # 基板背景: 浅灰
    "interposer_border": QColor(0, 0, 0),     # 基板边框: 纯黑
    "chiplet_bg": QColor(200, 200, 200),      # 芯粒: 灰色
    "chiplet_outline_only": QColor(245, 245, 245, 0),
    "chiplet_border": QColor(0, 0, 0),        # 芯粒边框: 纯黑
    "chiplet_border_dim": QColor(150, 150, 150),
    "text_dark": QColor(0, 0, 0),             # 文字: 黑色
    "text_dim": QColor(130, 130, 130),
    "conn_line": QColor(255, 0, 255, 200),    # 飞线: 亮洋红
    "bump_color": QColor(0, 0, 0)             # 引脚: 纯黑
}

class DraggableChiplet(QGraphicsRectItem):
    def __init__(self, name, x, y, w, h, ih, model, main_window, is_movable, is_outline_only, is_conflict=False):
        super().__init__(0, 0, w, h)
        self.setPos(x, y)
        self.name = name
        self.ih = ih
        self.model = model
        self.main_window = main_window
        self.is_outline_only = is_outline_only

        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, is_movable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)

        border_width = 30 if name != "INTERPOSER" else 80
        if is_conflict:
            self.bg_color = QColor(255, 150, 150, 200)
            self.pen = QPen(QColor(255, 0, 0), border_width * 2, Qt.SolidLine)
        elif is_outline_only:
            self.bg_color = THEME["chiplet_outline_only"]
            self.pen = QPen(THEME["chiplet_border_dim"], 20, Qt.DashLine)
        else:
            self.bg_color = THEME["chiplet_bg"]
            self.pen = QPen(THEME["chiplet_border"], border_width, Qt.SolidLine)

        self.text_color = THEME["text_dim"] if is_outline_only else THEME["text_dark"]

    def paint(self, painter, option, widget):
        painter.setBrush(QBrush(self.bg_color))
        painter.setPen(self.pen)
        painter.drawRect(self.rect())

        if self.name != "INTERPOSER":
            painter.setPen(self.text_color)
            font = QFont("Arial", weight=QFont.Bold)
            pixel_size = max(200, int(min(self.rect().width(), self.rect().height()) / 12))
            font.setPixelSize(pixel_size)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignCenter | Qt.TextWordWrap, self.name)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and self.name != "INTERPOSER":
            iw, ih = self.model.chiplet_sizes.get("INTERPOSER", (40000, 40000))
            cw, ch = self.rect().width(), self.rect().height()

            clamped_x = max(0, min(value.x(), iw - cw))
            clamped_y = max(0, min(value.y(), ih - ch))
            return QPointF(clamped_x, clamped_y)
        return super().itemChange(change, value)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if self.flags() & QGraphicsItem.ItemIsMovable and self.name != "INTERPOSER":
            pos = self.scenePos()
            snapped_x = round(pos.x() / 100.0) * 100
            snapped_y = round(pos.y() / 100.0) * 100
            self.setPos(snapped_x, snapped_y)

            snapped_x, snapped_y = self.pos().x(), self.pos().y()
            phys_y = self.ih - snapped_y - self.rect().height()
            self.model.chiplet_global_pos[self.name]['x'] = snapped_x
            self.model.chiplet_global_pos[self.name]['y'] = phys_y

            self.main_window.check_global_drc()
            QTimer.singleShot(0, self.main_window.trigger_canvas_update)

class EDACanvasView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene_obj = QGraphicsScene()
        self.setScene(self.scene_obj)

        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.TextAntialiasing)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setOptimizationFlag(QGraphicsView.DontSavePainterState)
        self.setViewportUpdateMode(QGraphicsView.SmartViewportUpdate)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setBackgroundBrush(QBrush(THEME["bg"]))

    def render_layout(self, model, view_mode, sub_option, bump_size, main_window):
        self.scene_obj.clear()
        self.scene_obj.link_map = {}
        if not model.chiplet_sizes: return

        iw, ih = model.chiplet_sizes.get("INTERPOSER", (40000, 40000))
        self.scene_obj.setSceneRect(-2000, -2000, iw + 4000, ih + 4000)

        # ==================================
        # 1. 绘制 Interposer (最底层)
        # ==================================
        show_interposer_fill = True
        if view_mode == "Local" and sub_option != "INTERPOSER":
            show_interposer_fill = False

        interposer_item = DraggableChiplet("INTERPOSER", 0, 0, iw, ih, ih, model, main_window,
                                           is_movable=False, is_outline_only=(not show_interposer_fill),
                                           is_conflict=("INTERPOSER" in model.chip_conflicts))
        interposer_item.setZValue(-10)
        self.scene_obj.addItem(interposer_item)

        # ==================================
        # 2. 绘制 Chiplets
        # ==================================
        for chip_name, pos in model.chiplet_global_pos.items():
            if chip_name == "INTERPOSER": continue

            w, h = model.chiplet_sizes.get(chip_name, (5000, 5000))

            # 【核心转换】Physical Y -> Scene Y
            phys_x, phys_y = pos['x'], pos['y']
            scene_x = phys_x
            scene_y = ih - phys_y - h

            is_movable = False
            is_outline_only = False

            if view_mode == "Floorplan":
                is_movable = True
            elif view_mode == "Local":
                if sub_option != chip_name:
                    is_outline_only = True
            elif view_mode in ["Connectivity", "Bump"]:
                is_outline_only = False

            is_conflict = chip_name in model.chip_conflicts

            chip_item = DraggableChiplet(chip_name, scene_x, scene_y, w, h, ih, model, main_window, is_movable, is_outline_only, is_conflict)
            chip_item.setZValue(0)
            self.scene_obj.addItem(chip_item)

        # Benchmark pins are physical coordinates, not regenerated protocol blocks.
        if view_mode in ("Bump", "Local"):
            for (chip, name), (x, y, kind) in model.bumps.items():
                if view_mode == "Local" and chip != sub_option:
                    continue
                if view_mode == "Bump":
                    if sub_option == "C4 Bump" and chip != "INTERPOSER":
                        continue
                    if sub_option == "uBump" and chip == "INTERPOSER":
                        continue
                pos = model.chiplet_global_pos[chip]
                item = QGraphicsEllipseItem(pos['x'] + x - bump_size / 2,
                    ih - pos['y'] - y - bump_size / 2, bump_size, bump_size)
                item.setBrush(QBrush(THEME["bump_color"]))
                item.setPen(QPen(Qt.NoPen))
                item.setToolTip(f"{chip}/{name} ({kind})")
                item.setZValue(10)
                self.scene_obj.addItem(item)

        if view_mode == "Connectivity":
            pen = QPen(THEME["conn_line"], max(5, iw / 2000))
            for net in model.netlist['nets']:
                # Supply nets have thousands of pins; signal flylines are shown here.
                if net.get('net_type', '').lower() != 'signal':
                    continue
                connections = net['connections']
                fanout = any(c['chiplet_instance_name'] == 'INTERPOSER' for c in connections)
                if sub_option == 'D2D' and fanout:
                    continue
                if sub_option == 'Fanout' and not fanout:
                    continue
                points = []
                for connection in connections:
                    chip = connection['chiplet_instance_name']
                    x, y, _ = model.bumps[(chip, connection['chiplet_bump_name'])]
                    pos = model.chiplet_global_pos[chip]
                    points.append((pos['x'] + x, ih - pos['y'] - y))
                for point in points[1:]:
                    item = QGraphicsLineItem(*points[0], *point)
                    item.setPen(pen)
                    item.setToolTip(net['net_name'])
                    item.setZValue(10)
                    self.scene_obj.addItem(item)

    def wheelEvent(self, event):
        zoom_factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(zoom_factor, zoom_factor)

    def zoom_in(self): self.scale(1.2, 1.2)
    def zoom_out(self): self.scale(1 / 1.2, 1 / 1.2)
    def fit_in_view(self):
        rect = self.scene_obj.itemsBoundingRect()
        if not rect.isEmpty():
            self.fitInView(rect, Qt.KeepAspectRatio)
