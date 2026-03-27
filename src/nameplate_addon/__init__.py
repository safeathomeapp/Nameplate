bl_info = {
    "name": "Nameplate Generator",
    "author": "OpenAI Codex",
    "version": (0, 1, 0),
    "blender": (5, 0, 0),
    "location": "View3D > Sidebar > Name Plate",
    "description": "Foundation package for a procedural tabletop nameplate generator.",
    "category": "3D View",
}

import bpy

from . import operators, properties, ui

CLASSES = (
    properties.NameplateSettings,
    operators.NAMEPLATE_OT_build_reference_objects,
    operators.NAMEPLATE_OT_reset_reference_objects,
    ui.NAMEPLATE_PT_main_panel,
)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)

    bpy.types.Scene.nameplate_settings = bpy.props.PointerProperty(
        type=properties.NameplateSettings
    )


def unregister():
    del bpy.types.Scene.nameplate_settings

    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
