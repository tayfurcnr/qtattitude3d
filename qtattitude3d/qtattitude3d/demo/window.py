import sys
import warnings
from pathlib import Path

warnings.simplefilter("ignore", DeprecationWarning)
warnings.filterwarnings(
    "ignore",
    message=r"sipPyTypeDict\(\) is deprecated",
    category=DeprecationWarning,
)

import pyvista as pv
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..core import get_demo_model_path, gui_session_error_message, has_gui_session
from ..widgets import QtAttitude3DWidget


class QtAttitudeDemoWindow(QWidget):
    def __init__(
        self,
        model_path=None,
        parent=None,
        window_title="qtattitude3d Demo",
        window_size=(1280, 760),
        background=("#08111f", "#1b2b45"),
        grid_color="#6b7c93",
        show_grid=True,
        show_axes=True,
        camera_position=None,
        initial_angles=(0.0, 0.0, 0.0),
        model_scale=1.25,
        theme="midnight",
        render_quality="performance",
    ):
        super().__init__(parent)
        self.setWindowTitle(window_title)
        self.resize(*window_size)
        self.model_path = Path(model_path).resolve() if model_path else get_demo_model_path()
        self.widget_config = {
            "background": background,
            "grid_color": grid_color,
            "show_grid": show_grid,
            "show_axes": show_axes,
            "camera_position": camera_position,
            "initial_angles": initial_angles,
            "model_scale": model_scale,
            "theme": theme,
            "render_quality": render_quality,
        }
        self._auto_rotate_step = 1.5
        self._auto_rotate_timer = QTimer(self)
        self._auto_rotate_timer.setInterval(60)
        self._auto_rotate_timer.timeout.connect(self._advance_auto_rotation)
        self.init_ui()
        self.model_widget.load_model(self.model_path)

    def init_ui(self):
        layout = QHBoxLayout(self)

        panel = QWidget(self)
        panel.setFixedWidth(280)
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(12, 12, 12, 12)

        title = QLabel("Attitude Controls", panel)
        panel_layout.addWidget(title)

        form = QFormLayout()
        self.spin_roll = self._create_spinbox()
        self.spin_pitch = self._create_spinbox()
        self.spin_yaw = self._create_spinbox()
        form.addRow("Roll", self.spin_roll)
        form.addRow("Pitch", self.spin_pitch)
        form.addRow("Yaw", self.spin_yaw)
        self.theme_combo = QComboBox(panel)
        self.theme_combo.addItems(QtAttitude3DWidget.available_themes())
        self.theme_combo.setCurrentText(self.widget_config["theme"] or "midnight")
        self.theme_combo.currentTextChanged.connect(self._change_theme)
        form.addRow("Tema", self.theme_combo)
        self.render_quality_combo = QComboBox(panel)
        self.render_quality_combo.addItems(QtAttitude3DWidget.available_render_qualities())
        self.render_quality_combo.setCurrentText(self.widget_config["render_quality"] or "performance")
        self.render_quality_combo.currentTextChanged.connect(self._change_render_quality)
        form.addRow("Kalite", self.render_quality_combo)
        self.camera_view_combo = QComboBox(panel)
        self.camera_view_combo.addItems(QtAttitude3DWidget.available_camera_views())
        self.camera_view_combo.setCurrentText("isometric")
        self.camera_view_combo.currentTextChanged.connect(self._change_camera_view)
        form.addRow("Kamera", self.camera_view_combo)
        panel_layout.addLayout(form)

        reset_button = QPushButton("Reset Camera", panel)
        reset_button.clicked.connect(self._reset_camera)
        panel_layout.addWidget(reset_button)

        zoom_in_button = QPushButton("Yakınlaştır", panel)
        zoom_in_button.clicked.connect(lambda: self.model_widget.zoom_camera(1.2))
        panel_layout.addWidget(zoom_in_button)

        zoom_out_button = QPushButton("Uzaklaştır", panel)
        zoom_out_button.clicked.connect(lambda: self.model_widget.zoom_camera(1 / 1.2))
        panel_layout.addWidget(zoom_out_button)

        self.auto_rotate_button = QPushButton("Otomatik Rotasyonu Başlat", panel)
        self.auto_rotate_button.setCheckable(True)
        self.auto_rotate_button.toggled.connect(self._toggle_auto_rotation)
        panel_layout.addWidget(self.auto_rotate_button)

        panel_layout.addStretch()

        self.model_widget = QtAttitude3DWidget(self, **self.widget_config)
        layout.addWidget(panel)
        layout.addWidget(self.model_widget, stretch=1)

    def _create_spinbox(self):
        spin = QDoubleSpinBox(self)
        spin.setRange(-360, 360)
        spin.setDecimals(1)
        spin.setSingleStep(5)
        spin.valueChanged.connect(self._update_rotation)
        return spin

    def _update_rotation(self):
        self.model_widget.set_angles(
            roll=self.spin_roll.value(),
            pitch=self.spin_pitch.value(),
            yaw=self.spin_yaw.value(),
        )

    def _reset_camera(self):
        self.model_widget.reset_camera()

    def _change_theme(self, theme_name):
        self.model_widget.set_theme(theme_name)

    def _change_render_quality(self, render_quality):
        self.model_widget.set_render_quality(render_quality)

    def _change_camera_view(self, view_name):
        self.model_widget.set_camera_view(view_name)

    def _toggle_auto_rotation(self, enabled):
        if enabled:
            self.auto_rotate_button.setText("Otomatik Rotasyonu Durdur")
            self._auto_rotate_timer.start()
        else:
            self.auto_rotate_button.setText("Otomatik Rotasyonu Başlat")
            self._auto_rotate_timer.stop()

    def _advance_auto_rotation(self):
        next_yaw = self.spin_yaw.value() + self._auto_rotate_step
        if next_yaw > self.spin_yaw.maximum():
            next_yaw -= 720.0
        self.spin_yaw.setValue(next_yaw)

    def set_window_size(self, width, height):
        self.resize(int(width), int(height))

    def closeEvent(self, event):
        self._auto_rotate_timer.stop()
        super().closeEvent(event)


YerIstasyonuDemoWindow = QtAttitudeDemoWindow


def main():
    if not has_gui_session():
        print(gui_session_error_message(), file=sys.stderr)
        return 1

    pv.global_theme.smooth_shading = True
    app = QApplication(sys.argv)
    window = QtAttitudeDemoWindow()
    window.show()
    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
