import os
import sys
import pickle
from pathlib import Path

import bpy
from bpy.types import Operator
from bpy.props import StringProperty

from .shellarc_blender_action import LocalOperation
from .shellarc_core_action import BackendCommunication

def update_asset_list(backend_communication: BackendCommunication | None=None,
                      force_load_asset_list: bool=False
                      ) -> None:
    asset_list = []
    submission_type = "assets" if force_load_asset_list else ""
    if backend_communication is None:
        backend_communication = BackendCommunication(
            ctx=bpy.context,
            submission_type=submission_type
            )
    pref = bpy.context.preferences
    addon_pref = pref.addons[__package__].preferences
    accessible_asset_set = backend_communication.get_member_data(mem_id=addon_pref.member_id)
    print(type(accessible_asset_set))
    asset_dict = backend_communication.get_asset_metadata()
    if accessible_asset_set != ["NIL"]:
        for asset in asset_dict:
            if accessible_asset_set == ["ALL"]:
                asset_list.append((asset, asset, asset))
                continue
            if asset not in accessible_asset_set:
                continue
            asset_list.append((asset, asset, asset))
    pkl_file_name = "tmp_asset_list.pkl" if force_load_asset_list else "asset_list.pkl"
    cache_path = Path(__file__).resolve().parent / pkl_file_name
    with open(cache_path, "wb") as f:
        pickle.dump(asset_list, f)


class SHELLARC_modetoggle_Nop(Operator):

    bl_idname = "object.shellarc_modetoggle_nop"
    bl_label = "NOP"
    bl_description = "モードをスイッチ"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        context.scene.shellarc_prop_bool_ismodellingmode = not context.scene.shellarc_prop_bool_ismodellingmode
        return {'FINISHED'}
    

class SHELLARC_getfile_Nop(Operator):

    bl_idname = "object.shellarc_getfile_nop"
    bl_label = "NOP"
    bl_description = "ファイルをサーバからロードする"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        asset_name = context.scene.shellarc_prop_enum
        saving_dir = context.scene.shellarc_prop_str_savepath
        update_asset_list(force_load_asset_list=True)
        if LocalOperation.is_snapshot_exists(ctx=context,
                                             asset_name=asset_name
                                             ):
            LocalOperation.open_snapshot(ctx=context)
            bpy.ops.wm.save_as_mainfile(filepath=f"{saving_dir}/{asset_name}.blend")
            self.report({'INFO'}, f"recovered crashed blend file")
        else:
            backend_communication = BackendCommunication(ctx=context)
            addon_pref = bpy.context.preferences.addons[__package__].preferences
            mem_id = str(addon_pref.member_id)
            getfile_status = backend_communication.request_asset(
                ctx=context,
                mem_id=mem_id,
                asset_name=asset_name,
                saving_dir=saving_dir
            )
            backend_communication.set_asset_metadata(
                asset_name=asset_name,
                status=["3", mem_id]
            )
            if getfile_status != asset_name:
                self.report({'INFO'}, f"loaded blend file failed : {getfile_status}")
                return {'CANCELLED'}
            self.report({'INFO'}, f"loaded blend file")
        context.scene.shellarc_prop_int_reflogidx = 0
        cache_path = Path(__file__).resolve().parent / "cache_reflogidx.pkl"
        if cache_path.exists():
            os.unlink(cache_path)
        bpy.context.scene["under_progress"] = True
        bpy.app.timers.register(LocalOperation.shellarc_autosave)
        return {'FINISHED'}
    

