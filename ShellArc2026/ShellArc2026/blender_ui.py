import bpy
from bpy.types import Operator, Panel
from bpy.props import (
    EnumProperty,
    StringProperty
)

    
class SHELLARC_getfile_Nop(Operator):

    bl_idname = "object.shellarc_getfile_nop"
    bl_label = "NOP"
    bl_description = "ファイルをサーバからロードする"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.context.scene["under_progress"] = True
        self.report({'INFO'}, f"loaded blend file")
        return {'FINISHED'}
    
class SHELLARC_commitfile_Nop(Operator):

    bl_idname = "object.shellarc_commitfile_nop"
    bl_label = "NOP"
    bl_description = "ファイルをサーバでキャッシュする"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        return {'FINISHED'}
    
class SHELLARC_submitfile_Nop(Operator):

    bl_idname = "object.shellarc_submitfile_nop"
    bl_label = "NOP"
    bl_description = "ファイルをサーバに提出する"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        return {'FINISHED'}
    
class SHELLARC_login_Nop(Operator):

    bl_idname = "object.shellarc_login_nop"
    bl_label = "NOP"
    bl_description = "ログインする"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        pref = context.preferences
        addon_pref = pref.addons[__package__].preferences
        mem_id = context.scene.shellarc_prop_str
        addon_pref.member_id = mem_id
        self.report({'INFO'}, f"logged-in as {mem_id}")
        return {'FINISHED'}

class SHELLARC_logout_Nop(Operator):

    bl_idname = "object.shellarc_logout_nop"
    bl_label = "NOP"
    bl_description = "何もしない"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        pref = context.preferences
        addon_pref = pref.addons[__package__].preferences
        addon_pref.member_id = ""
        self.report({'INFO'}, f"logged-out")
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
            layout.prop(scene, "shellarc_prop_str", text="作業者ID")
            layout.operator(SHELLARC_login_Nop.bl_idname, text="ログイン")

        elif mem_id.startswith("m"):

            if "under_progress" not in bpy.context.scene or bpy.context.scene["under_progress"] is False:
                layout.prop(scene, "shellarc_prop_enum", text="アセット")
                layout.separator()
                layout.operator(SHELLARC_getfile_Nop.bl_idname, text="ロードする")

            else:
                layout.operator(SHELLARC_commitfile_Nop.bl_idname, text="キャッシュする")
                layout.operator(SHELLARC_submitfile_Nop.bl_idname, text="アップする")


def init_props():
    scene = bpy.types.Scene
    scene.shellarc_prop_str = StringProperty(
        name="作業者ID",
        description="Discordボットから発行された6桁のIDを入力してください",
        default=""
    )
    scene.shellarc_prop_enum = EnumProperty(
        name="アセット",
        description="アセットを選択してください",
        items=[
            ('ITEM_1', "ビル", "ビル"),
            ('ITEM_2', "車", "車"),
            ('ITEM_3', "湖", "湖")
        ],
        default='ITEM_1'
    )