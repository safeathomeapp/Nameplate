import bpy
import os
from bpy.types import Panel
from bpy.app.handlers import persistent

from .constants import (
    BASE_OBJECT,
    EMPTY_OBJECT,
    IMPORT_PLATE_OBJECT,
    LEFT_NURNIE_OBJECT,
    MAIN_TEXT_OBJECT,
    PLATE_OBJECT,
    RIGHT_NURNIE_OBJECT,
    UPPER_TEXT_OBJECT,
)
from .icons import get_icon_id

_LAST_ACTIVE_TARGET_NAME = None


def _get_target_object(context, target_name):
    return context.scene.objects.get(target_name)


def _draw_section_header(layout, title, icon):
    box = layout.box()
    box.label(text=title, icon=icon)
    return box


def _draw_enum_button_row(layout, data_path, current_value, items):
    row = layout.row(align=True)
    for value, label in items:
        op = row.operator(
            "wm.context_set_enum",
            text=label,
            depress=(str(current_value) == str(value)),
        )
        op.data_path = data_path
        op.value = str(value)


def _draw_end_style_icon_row(layout, data_path, current_value):
    grid = layout.grid_flow(
        row_major=True,
        columns=4,
        even_columns=True,
        even_rows=True,
        align=True,
    )

    button_defs = (
        ("PLAIN", "SQUARE"),
        ("CHAMFER", "CHAMFERED"),
        ("SLANT", "SLANTED"),
        ("BEVEL", "ROUNDED"),
    )

    for enum_value, icon_name in button_defs:
        cell = grid.column(align=True)
        op = cell.operator(
            "wm.context_set_enum",
            text="",
            icon_value=get_icon_id(icon_name),
            depress=(str(current_value) == enum_value),
        )
        op.data_path = data_path
        op.value = enum_value


def _sync_edit_target_from_active_object(context, mytool):
    active_obj = context.object
    if active_obj is None:
        return

    target_names = {
        PLATE_OBJECT,
        MAIN_TEXT_OBJECT,
        UPPER_TEXT_OBJECT,
        LEFT_NURNIE_OBJECT,
        RIGHT_NURNIE_OBJECT,
    }

    if active_obj.name in target_names and mytool.my_item != active_obj.name:
        mytool.my_item = active_obj.name


@persistent
def _sync_edit_target_handler(_scene, _depsgraph):
    global _LAST_ACTIVE_TARGET_NAME

    context = bpy.context
    scene = getattr(context, "scene", None)
    if scene is None or not hasattr(scene, "my_tool"):
        return

    if getattr(context, "mode", "OBJECT") != 'OBJECT':
        return

    active_obj = getattr(context, "object", None)
    if active_obj is None:
        return

    plate_obj = scene.objects.get(PLATE_OBJECT)
    if not plate_obj:
        _LAST_ACTIVE_TARGET_NAME = None
        return

    target_names = {
        PLATE_OBJECT,
        MAIN_TEXT_OBJECT,
        UPPER_TEXT_OBJECT,
        LEFT_NURNIE_OBJECT,
        RIGHT_NURNIE_OBJECT,
    }

    active_name = active_obj.name
    if active_name not in target_names:
        return

    if active_name == _LAST_ACTIVE_TARGET_NAME:
        return

    try:
        _sync_edit_target_from_active_object(context, scene.my_tool)
        _LAST_ACTIVE_TARGET_NAME = active_name
    except Exception:
        pass


def _draw_edit_actions(layout, mytool, import_plate):
    box = _draw_section_header(layout, "Edit And Export", 'TOOL_SETTINGS')
    box.label(text="Edit Target", icon='GREASEPENCIL')
    box.prop(mytool, "my_item", expand=True)
    row = box.row(align=True)
    row.operator("object.export_stl_custom", text="Export STL", icon='DISK_DRIVE')
    row.operator("clear_scene.myop_operator", text="Start Over", icon='RECOVER_LAST')
    if not import_plate:
        box.operator("draw.myop_operator", text="Rebuild Plate", icon='FILE_REFRESH')


