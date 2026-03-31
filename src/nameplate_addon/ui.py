import bpy
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


def _get_target_object(context, target_name):
    return context.scene.objects.get(target_name)


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
        return

    try:
        _sync_edit_target_from_active_object(context, scene.my_tool)
    except Exception:
        pass


def _draw_edit_actions(layout, mytool, import_plate):
    box = layout.box()
    box.label(text="Edit Target", icon='GREASEPENCIL')
    box.prop(mytool, "my_item", expand=True)
    box.label(text="Actions", icon='TOOL_SETTINGS')
    box.operator("object.export_stl_custom", text="Export STL", icon='DISK_DRIVE')
    box.operator("clear_scene.myop_operator", text="Start Over", icon='RECOVER_LAST')
    if not import_plate:
        box.operator("draw.myop_operator", text="Rebuild Plate", icon='FILE_REFRESH')


def _draw_text_editor(layout, obj, text, mytool, engrave_prop, italic_prop, extra_prop_name):
    box = layout.box()
    box.label(text="Text", icon='SMALL_CAPS')
    box.prop(text, 'body', text="")

    box = layout.box()
    box.label(text="Font", icon='FONT_DATA')
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

    box = layout.box()
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

    box = layout.box()
    box.label(text=side_title, icon='MESH_PLANE')
    loc_text = "Left / Right" if base_type == "S" else "Around Curve"
    box.prop(obj, 'location', index=0, text=loc_text)
    box.prop(obj, 'myNurnZFloat', slider=False)
    box.prop(obj, 'myNurnYFloat', slider=False)
    box.prop(obj, "instance_faces_scale", text="Scale", slider=False)
    box.operator(flip_operator, text="Flip Nurnie", icon='MOD_MIRROR')
    box.operator(mirror_operator, text="Mirror To Other Side", icon='UV_SYNC_SELECT')

    box = layout.box()
    box.label(text="Asset", icon='FILE_FOLDER')
    box.prop(wm, "my_previews_dir")
    box.template_icon_view(wm, "my_previews")
    box.operator(change_operator, text="Change Nurnie", icon='FILE_REFRESH')

    box = layout.box()
    box.operator(delete_operator, text="Remove Nurnie", icon='TRASH')


def _draw_nurnie_add(layout, wm, side):
    label = "Add Left Nurnie" if side == "LEFT" else "Add Right Nurnie"
    operator = "addnurnieleft.myop_operator" if side == "LEFT" else "addnurnieright.myop_operator"

    box = layout.box()
    box.label(text=label, icon='MESH_PLANE')
    box.prop(wm, "my_previews_dir")
    box.template_icon_view(wm, "my_previews")
    box.operator(operator, text=label)


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
                    if import_plate:
                        box = layout.box()
                        box.label(text="Plate Position", icon='ORIENTATION_GLOBAL')
                        box.prop(plate_target, 'location', index=2, text='Up / Down')
                        box.prop(plate_target, 'location', index=1, text='Back / Forward')
                    else:
                        row = layout.row()
                        row.label(text="Autodraw")
                        row.prop(mytool, "autodraw")
                        if not mytool.autodraw:
                            layout.operator("draw.myop_operator", text="Create Plate", icon='GREASEPENCIL')

                        box = layout.box()
                        row = box.row()
                        row.prop(mytool, "basic_options")
                        row.label(text="Basic Plate Options")
                        if mytool.basic_options:
                            row = box.row()
                            row.label(text="Engravable Plate")
                            row.prop(mytool, "eng_bot")

                            if mytool.my_baselist in {"BCIRCLE", "BSPECIAL"}:
                                box.label(text="Arc of nameplate", icon='PROP_PROJECTED')
                                box.prop(mytool, "angles", expand=True)

                            if mytool.my_baselist == "BOVAL":
                                if base_type == "L":
                                    box.label(text="Arc of nameplate", icon='PROP_PROJECTED')
                                    box.prop(mytool, "o_angles", expand=True)
                                else:
                                    box.label(text="Only comes in 90 degrees")

                            box.label(text="End Style", icon='IMAGE_ALPHA')
                            box.prop(mytool, "my_main_ends", expand=True)
                            box.label(text="End Cap Width", icon='FACE_MAPS')
                            box.prop(mytool, "end_length", expand=True)
                            box.label(text="Plate Height", icon='EMPTY_SINGLE_ARROW')
                            box.prop(mytool, "my_user_z", expand=True)

                        box = layout.box()
                        row = box.row()
                        row.prop(mytool, "top_options")
                        row.label(text="Top Plate Options")
                        if mytool.top_options:
                            row = box.row()
                            row.label(text="Add top plate")
                            row.prop(mytool, "add_top")
                            box.label(text="Top Plate Height", icon='EXPORT')
                            box.prop(mytool, "my_top_height", expand=True)
                            box.label(text="Coverage", icon='PROP_PROJECTED')
                            box.prop(mytool, "top_angles", expand=True)
                            label = "Put On Top" if mytool.drop_top_halfway else "Drop Half Way"
                            icon = 'ANCHOR_TOP' if mytool.drop_top_halfway else 'ANCHOR_CENTER'
                            box.prop(mytool, "drop_top_halfway", text=label, icon=icon, toggle=True)
                            box.label(text="Top End Style")
                            box.prop(mytool, "my_top_ends", expand=True)

                        box = layout.box()
                        row = box.row()
                        row.prop(mytool, "addit_options")
                        row.label(text="Advanced options")
                        if mytool.addit_options:
                            row = box.row()
                            row.label(text="Add FOV Cutout", icon='LINCURVE')
                            row.prop(mytool, "fov_option")

                return

            if import_plate:
                if not empty_obj:
                    box = layout.box()
                    box.operator("wm.importhelp", text="!!PLEASE READ!!")
                    box.label(text="Choose your base shape", icon='PROP_ON')
                    box.prop(mytool, "my_baselist", expand=True)
                    box.label(text="Choose your base size", icon='PROP_ON')
                    box.prop(mytool, "my_" + mytool.my_baselist, expand=True)
                    if base_obj:
                        box.operator("getready.myop_operator", text="Confirm Base Choice", icon='CHECKBOX_HLT')
                return

            if not empty_obj:
                box = layout.box()
                box.label(text="Get Started")
                box = layout.box()
                box.label(text="Choose a workflow")
                layout.prop(mytool, "my_newbase", expand=True)

                if mytool.my_newbase == "IMPORT":
                    box = layout.box()
                    box.label(text="Import a previously saved plate")
                    box = layout.box()
                    box.operator("object.import_stl_custom", text="Import a Saved Plate", icon='FILE_NEW')

                if mytool.my_newbase == "NEW":
                    box = layout.box()
                    box.label(text="Create a new plate", icon='FILE_NEW')
                    box = layout.box()
                    box.label(text="Choose your base shape", icon='PROP_ON')
                    box.prop(mytool, "my_baselist", expand=True)
                    box.label(text="Choose your base size", icon='PROP_ON')
                    box.prop(mytool, "my_" + mytool.my_baselist, expand=True)
                    if base_obj:
                        box.operator("getready.myop_operator", text="Confirm Base Choice", icon='FILE_NEW')
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
