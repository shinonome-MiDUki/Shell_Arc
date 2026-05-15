print("run")

import sys
import os
from pathlib import Path

import bpy

from . import shellarc_blender_ui as shellarc_blender_ui
from .shellarc_blender_ui import SHELLARC_BLENDER_CustomPanel
from .shellarc_ui_action import (
    SHELLARC_modetoggle_Nop,
    SHELLARC_getfile_Nop,
    SHELLARC_forcesubmit_Nop,
    SHELLARC_reloadassetlist_Nop,
    SHELLARC_exclock_Nop,
    SHELLARC_commitfile_Nop,
    SHELLARC_submitfile_Nop,
    SHELLARC_checkoutfile_Nop,
    SHELLARC_appendasset_Nop,
    SHELLARC_reloadtmpasset_Nop,
    SHELLARC_reflog_Nop,
    SHELLARC_reflogconfirm_Nop,
    SHELLARC_login_Nop,
    SHELLARC_logout_Nop,
    SHELLARC_clearcache_Nop
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
    del scene.shellarc_prop_bool_ismodellingmode
    del scene.shellarc_prop_str_decodekey
    del scene.shellarc_prop_str_memid
    del scene.shellarc_prop_str_savepath
    del scene.shellarc_prop_enum
    del scene.shellarc_prop_enum_assets
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
    SHELLARC_appendasset_Nop,
    SHELLARC_reloadtmpasset_Nop,
    SHELLARC_reflog_Nop,
    SHELLARC_reflogconfirm_Nop,
    SHELLARC_login_Nop,
    SHELLARC_logout_Nop,
    SHELLARC_clearcache_Nop,
    SHELLARC_BLENDER_CustomPanel
    ]

@bpy.app.handlers.persistent
def blender_normal_exit_action():
    from .shellarc_blender_action import BlenderOperation, LocalOperation
    from .shellarc_core_action import BackendCommunication
    LocalOperation.delete_snapshot_dir(ctx=bpy.context)
    if bpy.context.scene["under_progress"]:
        backend_communication = BackendCommunication(ctx=bpy.context)
        backend_communication.submit_action(
            ctx=bpy.context,
            asset_name=str(Path(bpy.data.filepath).stem),
            status=["2", ""]
        )
        bpy.context.scene["under_progress"] = False
    for garbage in ["asset_list.pkl", "tmp_asset_list.pkl"]:
        cache_path = Path(__file__).resolve().parent / garbage
        if cache_path.exists(): 
            os.unlink(cache_path)

def register():
    site_package = str(Path(__file__).resolve().parent / "site_packages")
    print(site_package)
    if site_package not in sys.path:
        sys.path.append(site_package)
    import keyring
    from .shellarc_ui_action import update_asset_list
    if keyring.get_password("shellarc", "shellarc") is None:
        keyring.set_password("shellarc", "shellarc", "")
    for c in classes:
        bpy.utils.register_class(c)
    if blender_normal_exit_action not in bpy.app.handlers.exit_pre:
        bpy.app.handlers.exit_pre.append(blender_normal_exit_action)
    if blender_normal_exit_action not in bpy.app.handlers.load_pre:
        bpy.app.handlers.load_pre.append(blender_normal_exit_action)
    update_asset_list()
    shellarc_blender_ui.init_props()


def unregister():
    clear_props()
    for c in classes:
        bpy.utils.unregister_class(c)
    from .shellarc_blender_action import LocalOperation
    LocalOperation.delete_snapshot_dir(ctx=bpy.context)
    bpy.app.timers.unregister(LocalOperation.shellarc_autosave)
    blender_normal_exit_action()