def _draw_setup_panel(layout, mytool, base_obj):
    box = _draw_section_header(layout, "Setup", 'SETTINGS')
    box.label(text="Choose a workflow")
    box.prop(mytool, "my_newbase", expand=True)

    if mytool.my_newbase == "IMPORT":
        import_box = layout.box()
        import_box.label(text="Import a previously saved plate", icon='IMPORT')
        import_box.operator("object.import_stl_custom", text="Import a Saved Plate", icon='FILE_NEW')
        return

    create_box = layout.box()
    create_box.label(text="Create a new plate", icon='FILE_NEW')
    create_box.label(text="Choose your base shape", icon='PROP_ON')
    create_box.prop(mytool, "my_baselist", expand=True)
    create_box.label(text="Choose your base size", icon='PROP_ON')
    create_box.prop(mytool, "my_" + mytool.my_baselist, expand=True)
    if base_obj:
        create_box.operator("getready.myop_operator", text="Confirm Base Choice", icon='CHECKBOX_HLT')


def _draw_import_alignment_panel(layout, mytool, base_obj):
    box = _draw_section_header(layout, "Import Alignment", 'IMPORT')
    box.operator("wm.importhelp", text="Read Import Note")
    box.label(text="Choose your base shape", icon='PROP_ON')
    box.prop(mytool, "my_baselist", expand=True)
    box.label(text="Choose your base size", icon='PROP_ON')
    box.prop(mytool, "my_" + mytool.my_baselist, expand=True)
    if base_obj:
        box.operator("getready.myop_operator", text="Confirm Base Choice", icon='CHECKBOX_HLT')


def _draw_text_editor(layout, obj, text, mytool, engrave_prop, italic_prop, extra_prop_name):
    box = _draw_section_header(layout, "Text", 'SMALL_CAPS')
    box.prop(text, 'body', text="")

    box = _draw_section_header(layout, "Font And Position", 'FONT_DATA')
    box.template_ID(text, "font", open="font.open", unlink="font.unlink")

    row = box.row()
    row.label(text="Engrave On Export")
    row.prop(mytool, engrave_prop)

    row = box.row()
    row.label(text="Italic")
    row.prop(mytool, italic_prop)

    box.prop(text, "size", text="Text Size")
    box.label(text="Position", icon='ORIENTATION_GLOBAL')
    box.prop(obj, 'myZFloat', slider=False)
    box.prop(obj, 'myYFloat', slider=False)

    box = _draw_section_header(layout, "Text Extras", 'PREFERENCES')
    row = box.row()
    row.prop(mytool, extra_prop_name)
    row.label(text="Extra Options")
    if getattr(mytool, extra_prop_name):
        box.label(text="Spacing", icon='CENTER_ONLY')
        row = box.row()
        row.label(text="Characters")
        row.prop(text, "space_character", text="")
        row = box.row()
        row.label(text="Words")
        row.prop(text, "space_word", text="")
        box.operator("increasevoxel.myop_operator", text="Increase Text Clarity", icon='MOD_THICKNESS')
        box.operator("decreasevoxel.myop_operator", text="Decrease Text Clarity", icon='MOD_SMOOTH')


def _draw_nurnie_editor(layout, obj, wm, base_type, side):
    side_title = "Left Nurnie" if side == "LEFT" else "Right Nurnie"
    flip_operator = "flipnurnieleft.myop_operator" if side == "LEFT" else "flipnurnieright.myop_operator"
    mirror_operator = "mirrornurnieleft.myop_operator" if side == "LEFT" else "mirrornurnieright.myop_operator"
    change_operator = "changenurnieleft.myop_operator" if side == "LEFT" else "changenurnieright.myop_operator"
    delete_operator = "deletenurnieleft.myop_operator" if side == "LEFT" else "deletenurnieright.myop_operator"

    box = _draw_section_header(layout, side_title, 'MESH_PLANE')
    loc_text = "Left / Right" if base_type == "S" else "Around Curve"
    box.prop(obj, 'location', index=0, text=loc_text)
    box.prop(obj, 'myNurnZFloat', slider=False)
    box.prop(obj, 'myNurnYFloat', slider=False)
    box.prop(obj, "instance_faces_scale", text="Scale", slider=False)
    box.operator(flip_operator, text="Flip Nurnie", icon='MOD_MIRROR')
    box.operator(mirror_operator, text="Mirror To Other Side", icon='UV_SYNC_SELECT')

    box = _draw_section_header(layout, "Asset", 'FILE_FOLDER')
    box.prop(wm, "my_previews_dir")
    box.template_icon_view(wm, "my_previews")
    box.operator(change_operator, text="Change Nurnie", icon='FILE_REFRESH')

    box = _draw_section_header(layout, "Remove", 'TRASH')
    box.operator(delete_operator, text="Remove Nurnie", icon='TRASH')