class SHELLARC_forcesubmit_Nop(Operator):

    bl_idname = "object.shellarc_forcesubmit_nop"
    bl_label = "NOP"
    bl_description = "強制アップする"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        asset_name = context.scene.shellarc_prop_enum
        if Path(bpy.data.filepath).stem != asset_name:
            self.report({'INFO', f"Invalid file. Submit to the right file"})
            return {'CANCELLED'}
        LocalOperation.freeze_locally(ctx=context)
        bpy.ops.wm.save_as_mainfile(filepath=f"{context.scene.shellarc_prop_str_savepath}/{asset_name}.blend")
        backend_communication = BackendCommunication(ctx=context)
        submit_status = backend_communication.submit_action(
            ctx=context,
            asset_name=asset_name,
            status=["2", ""]
        )
        if submit_status != asset_name:
            self.report({'INFO'}, f"error : {submit_status}")
            return {'CANCELLED'}
        bpy.context.scene["under_progress"] = False
        context.scene.shellarc_prop_str_exlocksta = "Opening"
        update_asset_list(backend_communication=backend_communication)
        self.report({'INFO'}, f"submitted")
        return {'FINISHED'}
    
    
class SHELLARC_exclock_Nop(Operator):

    bl_idname = "object.shellarc_exclock_nop"
    bl_label = "NOP"
    bl_description = "排他ロックをかける"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        asset_name = context.scene.shellarc_prop_enum
        backend_communication = BackendCommunication(ctx=context)
        addon_pref = bpy.context.preferences.addons[__package__].preferences
        mem_id = str(addon_pref.member_id)
        current_asset_metadata = backend_communication.get_asset_metadata()[asset_name]
        if current_asset_metadata[0] not in ["1", "2"]:
            if current_asset_metadata[1] != mem_id:
                self.report({'INFO'}, f"locking failed. Someone is locking")
                return {'CANCELLED'}
            backend_communication.set_asset_metadata(
                asset_name=asset_name,
                status=["2", ""]
            )
            context.scene.shellarc_prop_str_exlocksta = "Opening"
        else:
            backend_communication.set_asset_metadata(
                asset_name=asset_name,
                status=["4", mem_id]
                )
            context.scene.shellarc_prop_str_exlocksta = "Locked"
        self.report({'INFO'}, f"locked")
        return {'FINISHED'}
    

class SHELLARC_reloadassetlist_Nop(Operator):

    bl_idname = "object.shellarc_reloadassetlist_nop"
    bl_label = "NOP"
    bl_description = "アセットリストをリロードする"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        update_asset_list()
        return {'FINISHED'}
    

class SHELLARC_commitfile_Nop(Operator):

    bl_idname = "object.shellarc_commitfile_nop"
    bl_label = "NOP"
    bl_description = "ファイルをサーバでキャッシュする"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        LocalOperation.snapshot_file(ctx=context)
        return {'FINISHED'}
    

class SHELLARC_submitfile_Nop(Operator):

    bl_idname = "object.shellarc_submitfile_nop"
    bl_label = "NOP"
    bl_description = "ファイルをサーバに提出する"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        asset_name=Path(bpy.data.filepath).stem
        backend_communication = BackendCommunication(ctx=context)
        submit_status = backend_communication.submit_action(
            ctx=context,
            asset_name=asset_name,
            status=["2", ""]
        )
        if submit_status != asset_name:
            self.report({'INFO'}, f"error : {submit_status}")
            return {'CANCELLED'}
        bpy.context.scene["under_progress"] = False
        context.scene.shellarc_prop_str_exlocksta = "Opening"
        update_asset_list(backend_communication=backend_communication)
        bpy.app.timers.unregister(LocalOperation.shellarc_autosave)
        self.report({'INFO'}, f"submitted")
        return {'FINISHED'}
    

class SHELLARC_checkoutfile_Nop(Operator):

    bl_idname = "object.shellarc_checkoutfile_nop"
    bl_label = "NOP"
    bl_description = "ファイルをチェックアウトする"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        asset_name=Path(bpy.data.filepath).stem
        backend_communication = BackendCommunication(ctx=context)
        backend_communication.set_asset_metadata(
            asset_name=asset_name,
            status=["2", ""]
        )
        bpy.ops.wm.save_as_mainfile()
        bpy.context.scene["under_progress"] = False
        context.scene.shellarc_prop_str_exlocksta = "Opening"
        update_asset_list(backend_communication=backend_communication)
        LocalOperation.delete_snapshot_dir(ctx=context)
        bpy.app.timers.unregister(LocalOperation.shellarc_autosave)
        return {'FINISHED'}
    

