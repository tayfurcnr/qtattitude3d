import logging
import warnings
from pathlib import Path

import numpy as np
import pyvista as pv
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QVBoxLayout, QWidget
from pyvistaqt import QtInteractor

from ..core import get_demo_model_path
from ..io import ObjMtlModelLoader

logger = logging.getLogger(__name__)

warnings.filterwarnings(
    "ignore",
    message=r"sipPyTypeDict\(\) is deprecated",
    category=DeprecationWarning,
)


class QtAttitude3DWidget(QWidget):
    modelLoaded = pyqtSignal(str)
    modelLoadFailed = pyqtSignal(str)
    CAMERA_VIEWS = ("isometric", "front", "top", "right")
    RENDER_QUALITIES = ("performance", "balanced", "quality")
    THEMES = {
        "midnight": {
            "background": ("#08111f", "#1b2b45"),
            "grid_color": "#6b7c93",
            "floor_color": "#0f172a",
            "floor_opacity": 0.16,
        },
        "dark": {
            "background": ("#0b1120", "#111827"),
            "grid_color": "#475569",
            "floor_color": "#020617",
            "floor_opacity": 0.18,
        },
        "light": {
            "background": ("#f8fafc", "#dbeafe"),
            "grid_color": "#94a3b8",
            "floor_color": "#cbd5e1",
            "floor_opacity": 0.22,
        },
        "sunset": {
            "background": ("#341216", "#7c2d12"),
            "grid_color": "#fdba74",
            "floor_color": "#431407",
            "floor_opacity": 0.20,
        },
    }

    def __init__(
        self,
        parent=None,
        background=("#08111f", "#1b2b45"),
        grid_color="#6b7c93",
        show_grid=True,
        show_axes=True,
        camera_position=None,
        initial_angles=(0.0, 0.0, 0.0),
        model_scale=1.0,
        theme=None,
        render_quality="balanced",
    ):
        super().__init__(parent)
        self.model_actors = []
        self.current_model_path = None
        self.current_angles = tuple(map(float, initial_angles))
        self.last_error = None
        self.last_scene_stats = None
        self._camera_position = camera_position or [(18, 12, 14), (0, 0, 0), (0, 0, 1)]
        self._model_scale = float(model_scale)
        self._floor_actor = None
        self._grid_color = grid_color
        self._current_theme = None
        self._render_quality = str(render_quality).lower()

        self.view = QtInteractor(parent=self)
        self.set_background(background)
        self._setup_render_quality()
        self._setup_lighting()
        self._axes_widget = self.view.add_axes() if show_axes else None
        self._grid_actor = self.view.show_grid(color=grid_color) if show_grid else None
        self._create_floor()
        if theme is not None:
            self.set_theme(theme)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.view.interactor)
        self.setLayout(layout)

    @staticmethod
    def _faces_to_pyvista(faces):
        faces = np.asarray(faces, dtype=np.int32)
        return np.hstack((np.full((len(faces), 1), 3, dtype=np.int32), faces)).ravel()

    @staticmethod
    def _apply_material_to_actor(actor, material):
        prop = actor.prop
        prop.color = tuple(float(x) for x in material.diffuse)
        prop.opacity = float(material.opacity)
        prop.ambient = min(1.0, max(0.0, float(np.mean(material.ambient)) * 1.5))
        prop.diffuse = 1.0
        prop.specular = min(1.0, max(0.0, float(np.mean(material.specular))))
        prop.specular_power = max(1.0, min(128.0, float(material.shininess)))
        prop.interpolation = "Phong"

    def _setup_render_quality(self):
        if self._render_quality not in self.RENDER_QUALITIES:
            available = ", ".join(self.RENDER_QUALITIES)
            raise ValueError(
                f"Bilinmeyen render kalitesi: {self._render_quality}. "
                f"Kullanilabilir degerler: {available}"
            )

        if self._render_quality == "performance":
            return

        try:
            anti_aliasing = "fxaa" if self._render_quality == "balanced" else "ssaa"
            self.view.enable_anti_aliasing(anti_aliasing)
        except Exception:
            pass

        if self._render_quality == "quality":
            try:
                self.view.enable_depth_peeling()
            except Exception:
                pass

    def _setup_lighting(self):
        key_light = pv.Light(
            position=(28, 18, 36),
            focal_point=(0, 0, 0),
            color="#f8fafc",
            intensity=0.95,
        )
        fill_light = pv.Light(
            position=(-24, -16, 20),
            focal_point=(0, 0, 0),
            color="#93c5fd",
            intensity=0.35,
        )
        rim_light = pv.Light(
            position=(0, 30, -10),
            focal_point=(0, 0, 0),
            color="#fca5a5",
            intensity=0.18,
        )
        self.view.add_light(key_light)
        self.view.add_light(fill_light)
        self.view.add_light(rim_light)

    def _create_floor(self):
        floor = pv.Plane(
            center=(0, 0, -10),
            direction=(0, 0, 1),
            i_size=80,
            j_size=80,
            i_resolution=1,
            j_resolution=1,
        )
        self._floor_actor = self.view.add_mesh(
            floor,
            color="#0f172a",
            opacity=0.16,
            smooth_shading=True,
            show_edges=False,
            ambient=0.55,
            diffuse=0.25,
            specular=0.05,
            name="floor_plane",
            render=False,
        )

    def _set_floor_style(self, color, opacity):
        if self._floor_actor is None:
            return
        prop = self._floor_actor.prop
        prop.color = color
        prop.opacity = float(opacity)

    @classmethod
    def available_themes(cls):
        return tuple(cls.THEMES.keys())

    @classmethod
    def available_render_qualities(cls):
        return cls.RENDER_QUALITIES

    @classmethod
    def available_camera_views(cls):
        return cls.CAMERA_VIEWS

    def clear_model(self):
        for actor in self.model_actors:
            self.view.remove_actor(actor, render=False)
        self.model_actors = []
        self.current_model_path = None
        self.last_scene_stats = None
        self.view.render()

    def load_scene(self, scene):
        self.clear_model()

        total_faces = 0
        for group in scene.groups:
            mesh = pv.PolyData(scene.vertices, self._faces_to_pyvista(group.faces))
            actor = self.view.add_mesh(
                mesh,
                color=tuple(float(x) for x in group.material.diffuse),
                opacity=float(group.material.opacity),
                smooth_shading=True,
                show_edges=False,
                name=",".join(group.material_names[:3]),
                render=False,
            )
            self._apply_material_to_actor(actor, group.material)
            self.model_actors.append(actor)
            total_faces += len(group.faces)

        if not self.model_actors:
            raise ValueError("OBJ yuklendi ama cizilecek yuz bulunamadi.")

        self.view.camera_position = self._camera_position
        self.view.reset_camera()
        self.current_model_path = Path(scene.source_path)
        self.last_scene_stats = {
            "group_count": len(scene.groups),
            "face_count": total_faces,
            "vertex_count": int(len(scene.vertices)),
            "source_path": str(scene.source_path),
            "render_quality": self._render_quality,
        }
        self.set_angles(*self.current_angles)

    def load_model(self, obj_path):
        try:
            self.last_error = None
            if obj_path is None:
                obj_path = get_demo_model_path()
            scene = ObjMtlModelLoader.load(obj_path, model_scale=self._model_scale)
            self.load_scene(scene)
            self.modelLoaded.emit(str(scene.source_path))
            return True
        except Exception as exc:
            self.last_error = f"Model yuklenemedi. Detay: {exc}"
            logger.exception("Model load failed: %s", obj_path)
            self.modelLoadFailed.emit(self.last_error)
            return False

    def set_angles(self, roll=0.0, pitch=0.0, yaw=0.0):
        self.current_angles = (float(roll), float(pitch), float(yaw))
        if not self.model_actors:
            return

        for actor in self.model_actors:
            actor.SetOrientation(roll, pitch, yaw)

        self.view.render()

    def reset_camera(self):
        self.view.reset_camera()

    def set_background(self, color):
        if isinstance(color, (tuple, list)) and len(color) == 2:
            self.view.set_background(color[0], top=color[1])
        else:
            self.view.set_background(color)

    def set_theme(self, theme_name):
        theme = self.THEMES.get(str(theme_name).lower())
        if theme is None:
            available = ", ".join(self.available_themes())
            raise ValueError(f"Bilinmeyen tema: {theme_name}. Kullanilabilir temalar: {available}")

        self._current_theme = str(theme_name).lower()
        self.set_background(theme["background"])
        self.set_grid_color(theme["grid_color"])
        self._set_floor_style(theme["floor_color"], theme["floor_opacity"])
        self.view.render()

    def set_render_quality(self, render_quality):
        quality = str(render_quality).lower()
        if quality not in self.RENDER_QUALITIES:
            available = ", ".join(self.RENDER_QUALITIES)
            raise ValueError(
                f"Bilinmeyen render kalitesi: {render_quality}. "
                f"Kullanilabilir degerler: {available}"
            )

        if quality == self._render_quality:
            return

        self._render_quality = quality
        self._setup_render_quality()
        if self.last_scene_stats is not None:
            self.last_scene_stats["render_quality"] = self._render_quality
        self.view.render()

    def set_camera_position(self, position):
        self._camera_position = position
        self.view.camera_position = position
        self.view.render()

    def zoom_camera(self, factor):
        zoom_factor = float(factor)
        if zoom_factor <= 0.0:
            raise ValueError("Zoom degeri sifirdan buyuk olmalidir.")
        self.view.camera.Zoom(zoom_factor)
        self.view.render()

    def set_camera_view(self, view_name):
        view = str(view_name).lower()
        if view not in self.CAMERA_VIEWS:
            available = ", ".join(self.CAMERA_VIEWS)
            raise ValueError(f"Bilinmeyen kamera gorunumu: {view_name}. Kullanilabilir gorunumler: {available}")

        if view == "isometric":
            self.view.view_isometric(render=False)
        elif view == "front":
            self.view.view_yz(render=False)
        elif view == "top":
            self.view.view_xy(render=False)
        elif view == "right":
            self.view.view_xz(render=False)
        self.view.render()

    def set_model_scale(self, scale):
        self._model_scale = float(scale)
        if self.current_model_path is not None:
            self.load_model(self.current_model_path)

    def set_grid_visible(self, visible):
        if visible and self._grid_actor is None:
            self._grid_actor = self.view.show_grid(color=self._grid_color)
        elif not visible and self._grid_actor is not None:
            self._grid_actor.SetVisibility(False)
        elif self._grid_actor is not None:
            self._grid_actor.SetVisibility(True)
        self.view.render()

    def set_grid_color(self, color):
        self._grid_color = color
        was_visible = self._grid_actor is not None and bool(self._grid_actor.GetVisibility())
        if self._grid_actor is not None:
            self.view.remove_actor(self._grid_actor, render=False)
        self._grid_actor = self.view.show_grid(color=color)
        self._grid_actor.SetVisibility(was_visible)
        self.view.render()

    def set_axes_visible(self, visible):
        if visible and self._axes_widget is None:
            self._axes_widget = self.view.add_axes()
        elif not visible and self._axes_widget is not None:
            self._axes_widget.setParent(None)
            self._axes_widget.deleteLater()
            self._axes_widget = None
        self.view.render()

    def set_floor_visible(self, visible):
        if self._floor_actor is not None:
            self._floor_actor.SetVisibility(bool(visible))
            self.view.render()

    def get_scene_stats(self):
        return dict(self.last_scene_stats) if self.last_scene_stats is not None else None

    def closeEvent(self, event):
        self.view.close()
        super().closeEvent(event)


# Geriye donuk uyumluluk
YerIstasyonu3DWidget = QtAttitude3DWidget