def _draw_nurnie_add(layout, wm, side):
    label = "Add Left Nurnie" if side == "LEFT" else "Add Right Nurnie"
    operator = "addnurnieleft.myop_operator" if side == "LEFT" else "addnurnieright.myop_operator"
    previews_dir = getattr(wm, "my_previews_dir", "")
    preview_value = getattr(wm, "my_previews", "")
    has_valid_dir = bool(previews_dir and os.path.isdir(previews_dir))
    has_preview_choice = bool(preview_value)
    can_add_nurnie = has_valid_dir and has_preview_choice

    box = _draw_section_header(layout, label, 'MESH_PLANE')
    box.label(text="Choose an icon and add it to the plate.")
    box.prop(wm, "my_previews_dir")
    box.template_icon_view(wm, "my_previews")
    if not can_add_nurnie:
        box.label(text="Load a folder with PNG icon previews first.", icon='INFO')

    row = box.row()
    row.enabled = can_add_nurnie
    row.operator(operator, text=label)


def _draw_plate_editor(layout, mytool, plate_target, import_plate, base_type):
    if import_plate:
        box = _draw_section_header(layout, "Imported Plate Position", 'ORIENTATION_GLOBAL')
        box.prop(plate_target, 'location', index=2, text='Up / Down')
        box.prop(plate_target, 'location', index=1, text='Back / Forward')
        return

    shape_box = _draw_section_header(layout, "Shape", 'MOD_BUILD')
    row = shape_box.row(align=True)
    row.label(text="Autodraw")
    row.prop(mytool, "autodraw")
    if not mytool.autodraw:
        shape_box.operator("draw.myop_operator", text="Create Plate", icon='GREASEPENCIL')

    row = shape_box.row()
    row.label(text="Engravable Plate")
    row.prop(mytool, "eng_bot")

    if mytool.my_baselist in {"BCIRCLE", "BSPECIAL"}:
        shape_box.label(text="Arc of nameplate", icon='PROP_PROJECTED')
        _draw_enum_button_row(
            shape_box,
            "scene.my_tool.angles",
            mytool.angles,
            (("25", "90"), ("33", "120"), ("41", "150"), ("50", "180")),
        )

    if mytool.my_baselist == "BOVAL":
        if base_type == "L":
            shape_box.label(text="Arc of nameplate", icon='PROP_PROJECTED')
            shape_box.prop(mytool, "o_angles", expand=True)
        else:
            shape_box.label(text="Only comes in 90 degrees")

    shape_box.label(text="End Style", icon='IMAGE_ALPHA')
    _draw_end_style_icon_row(shape_box, "scene.my_tool.my_main_ends", mytool.my_main_ends)
    shape_box.label(text="End Cap Width (mm)", icon='FACE_MAPS')
    _draw_enum_button_row(
        shape_box,
        "scene.my_tool.end_length",
        mytool.end_length,
        (("2", "2"), ("3", "3"), ("4", "4"), ("5", "5"), ("6", "6")),
    )
    shape_box.label(text="Plate Height (mm)", icon='EMPTY_SINGLE_ARROW')
    _draw_enum_button_row(
        shape_box,
        "scene.my_tool.my_user_z",
        mytool.my_user_z,
        (("3", "3"), ("4", "4"), ("5", "5"), ("6", "6")),
    )

    top_box = _draw_section_header(layout, "Top Plate", 'ANCHOR_TOP')
    row = top_box.row()
    row.label(text="Enable Top Plate")
    row.prop(mytool, "add_top")
    if mytool.add_top:
        top_box.label(text="Top Plate Height", icon='EXPORT')
        _draw_enum_button_row(
            top_box,
            "scene.my_tool.my_top_height",
            mytool.my_top_height,
            (("3", "1.5"), ("4", "2"), ("5", "2.5"), ("6", "3")),
        )
        top_box.label(text="Coverage", icon='PROP_PROJECTED')
        _draw_enum_button_row(
            top_box,
            "scene.my_tool.top_angles",
            mytool.top_angles,
            (("25", "1/4"), ("50", "1/2"), ("75", "3/4"), ("100", "Full")),
        )
        label = "Put On Top" if mytool.drop_top_halfway else "Drop Half Way"
        icon = 'ANCHOR_TOP' if mytool.drop_top_halfway else 'ANCHOR_CENTER'
        top_box.prop(mytool, "drop_top_halfway", text=label, icon=icon, toggle=True)
        top_box.label(text="Top End Style", icon='IMAGE_ALPHA')
        _draw_end_style_icon_row(top_box, "scene.my_tool.my_top_ends", mytool.my_top_ends)

    advanced_box = _draw_section_header(layout, "Advanced", 'PREFERENCES')
    row = advanced_box.row()
    row.label(text="Add FOV Cutout", icon='LINCURVE')
    row.prop(mytool, "fov_option")


