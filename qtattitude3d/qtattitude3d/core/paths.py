from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PACKAGE_ROOT / "assets"


def get_asset_path(name):
    return ASSETS_DIR / name


def get_demo_model_path():
    return get_asset_path("example/Drone.obj")
