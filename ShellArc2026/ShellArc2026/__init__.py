import sys
from pathlib import Path

import bpy

import keyring

from . import blender_ui as blender_ui
from .blender_ui import (
    SHELLARC_getfile_Nop,
    SHELLARC_exclock_Nop,
    SHELLARC_commitfile_Nop,
    SHELLARC_submitfile_Nop,
    SHELLARC_login_Nop,
    SHELLARC_logout_Nop,
    SHELLARC_BLENDER_CustomPanel,
)
from .blender_prefs import SHELLARC_AddonPreferences
from .shellarc_action import BlenderOperation

bl_info = {
    "name": "Shell Arc 2026.1",
    "author": "未定研ShellTech 2026",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "3Dビューポート > Sidebar",
    "description": "ShellArc Blender UI",
    "warning": "",
    "support": "TESTING",
    "doc_url": "",
    "tracker_url": "",
    "category": "User Interface"
}


def clear_props():
    scene = bpy.types.Scene
    del scene.shellarc_prop_enum
    del scene.shellarc_prop_str_memid


classes = [
    SHELLARC_AddonPreferences,
    SHELLARC_getfile_Nop,
    SHELLARC_exclock_Nop,
    SHELLARC_commitfile_Nop,
    SHELLARC_submitfile_Nop,
    SHELLARC_login_Nop,
    SHELLARC_logout_Nop,
    SHELLARC_BLENDER_CustomPanel
    ]


def register():
    if keyring.get_password("shellarc", "shellarc") is None:
        keyring.set_password("shellarc", "shellarc", "")
    bpy.context.scene["under_progress"] = False
    site_package = str(Path(__file__).resolve().parent / "site_packages")
    if site_package not in sys.path:
        sys.path.append(site_package)
    for c in classes:
        bpy.utils.register_class(c)
    blender_ui.init_props()


def unregister():
    clear_props()
    for c in classes:
        bpy.utils.unregister_class(c)
    BlenderOperation().delete_snapshot_dir()