class OBJECT_PT_NamePlate(Panel):
    bl_label = ""
    bl_idname = "OBJECT_PT_nameplate"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Name Plate"

    def draw_header(self, context):
        self.layout.label(text="Name Plate Maker v1.15.2", icon='WORDWRAP_ON')

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        mytool = scene.my_tool
        wm = context.window_manager

        try:
            base_obj = bpy.context.scene.objects.get(BASE_OBJECT)
            plate_obj = bpy.context.scene.objects.get(PLATE_OBJECT)
            empty_obj = bpy.context.scene.objects.get(EMPTY_OBJECT)
            import_plate = bpy.context.scene.objects.get(IMPORT_PLATE_OBJECT)
            base_type = base_obj.data.name[:1] if base_obj else ""

            if plate_obj:
                target_name = mytool.my_item
                target_obj = _get_target_object(context, target_name)
                _draw_edit_actions(layout, mytool, import_plate)

                if target_name == LEFT_NURNIE_OBJECT and target_obj:
                    _draw_nurnie_editor(layout, target_obj, wm, base_type, "LEFT")
                elif mytool.my_item == LEFT_NURNIE_OBJECT and LEFT_NURNIE_OBJECT not in bpy.context.scene.objects and BASE_OBJECT in bpy.context.scene.objects:
                    _draw_nurnie_add(layout, wm, "LEFT")

                if target_name == RIGHT_NURNIE_OBJECT and target_obj:
                    _draw_nurnie_editor(layout, target_obj, wm, base_type, "RIGHT")
                elif mytool.my_item == RIGHT_NURNIE_OBJECT and RIGHT_NURNIE_OBJECT not in bpy.context.scene.objects and BASE_OBJECT in bpy.context.scene.objects:
                    _draw_nurnie_add(layout, wm, "RIGHT")

                if target_name == UPPER_TEXT_OBJECT and target_obj:
                    _draw_text_editor(layout, target_obj, target_obj.data, mytool, "eng_top_text", "it_top_text", "toptext_options")

                if target_name == MAIN_TEXT_OBJECT and target_obj:
                    _draw_text_editor(layout, target_obj, target_obj.data, mytool, "eng_bot_text", "it_bot_text", "maintext_options")

                plate_target = target_obj if target_name == PLATE_OBJECT and target_obj else None
                if plate_target:
                    _draw_plate_editor(layout, mytool, plate_target, import_plate, base_type)

                return

            if import_plate:
                if not empty_obj:
                    _draw_import_alignment_panel(layout, mytool, base_obj)
                return

            if not empty_obj:
                _draw_setup_panel(layout, mytool, base_obj)
                return

        except Exception as e:
            layout.label(text="UI error. Check the System Console.", icon='ERROR')
            layout.label(text=str(e)[:80])


def register():
    if _sync_edit_target_handler not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(_sync_edit_target_handler)
    bpy.utils.register_class(OBJECT_PT_NamePlate)


def unregister():
    if _sync_edit_target_handler in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(_sync_edit_target_handler)
    bpy.utils.unregister_class(OBJECT_PT_NamePlate)