class SHELLARC_appendasset_Nop(Operator):
    bl_idname = "object.shellarc_appendasset_nop"
    bl_label = "NOP"
    bl_description = "アセットをシーンに統合"
    bl_options = {'REGISTER', 'UNDO'}

    asset : StringProperty()

    def execute(self, context):
        backend_communication = BackendCommunication()
        backend_communication.append_asset(
            asset_name=self.asset,
            current_dir=context.scene.shellarc_prop_str_savepath
        )
        return {'FINISHED'}
    

class SHELLARC_reloadtmpasset_Nop(Operator):
    bl_idname = "object.shellarc_reloadtmpasset_nop"
    bl_label = "NOP"
    bl_description = "アセットリストをリロード"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        update_asset_list(force_load_asset_list=True)
        return {'FINISHED'}
    

class SHELLARC_reflog_Nop(Operator):

    bl_idname = "object.shellarc_reflog_nop"
    bl_label = "NOP"
    bl_description = "履歴を戻す"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        cache_path = Path(__file__).resolve().parent / "cache_reflogidx.pkl"
        if not cache_path.exists():
            LocalOperation.freeze_locally(ctx=context)
            frozen_files = LocalOperation.get_frozen_files()
            if not frozen_files:
                return {'CANCELLED'}
        with open(cache_path, "rb") as f:
            frozen_files_list = pickle.load(f)
        idx = context.scene.shellarc_prop_int_reflogidx
        LocalOperation.open_frozen_file(
            ctx=context,
            frozen_file_path=frozen_files_list[idx]
            )
        if idx < len(frozen_files_list):
            context.scene.shellarc_prop_int_reflogidx = idx + 1
        else:
            context.scene.shellarc_prop_int_reflogidx = 0
        return {'FINISHED'}


class SHELLARC_reflogconfirm_Nop(Operator):

    bl_idname = "object.shellarc_reflogconfirm_nop"
    bl_label = "NOP"
    bl_description = "選択中の履歴に固定"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        context.scene.shellarc_prop_int_reflogidx = 0
        cache_path = Path(__file__).resolve().parent / "cache_reflogidx.pkl"
        if cache_path.exists():
            os.unlink(cache_path)
        return {'FINISHED'}
    

class SHELLARC_login_Nop(Operator):

    bl_idname = "object.shellarc_login_nop"
    bl_label = "NOP"
    bl_description = "ログインする"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        import keyring
        if not keyring.get_password("shellarc", "shellarc"):
            decode_key = context.scene.shellarc_prop_str_decodekey
            keyring.set_password("shellarc", "shellarc", decode_key)

        pref = context.preferences
        addon_pref = pref.addons[__package__].preferences
        mem_id = context.scene.shellarc_prop_str_memid

        backend_communication = BackendCommunication(ctx=context)
        accessible_asset_set = backend_communication.get_member_data(mem_id=mem_id)
        if accessible_asset_set == []:
            self.report({'INFO'}, f"Invalid ID")
            return {'CANCELLED'}
        addon_pref.member_id = mem_id
        update_asset_list(backend_communication=backend_communication)
        self.report({'INFO'}, f"logged-in as {mem_id}")
        return {'FINISHED'}


class SHELLARC_logout_Nop(Operator):

    bl_idname = "object.shellarc_logout_nop"
    bl_label = "NOP"
    bl_description = "ログアウトする"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        pref = context.preferences
        addon_pref = pref.addons[__package__].preferences
        addon_pref.member_id = ""
        self.report({'INFO'}, f"logged-out")
        return {'FINISHED'}
    

class SHELLARC_clearcache_Nop(Operator):

    bl_idname = "object.shellarc_clearcache_nop"
    bl_label = "NOP"
    bl_description = "安全キャッシュをクリアする"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        LocalOperation.delete_freeze_dir(
            ctx=context
            )
        return {'FINISHED'}
    