import os
import sys
import pickle
from pathlib import Path

import bpy
from bpy.types import Panel
from bpy.props import (
    IntProperty,
    EnumProperty,
    StringProperty,
    BoolProperty
)

from .shellarc_blender_action import LocalOperation
from shellarc_ui_action import (
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
            import keyring
            if not keyring.get_password("shellarc", "shellarc"):
                layout.prop(scene, "shellarc_prop_str_decodekey", text="デコードキー")
            layout.operator(SHELLARC_login_Nop.bl_idname, text="ログイン")

        elif mem_id.startswith("m"):

            if "under_progress" not in bpy.context.scene or bpy.context.scene["under_progress"] is False:
                current_mode = "今 : モデリングモード" if scene.shellarc_prop_bool_ismodellingmode else "今 : レイアウトモード"
                layout.operator(SHELLARC_modetoggle_Nop.bl_idname, text=current_mode)
                layout.separator()

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

                layout.separator()
                freeze_dir_size = scene.shellarc_prop_str_freezedirsize
                layout.operator(SHELLARC_clearcache_Nop.bl_idname, text=f"キャッシュをクリア ({freeze_dir_size})")
                layout.operator(SHELLARC_logout_Nop.bl_idname, text="ログアウト")

            else:
                layout.operator(SHELLARC_commitfile_Nop.bl_idname, text="キャッシュ")
                layout.operator(SHELLARC_submitfile_Nop.bl_idname, text="アップ")
                layout.operator(SHELLARC_checkoutfile_Nop.bl_idname, text="チェックアウト")

                if scene.shellarc_prop_bool_ismodellingmode:
                    layout.separator()
                    split = layout.split(factor=0.3)
                    column = split.column(align=True)
                    column.label(text="アセット：")
                    split = split.split(factor=0.4)
                    column = split.column(align=True)
                    column.operator(SHELLARC_reloadtmpasset_Nop.bl_idname, text="⟳")
                    for asset_tuple in scene.shellarc_prop_enum_assets:
                        asset = asset_tuple[0]
                        split = layout.split(factor=0.3)
                        column = split.column(align=True)
                        column.label(text=asset)
                        split = split.split(factor=1.0)
                        column = split.column(align=True)
                        merge_ope = column.operator(SHELLARC_appendasset_Nop.bl_idname, text="統合")
                        merge_ope.asset = asset

                layout.separator()    
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

def read_asset_list_f(self, context) -> list[str]:
    cache_path = Path(__file__).resolve().parent / "tmp_asset_list.pkl"
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
    scene.shellarc_prop_enum_assets = EnumProperty(
        name="アセットリスト",
        description="統合するアセットを選択してください",
        items=read_asset_list_f
    )
    scene.shellarc_prop_str_exlocksta = StringProperty(
        name="排他ロック状態",
        description="排他ロックの状態",
        default="Opening"
    )
    scene.shellarc_prop_str_freezedirsize = StringProperty(
        name="キャッシュディレクトリサイズ",
        description="キャッシュディレクトリのサイズ（MB）",
        default=f"{LocalOperation.get_freeze_dir_size()}MB"
    )
    scene.shellarc_prop_int_reflogidx = IntProperty(
        name="履歴インデックス",
        description="走査中の履歴のインデックス",
        default=0
    )