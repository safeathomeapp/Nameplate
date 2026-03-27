import bpy

from .constants import (
    BASE_FAMILY_ITEMS,
    BASE_PRESETS,
    DEFAULT_SETTINGS,
    WORKFLOW_MODE_ITEMS,
)


class NameplateSettings(bpy.types.PropertyGroup):
    workflow_mode: bpy.props.EnumProperty(
        name="Workflow",
        items=WORKFLOW_MODE_ITEMS,
        default=DEFAULT_SETTINGS["workflow_mode"],
    )
    base_family: bpy.props.EnumProperty(
        name="Base Family",
        items=BASE_FAMILY_ITEMS,
        default=DEFAULT_SETTINGS["base_family"],
    )
    base_preset_circle: bpy.props.EnumProperty(
        name="Circle Preset",
        items=BASE_PRESETS["CIRCLE"],
        default=DEFAULT_SETTINGS["base_preset_circle"],
    )
    base_preset_oval: bpy.props.EnumProperty(
        name="Oval Preset",
        items=BASE_PRESETS["OVAL"],
        default=DEFAULT_SETTINGS["base_preset_oval"],
    )
    base_preset_square: bpy.props.EnumProperty(
        name="Square Preset",
        items=BASE_PRESETS["SQUARE"],
        default=DEFAULT_SETTINGS["base_preset_square"],
    )
    base_preset_special: bpy.props.EnumProperty(
        name="Special Preset",
        items=BASE_PRESETS["SPECIAL"],
        default=DEFAULT_SETTINGS["base_preset_special"],
    )
    status_message: bpy.props.StringProperty(
        name="Status",
        default=DEFAULT_SETTINGS["status_message"],
    )
