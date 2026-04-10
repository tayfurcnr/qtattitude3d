from importlib import import_module

from .core import ASSETS_DIR, PACKAGE_ROOT, get_asset_path, get_demo_model_path

__all__ = [
    "QtAttitude3DWidget",
    "QtAttitudeDemoWindow",
    "YerIstasyonu3DWidget",
    "YerIstasyonuDemoWindow",
    "PACKAGE_ROOT",
    "ASSETS_DIR",
    "get_asset_path",
    "get_demo_model_path",
]


def __getattr__(name):
    if name in {"QtAttitude3DWidget", "YerIstasyonu3DWidget"}:
        module = import_module(".widgets", __name__)
        return getattr(module, name)

    if name in {"QtAttitudeDemoWindow", "YerIstasyonuDemoWindow"}:
        module = import_module(".demo", __name__)
        return getattr(module, name)

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
