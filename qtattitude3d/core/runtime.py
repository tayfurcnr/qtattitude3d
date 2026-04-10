import os
import subprocess
import sys


def has_gui_session():
    if sys.platform.startswith("linux"):
        wayland_display = os.environ.get("WAYLAND_DISPLAY")
        if wayland_display:
            return True

        display = os.environ.get("DISPLAY")
        if not display:
            return False

        # DISPLAY ayarli olsa bile X sunucusuna baglanti kopuk olabilir.
        try:
            result = subprocess.run(
                ["xset", "q"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            return result.returncode == 0
        except FileNotFoundError:
            display_num = display.split(":")[-1].split(".")[0]
            return os.path.exists(f"/tmp/.X11-unix/X{display_num}")
    return True


def gui_session_error_message():
    return (
        "GUI oturumu bulunamadi. Bu demo bir masaustu oturumunda "
        "(X11/Wayland) calistirilmalidir."
    )
