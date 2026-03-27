import bpy

from .helpers import (
    create_base_object,
    create_empty_object,
    create_path_object,
    create_plate_object,
    delete_managed_objects,
    get_settings,
    reset_settings,
    tag_view_layer_for_update,
    workflow_summary,
)


class NAMEPLATE_OT_build_reference_objects(bpy.types.Operator):
    bl_idname = "nameplate.build_reference_objects"
    bl_label = "Build References"
    bl_description = "Create deterministic BASE, EMPTY, conditional PATH, and PLATE objects"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = get_settings(context)
        removed_names = delete_managed_objects(context)
        created_names = []

        empty = create_empty_object(context)
        created_names.append(empty.name)
        created_names.append(create_base_object(context, settings, parent=empty).name)
        path = create_path_object(context, settings, parent=empty)
        if path is not None:
            created_names.append(path.name)
        created_names.append(create_plate_object(context, settings, parent=empty).name)

        removed_text = ", ".join(removed_names) if removed_names else "none"
        created_text = ", ".join(created_names)
        settings.status_message = (
            f"Phase 2B build complete. Created: {created_text}. "
            f"Removed previous managed objects: {removed_text}. "
            f"{workflow_summary(settings)}"
        )
        tag_view_layer_for_update(context)
        self.report({"INFO"}, settings.status_message)
        return {"FINISHED"}


class NAMEPLATE_OT_reset_reference_objects(bpy.types.Operator):
    bl_idname = "nameplate.reset_reference_objects"
    bl_label = "Start Over"
    bl_description = "Delete managed Phase 2 objects and reset settings"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = get_settings(context)
        removed_names = delete_managed_objects(context)
        reset_settings(settings)
        settings.status_message = (
            "Reset complete. Removed managed objects: "
            f"{', '.join(removed_names) if removed_names else 'none'}."
        )
        tag_view_layer_for_update(context)
        self.report({"INFO"}, settings.status_message)
        return {"FINISHED"}
