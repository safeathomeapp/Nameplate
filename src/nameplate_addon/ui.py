import bpy

from .constants import ADDON_TAB
from .helpers import (
    base_dimensions_m,
    base_preset_label,
    get_settings,
    list_managed_objects,
    object_role,
    parse_base_preset_mm,
    path_required,
)


def draw_base_preset(layout, settings):
    family_key = settings.base_family.lower()
    layout.prop(settings, f"base_preset_{family_key}", text="Base Size")


class NAMEPLATE_PT_main_panel(bpy.types.Panel):
    bl_label = "Name Plate"
    bl_idname = "NAMEPLATE_PT_main_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = ADDON_TAB

    def draw(self, context):
        layout = self.layout
        settings = get_settings(context)
        width_m, depth_m = base_dimensions_m(settings)
        width_mm, depth_mm = parse_base_preset_mm(settings)
        managed_objects = list_managed_objects(context)

        setup_box = layout.box()
        setup_box.label(text="Phase 1 Reference Objects")
        setup_box.prop(settings, "workflow_mode", text="")
        setup_box.prop(settings, "base_family")
        draw_base_preset(setup_box, settings)
        setup_box.label(
            text=f"Preset source: {width_mm:.0f}mm x {depth_mm:.0f}mm"
        )
        setup_box.label(
            text=f"Working footprint: {width_m * 1000:.0f}mm x {depth_m * 1000:.0f}mm"
        )
        setup_box.label(text=f"PATH required: {'Yes' if path_required(settings) else 'No'}")

        status_box = layout.box()
        status_box.label(text="Status")
        status_box.label(text=settings.status_message)

        action_row = layout.row(align=True)
        action_row.operator("nameplate.build_reference_objects", icon="MOD_BUILD")
        action_row.operator("nameplate.reset_reference_objects", icon="LOOP_BACK")

        managed_box = layout.box()
        managed_box.label(text="Managed Objects")
        if managed_objects:
            for obj in managed_objects:
                managed_box.label(text=f"{obj.name} ({object_role(obj)})")
        else:
            managed_box.label(text="None")

        footer = layout.box()
        footer.label(text=f"Selected preset: {base_preset_label(settings)}")
        footer.label(text="This phase creates only BASE, EMPTY, and conditional PATH.")
