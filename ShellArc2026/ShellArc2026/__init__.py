print("run")

import sys
from pathlib import Path

import bpy

from . import blender_ui as blender_ui
from .blender_ui import (
    SHELLARC_modetoggle_Nop,
    SHELLARC_getfile_Nop,
    SHELLARC_forcesubmit_Nop,
    SHELLARC_reloadassetlist_Nop,
    SHELLARC_exclock_Nop,
    SHELLARC_commitfile_Nop,
    SHELLARC_submitfile_Nop,
    SHELLARC_checkoutfile_Nop,
    SHELLARC_reflog_Nop,
    SHELLARC_reflogconfirm_Nop,
    SHELLARC_login_Nop,
    SHELLARC_logout_Nop,
    SHELLARC_clearcache_Nop,
    SHELLARC_BLENDER_CustomPanel,
)
from .blender_prefs import SHELLARC_AddonPreferences

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
    del scene.shellarc_prop_str_decodekey
    del scene.shellarc_prop_str_savepath
    del scene.shellarc_prop_str_memid
    del scene.shellarc_prop_str_exlocksta
    del scene.shellarc_prop_str_freezedirsize
    del scene.shellarc_prop_int_reflogidx


classes = [
    SHELLARC_modetoggle_Nop,
    SHELLARC_AddonPreferences,
    SHELLARC_getfile_Nop,
    SHELLARC_forcesubmit_Nop,
    SHELLARC_reloadassetlist_Nop,
    SHELLARC_exclock_Nop,
    SHELLARC_commitfile_Nop,
    SHELLARC_submitfile_Nop,
    SHELLARC_checkoutfile_Nop,
    SHELLARC_reflog_Nop,
    SHELLARC_reflogconfirm_Nop,
    SHELLARC_login_Nop,
    SHELLARC_logout_Nop,
    SHELLARC_clearcache_Nop,
    SHELLARC_BLENDER_CustomPanel
    ]

@bpy.app.handlers.persistent
def blender_normal_exit_action():
    from .shellarc_action import BlenderOperation, BackendCommunication
    BlenderOperation.delete_snapshot_dir()
    if bpy.context.scene["under_progress"]:
        BackendCommunication().submit_action(
            asset_name=str(Path(bpy.data.filepath).stem),
            status=["2", ""]
        )
        bpy.context.scene["under_progress"] = False

def register():
    site_package = str(Path(__file__).resolve().parent / "site_packages")
    print(site_package)
    if site_package not in sys.path:
        sys.path.append(site_package)
    import keyring
    from .blender_ui import update_asset_list
    if keyring.get_password("shellarc", "shellarc") is None:
        keyring.set_password("shellarc", "shellarc", "")
    for c in classes:
        bpy.utils.register_class(c)
    if blender_normal_exit_action not in bpy.app.handlers.exit_pre:
        bpy.app.handlers.exit_pre.append(blender_normal_exit_action)
    if blender_normal_exit_action not in bpy.app.handlers.load_pre:
        bpy.app.handlers.load_pre.append(blender_normal_exit_action)
    blender_ui.init_props()


def unregister():
    clear_props()
    for c in classes:
        bpy.utils.unregister_class(c)
    from .shellarc_action import BlenderOperation
    BlenderOperation.delete_snapshot_dir()
    bpy.app.timers.unregister(BlenderOperation.shellarc_autosave)
    blender_normal_exit_action()
