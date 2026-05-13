import bpy
from bpy.types import AddonPreferences
from bpy.props import StringProperty


class SHELLARC_AddonPreferences(AddonPreferences):
    bl_idname = __package__

    member_id: StringProperty(
        name="6-digit member ID",
        default=""
    )