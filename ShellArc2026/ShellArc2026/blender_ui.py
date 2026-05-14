import os
import sys
import pickle
from pathlib import Path

import bpy
from bpy.types import Operator, Panel
from bpy.props import (
    IntProperty,
    EnumProperty,
    StringProperty,
    BoolProperty
)

import keyring

from .shellarc_action import BlenderOperation, BackendCommunication

def update_asset_list(backend_communication: BackendCommunication | None=None) -> None:
    asset_list = []
    if backend_communication is None:
        backend_communication = BackendCommunication()
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
    cache_path = Path(__file__).resolve().parent / "asset_list.pkl"
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
        if BlenderOperation.is_snapshot_exists(asset_name=asset_name):
            BlenderOperation.open_snapshot()
            self.report({'INFO'}, f"recovered crashed blend file")
        else:
            backend_communication = BackendCommunication()
            addon_pref = bpy.context.preferences.addons[__package__].preferences
            mem_id = str(addon_pref.member_id)
            getfile_status = backend_communication.request_asset(
                mem_id=mem_id,
                asset_name=asset_name,
                saving_dir=context.scene.shellarc_prop_str_savepath
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
        bpy.app.timers.register(BlenderOperation.shellarc_autosave)
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
        BlenderOperation.freeze_locally()
        bpy.ops.wm.save_as_mainfile(filepath=f"{context.scene.shellarc_prop_str_savepath}/{asset_name}.blend")
        backend_communication = BackendCommunication()
        submit_status = backend_communication.submit_action(
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
        backend_communication = BackendCommunication()
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
        BlenderOperation().snapshot_file()
        return {'FINISHED'}
    
class SHELLARC_submitfile_Nop(Operator):

    bl_idname = "object.shellarc_submitfile_nop"
    bl_label = "NOP"
    bl_description = "ファイルをサーバに提出する"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        asset_name=Path(bpy.data.filepath).stem
        backend_communication = BackendCommunication()
        submit_status = backend_communication.submit_action(
            asset_name=asset_name,
            status=["2", ""]
        )
        if submit_status != asset_name:
            self.report({'INFO'}, f"error : {submit_status}")
            return {'CANCELLED'}
        bpy.context.scene["under_progress"] = False
        context.scene.shellarc_prop_str_exlocksta = "Opening"
        update_asset_list(backend_communication=backend_communication)
        bpy.app.timers.unregister(BlenderOperation.shellarc_autosave)
        self.report({'INFO'}, f"submitted")
        return {'FINISHED'}
    
class SHELLARC_checkoutfile_Nop(Operator):

    bl_idname = "object.shellarc_checkoutfile_nop"
    bl_label = "NOP"
    bl_description = "ファイルをチェックアウトする"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        asset_name=Path(bpy.data.filepath).stem
        backend_communication = BackendCommunication()
        backend_communication.set_asset_metadata(
            asset_name=asset_name,
            status=["2", ""]
        )
        bpy.ops.wm.save_as_mainfile()
        bpy.context.scene["under_progress"] = False
        context.scene.shellarc_prop_str_exlocksta = "Opening"
        update_asset_list(backend_communication=backend_communication)
        BlenderOperation.delete_snapshot_dir()
        bpy.app.timers.unregister(BlenderOperation.shellarc_autosave)
        return {'FINISHED'}
    
class SHELLARC_reflog_Nop(Operator):

    bl_idname = "object.shellarc_reflog_nop"
    bl_label = "NOP"
    bl_description = "履歴を戻す"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        cache_path = Path(__file__).resolve().parent / "cache_reflogidx.pkl"
        if not cache_path.exists():
            BlenderOperation.freeze_locally()
            frozen_files = BlenderOperation.get_frozen_files()
            if not frozen_files:
                return {'CANCELLED'}
        with open(cache_path, "rb") as f:
            frozen_files_list = pickle.load(f)
        idx = context.scene.shellarc_prop_int_reflogidx
        BlenderOperation.open_frozen_file(frozen_file_path=frozen_files_list[idx])
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
        if not keyring.get_password("shellarc", "shellarc"):
            decode_key = context.scene.shellarc_prop_str_decodekey
            keyring.set_password("shellarc", "shellarc", decode_key)

        pref = context.preferences
        addon_pref = pref.addons[__package__].preferences
        mem_id = context.scene.shellarc_prop_str_memid

        backend_communication = BackendCommunication()
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
        BlenderOperation.delete_freeze_dir()
        return {'FINISHED'}


class SHELLARC_BLENDER_CustomPanel(Panel):

    bl_label = "ShellArc 2026"         
    bl_space_type = 'VIEW_3D'           
    bl_region_type = 'UI'               
    bl_category = "ShellArc"      
    bl_context = "objectmode"        

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon='PLUGIN')

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        pref = context.preferences
        addon_pref = pref.addons[__package__].preferences
        mem_id = addon_pref.member_id if addon_pref is not None else ""

        if not mem_id:
            layout.prop(scene, "shellarc_prop_str_memid", text="作業者ID")
            if not keyring.get_password("shellarc", "shellarc"):
                layout.prop(scene, "shellarc_prop_str_decodekey", text="デコードキー")
            layout.operator(SHELLARC_login_Nop.bl_idname, text="ログイン")

        elif mem_id.startswith("m"):

            if "under_progress" not in bpy.context.scene or bpy.context.scene["under_progress"] is False:
                current_mode = "今 : モデリングモード" if scene.shellarc_prop_bool_ismodellingmode else "今 : レイアウトモード"
                layout.operator(SHELLARC_modetoggle_Nop.bl_idname, text=current_mode)
                layout.separator()

                if scene.shellarc_prop_bool_ismodellingmode:
                    layout.prop(scene, "shellarc_prop_enum", text="アセット")
                    layout.prop(scene, "shellarc_prop_str_savepath", text="保存ディレクトリ")
                    layout.separator()
                    layout.operator(SHELLARC_getfile_Nop.bl_idname, text="ロード")
                    layout.operator(SHELLARC_forcesubmit_Nop.bl_idname, text="強制アップ")
                    split = layout.split(factor=0.7)
                    column = split.column(align=True)
                    column.operator(SHELLARC_exclock_Nop.bl_idname, text="排他ロック")
                    split = split.split(factor=1.0)
                    column = split.column(align=True)
                    column.label(text=scene.shellarc_prop_str_exlocksta)
                    layout.operator(SHELLARC_reloadassetlist_Nop.bl_idname, text="アセットリストをリロード")

                else:
                    pass

                layout.separator()
                freeze_dir_size = scene.shellarc_prop_str_freezedirsize
                layout.operator(SHELLARC_clearcache_Nop.bl_idname, text=f"キャッシュをクリア ({freeze_dir_size})")
                layout.operator(SHELLARC_logout_Nop.bl_idname, text="ログアウト")

            else:
                layout.operator(SHELLARC_commitfile_Nop.bl_idname, text="キャッシュ")
                layout.operator(SHELLARC_submitfile_Nop.bl_idname, text="アップ")
                layout.operator(SHELLARC_checkoutfile_Nop.bl_idname, text="チェックアウト")
                split = layout.split(factor=0.8)
                column = split.column(align=True)
                column.operator(SHELLARC_reflog_Nop.bl_idname, text="過去履歴に戻す")
                split = split.split(factor=1.0)
                column = split.column(align=True)
                column.operator(SHELLARC_reflogconfirm_Nop.bl_idname, text="固定")


def read_asset_list(self, context) -> list[str]:
    cache_path = Path(__file__).resolve().parent / "asset_list.pkl"
    if not cache_path.exists():
        return []
    with open(cache_path, "rb") as f:
        asset_list = pickle.load(f)
    return asset_list

def init_props():
    scene = bpy.types.Scene
    scene.shellarc_prop_bool_ismodellingmode = BoolProperty(
        name="モード",
        description="モード（モデリングモードとレイアウトモード）をスイッチ",
        default=True
    )
    scene.shellarc_prop_str_decodekey = StringProperty(
        name="鍵",
        description="デコードキーを入力してください（わからない場合は問い合わせてください）",
        subtype="PASSWORD",
        default=""
    )
    scene.shellarc_prop_str_memid = StringProperty(
        name="作業者ID",
        description="Discordボットから発行された6桁のIDを入力してください",
        default=""
    )
    scene.shellarc_prop_str_savepath = StringProperty(
        name="保存ディレクトリ",
        description="ファイルを格納するディレクトリを指定してください",
        default=f"{os.path.expanduser("~")}/Downloads"
    )
    scene.shellarc_prop_enum = EnumProperty(
        name="アセット",
        description="アセットを選択してください",
        items=read_asset_list
    )
    scene.shellarc_prop_str_exlocksta = StringProperty(
        name="排他ロック状態",
        description="排他ロックの状態",
        default="Opening"
    )
    scene.shellarc_prop_str_freezedirsize = StringProperty(
        name="キャッシュディレクトリサイズ",
        description="キャッシュディレクトリのサイズ（MB）",
        default=f"{BlenderOperation.get_freeze_dir_size()}MB"
    )
    scene.shellarc_prop_int_reflogidx = IntProperty(
        name="履歴インデックス",
        description="走査中の履歴のインデックス",
        default=0
    )