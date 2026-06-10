import bpy
from bpy.types import AddonPreferences
from bpy.props import StringProperty, FloatProperty


class SHELLARC_AddonPreferences(AddonPreferences):
    bl_idname = "bl_ext.user_default.ShellArc2026"

    member_id: StringProperty(
        name="6桁メンバーID",
        default=""
    )
    preserve_latest_cache: FloatProperty(
        name="直近N秒のキャッシュを保護する",
        default=250000.0
    )

    def draw(self, context):
        layout = self.layout
        layout.label(text="ShellArc2026 Blenderアドオンプレファレンス設定")
        layout.prop(self, "preserve_latest_cache")