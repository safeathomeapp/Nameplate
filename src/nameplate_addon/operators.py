import os

import bpy
from bpy.props import StringProperty
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper

from .constants import (
    BASE_OBJECT,
    EMPTY_OBJECT,
    FOV_OBJECT,
    IMPORT_PLATE_OBJECT,
    LEFT_NUR_DUPLICATE_OBJECT,
    LEFT_NUR_EXPORT_OBJECT,
    LEFT_NUR_OBJECT,
    LEFT_NURNIE_DUPLICATE_OBJECT,
    LEFT_NURNIE_OBJECT,
    MAIN_TEXT_OBJECT,
    MAIN_TEXT_BOOL_OBJECT,
    NAMEPLATE_LEGACY_OBJECTS,
    PATH_OBJECT,
    PLATE_OBJECT,
    PLATE_FOV_BOOLEAN_MODIFIER,
    PLATE_MAIN_TEXT_BOOLEAN_MODIFIER,
    PLATE_UPPER_TEXT_BOOLEAN_MODIFIER,
    REALIZED_RIGHT_NURNIE_OBJECT,
    RIGHT_NUR_DUPLICATE_OBJECT,
    RIGHT_NUR_EXPORT_OBJECT,
    RIGHT_NUR_OBJECT,
    RIGHT_NURNIE_DUPLICATE_OBJECT,
    RIGHT_NURNIE_OBJECT,
    UPPER_TEXT_OBJECT,
    UPPER_TEXT_BOOL_OBJECT,
    pi,
)
from .helpers import (
    NURNIE_CONFIG,
    _get_base_curve_data,
    _deselect_all,
    _ensure_object_mode,
    _safe_remove_object,
    _set_active,
    enum_previews_from_directory_items,
    get_managed_objects,
    get_nurnie_anchor_state,
    preview_collections,
    store_nurnie_anchor_state,
    unhidenurnieleft,
    unhidenurnieright,
)
from .plate import drawPlateTrue


def _get_addon_preferences(context=None):
    context = context or bpy.context
    addon = getattr(getattr(context, "preferences", None), "addons", {}).get(__package__)
    return addon.preferences if addon else None


def _apply_saved_previews_dir_to_window_manager():
    prefs = _get_addon_preferences()
    wm = getattr(bpy.context, "window_manager", None)
    if not prefs or wm is None or not hasattr(wm, "my_previews_dir"):
        return
    saved_dir = getattr(prefs, "saved_previews_dir", "")
    if saved_dir and wm.my_previews_dir != saved_dir:
        wm.my_previews_dir = saved_dir


def _update_saved_previews_dir(self, context):
    prefs = _get_addon_preferences(context)
    if prefs is not None:
        prefs.saved_previews_dir = getattr(self, "my_previews_dir", "")


class NAMEPLATE_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    saved_previews_dir: StringProperty(
        name="Saved STL/Preview Directory",
        subtype='DIR_PATH',
        default="",
    )
    saved_font_dir: StringProperty(
        name="Saved Font Directory",
        subtype='DIR_PATH',
        default="",
    )

    def draw(self, context):
        layout = self.layout
        layout.label(text="Persisted Name Plate directories")
        layout.prop(self, "saved_previews_dir")
        layout.prop(self, "saved_font_dir")


class NAMEPLATE_OT_open_font(Operator, ImportHelper):
    bl_idname = "nameplate.open_font"
    bl_label = "Open Font"
    filename_ext = ".ttf"

    filter_glob: StringProperty(
        default="*.ttf;*.otf;*.ttc;*.otc;*.woff;*.woff2",
        options={'HIDDEN'},
    )

    def invoke(self, context, event):
        prefs = _get_addon_preferences(context)
        saved_font_dir = getattr(prefs, "saved_font_dir", "") if prefs else ""
        if saved_font_dir and os.path.isdir(saved_font_dir):
            self.filepath = os.path.join(saved_font_dir, "select_font.ttf")
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        target_obj = context.object
        if not target_obj or target_obj.type != 'FONT':
            self.report({'ERROR'}, "Select a text object before loading a font")
            return {'CANCELLED'}

        filepath = bpy.path.abspath(self.filepath)
        if not filepath or not os.path.isfile(filepath):
            self.report({'ERROR'}, "Choose a valid font file")
            return {'CANCELLED'}

        try:
            font = bpy.data.fonts.load(filepath, check_existing=True)
        except Exception as exc:
            self.report({'ERROR'}, f"Failed to load font: {exc}")
            return {'CANCELLED'}

        target_obj.data.font = font

        prefs = _get_addon_preferences(context)
        if prefs is not None:
            prefs.saved_font_dir = os.path.dirname(filepath)

        return {'FINISHED'}


def selectBase(self, context):
    return


def _get_nurnie_anchor_location(side, base_type, base_size_x, base_size_y):
    # Suggested add/change anchor placement is base-type-specific.
    # `L` bases must use the oval span data (`o_angles`) rather than the circle curve formula.
    # Square Z placement is intentionally handled differently from curved bases to match legacy output.
    side = str(side).upper()
    user_z = int(bpy.context.scene.my_tool.my_user_z) * .5

    if base_type == "S":
        if side == "LEFT":
            return (2, -base_size_y * .5 - .5, user_z)
        return (base_size_x - 2, -base_size_y * .5 - .5, user_z)

    if base_type == "L":
        oval_choice = int(bpy.context.scene.my_tool.o_angles)
        base_selected = _get_base_curve_data(f"L{base_size_x:03d}", oval_choice)
        if base_selected:
            total_length = base_selected[0]
            center_offset = (base_size_x * pi) * .25
            end_length = float(bpy.context.scene.my_tool.end_length)
            if side == "LEFT":
                anchor_x = center_offset - (total_length * .5) + (end_length * .5)
            else:
                anchor_x = center_offset + (total_length * .5) - (end_length * .5)
            return (anchor_x, -1.5, user_z)

    end_length = float(bpy.context.scene.my_tool.end_length)
    center_offset = (base_size_x * pi) * .25

    circle_curve = int(bpy.context.scene.my_tool.angles) * .01
    if circle_curve == .41:
        circle_curve = .415

    total_length = (base_size_x * pi) * circle_curve

    if side == "LEFT":
        anchor_x = center_offset - (total_length * .5) + (end_length * .5)
    else:
        anchor_x = center_offset + (total_length * .5) - (end_length * .5)

    return (anchor_x, -1.5, user_z)


def _mirror_nurnie_plane_location(side, base_type, base_size_x, base_size_y, anchor_state):
    side = str(side).upper()

    if base_type == "S":
        mirror_axis = base_size_x * .5
    else:
        mirror_axis = (base_size_x * pi) * .25

    source_plane_x = anchor_state["plane_x"]
    target_plane_x = (mirror_axis * 2.0) - source_plane_x

    return (
        target_plane_x,
        anchor_state["plane_y"],
        anchor_state["plane_z"],
    )


def _configure_nurnie_anchor(anchor_name, nur_name, scale_value):
    # Keep this setup aligned with the legacy add/change/mirror order.
    bpy.data.objects[nur_name].parent = bpy.data.objects[anchor_name]
    bpy.ops.object.modifier_add(type='CURVE')
    bpy.context.object.modifiers["Curve"].object = bpy.data.objects.get(PATH_OBJECT)
    bpy.context.object.instance_type = 'FACES'
    bpy.context.object.show_instancer_for_render = False
    bpy.context.object.show_instancer_for_viewport = False
    bpy.context.object.use_instance_faces_scale = True
    bpy.context.object.instance_faces_scale = scale_value
    bpy.context.object.rotation_euler[0] = -0.261799
    store_nurnie_anchor_state(bpy.data.objects[anchor_name])


def _create_nurnie_anchor_plane(anchor_name, anchor_location, apply_location=True):
    bpy.ops.mesh.primitive_plane_add(
        enter_editmode=False,
        align='WORLD',
        location=anchor_location
    )
    bpy.ops.transform.resize(value=(0.1, 0.1, 0.1), orient_type='GLOBAL')
    bpy.ops.object.transform_apply(location=apply_location, rotation=False, scale=True)
    bpy.context.active_object.name = anchor_name


def _import_selected_nurnie(context, nur_name):
    wm = context.window_manager
    import_dir = wm.my_previews_dir
    import_file = bpy.data.window_managers["WinMan"].my_previews[:-4]
    bpy.ops.wm.stl_import(filepath=os.path.join(import_dir, import_file + ".stl"))
    bpy.context.active_object.name = nur_name


def _prepare_nurnie_for_export(side, unhide_fn):
    # Export-prep contract:
    # - duplicate the current instanced side, make it real, remove the temporary .001 pair
    # - keep source anchor/source names intact so later mirror and edit flows do not drift
    # - this helper is for export realization only; it must not change placement logic
    config = NURNIE_CONFIG.get(str(side).upper())
    if not config:
        return

    duplicate_anchor_name = LEFT_NURNIE_DUPLICATE_OBJECT if side == "LEFT" else RIGHT_NURNIE_DUPLICATE_OBJECT
    duplicate_nur_name = LEFT_NUR_DUPLICATE_OBJECT if side == "LEFT" else RIGHT_NUR_DUPLICATE_OBJECT

    anchor_obj = bpy.context.scene.objects.get(config["nurnie"])
    if not anchor_obj:
        return

    _deselect_all()
    _set_active(anchor_obj)
    anchor_obj.select_set(True)

    unhide_fn(None)

    source_obj = bpy.context.scene.objects.get(config["nur"])
    if source_obj:
        _set_active(source_obj)
        source_obj.select_set(True)

    try:
        bpy.ops.object.duplicate()
        bpy.ops.object.duplicates_make_real()
    except Exception:
        pass

    for object_name in (duplicate_anchor_name, duplicate_nur_name):
        if object_name in bpy.data.objects:
            bpy.data.objects.remove(bpy.data.objects[object_name], do_unlink=True)

    if config["nur"] in bpy.data.objects:
        bpy.data.objects[config["nur"]].hide_set(True)


def _cleanup_realized_nurnie_target(realized_name, remove_names):
    # Realized-nurnie cleanup contract:
    # - rename the realized export helper object to its final target name
    # - remove only the replaced source anchor/source pair
    # - do not change mirror placement or export-prep source object behavior
    realized_obj = bpy.context.scene.objects.get(RIGHT_NUR_DUPLICATE_OBJECT)
    if realized_obj:
        _deselect_all()
        _set_active(realized_obj)
        realized_obj.select_set(True)
        bpy.context.active_object.name = realized_name

    for object_name in remove_names:
        if object_name in bpy.context.scene.objects:
            bpy.data.objects.remove(bpy.data.objects[object_name], do_unlink=True)


def _get_base_dimensions():
    base = bpy.data.objects.get(BASE_OBJECT)
    if not base:
        return None
    return (
        base,
        base.data.name[:1],
        int(base.data.name[1:4]),
        int(base.data.name[4:7]),
    )


def _add_or_change_nurnie(context, side, preserve_anchor_state=False):
    _ensure_object_mode()

    base_info = _get_base_dimensions()
    if not base_info:
        return {'CANCELLED'}

    _base, base_type, base_size_x, base_size_y = base_info
    side = str(side).upper()
    config = NURNIE_CONFIG.get(side)
    if not config:
        return {'CANCELLED'}

    scale_value = float(bpy.context.scene.my_tool.my_user_z)
    anchor_state = None

    if preserve_anchor_state:
        anchor = bpy.data.objects.get(config["nurnie"])
        if not anchor:
            return {'CANCELLED'}
        store_nurnie_anchor_state(anchor)
        anchor_state = get_nurnie_anchor_state(anchor)
        scale_value = anchor_state["scale"]
        _safe_remove_object(config["nurnie"])
        _safe_remove_object(config["nur"])

    _import_selected_nurnie(context, config["nur"])

    anchor_location = _get_nurnie_anchor_location(side, base_type, base_size_x, base_size_y)
    _create_nurnie_anchor_plane(config["nurnie"], anchor_location, apply_location=(base_type != "S"))

    if anchor_state:
        bpy.context.object.location[0] = anchor_state["x"]
        bpy.context.object.location[1] = anchor_state["y"]
        bpy.context.object.location[2] = anchor_state["z"]

    _configure_nurnie_anchor(config["nurnie"], config["nur"], scale_value)

    nur_obj = bpy.data.objects.get(config["nur"])
    if nur_obj:
        nur_obj.hide_set(True)

    return {'FINISHED'}


def drawFOV(self, context):
    _ensure_object_mode()

    if bpy.context.scene.my_tool.fov_option:
        _safe_remove_object(FOV_OBJECT)

        base_obj = bpy.data.objects.get(BASE_OBJECT)
        if not base_obj:
            return

        base_size_x = int(base_obj.data.name[1:4])
        user_z = int(bpy.context.scene.my_tool.my_user_z)

        try:
            bpy.ops.view3d.snap_cursor_to_center()
        except Exception:
            bpy.context.scene.cursor.location = (0, 0, 0)

        bpy.ops.mesh.primitive_cube_add(enter_editmode=False, align='WORLD',
                                        location=(-((base_size_x * .5) + 2) * .5, .5, user_z + .02),
                                        scale=((base_size_x * .5) + 2, 1, 1))
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
        bpy.context.object.rotation_euler[2] = 0.785398
        bpy.context.active_object.name = 'FOV1'

        bpy.ops.mesh.primitive_cube_add(enter_editmode=False, align='WORLD',
                                        location=(((base_size_x * .5) + 2) * .5, .5, user_z + .02),
                                        scale=((base_size_x * .5) + 2, 1, 1))
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
        bpy.context.object.rotation_euler[2] = -0.785398
        bpy.context.active_object.name = 'FOV2'

        _deselect_all()
        for o in ("FOV1", "FOV2"):
            obj = bpy.context.scene.objects.get(o)
            if obj:
                obj.select_set(True)
                _set_active(obj)

        try:
            bpy.ops.object.join()
            bpy.context.active_object.name = FOV_OBJECT
        except Exception:
            pass
    else:
        _safe_remove_object(FOV_OBJECT)

    ob = bpy.context.scene.objects.get(PLATE_OBJECT)
    if ob:
        _deselect_all()
        _set_active(ob)
        ob.select_set(True)


def _clear_nameplate_objects():
    managed_names = {obj.name for obj in get_managed_objects()}
    target_names = managed_names.union(NAMEPLATE_LEGACY_OBJECTS)

    for object_name in target_names:
        _safe_remove_object(object_name)


def SetNurnie(self, context):
    _ensure_object_mode()
    _prepare_nurnie_for_export("LEFT", unhidenurnieleft)
    _prepare_nurnie_for_export("RIGHT", unhidenurnieright)


class Import_STL_Custom(Operator):
    bl_idname = "object.import_stl_custom"
    bl_label = "Import STL Custom"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob: bpy.props.StringProperty(default="*.stl;", options={'HIDDEN'})

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        try:
            bpy.ops.wm.stl_import(filepath=self.filepath)
        except Exception:
            bpy.ops.import_mesh.stl(filepath=self.filepath)

        for obj in bpy.context.selected_objects:
            obj.name = IMPORT_PLATE_OBJECT
            if obj.data:
                obj.data.name = IMPORT_PLATE_OBJECT
        return {"FINISHED"}


def ShowMessageBox(message="", title="", icon='INFO'):
    def draw(self, context):
        self.layout.label(text=message)
    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)


def _report_operator_error(message, exc):
    detail = f"{message}: {exc}"
    print(detail)
    ShowMessageBox(detail[:180], "Nameplate Export Warning", 'ERROR')


class Export_STL_Custom(Operator):
    bl_idname = "object.export_stl_custom"
    bl_label = "Export STL Custom"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob: bpy.props.StringProperty(default="*.stl;", options={'HIDDEN'})

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        _ensure_object_mode()
        SetNurnie(self, context)

        plate = bpy.context.scene.objects.get(PLATE_OBJECT)
        if not plate:
            ShowMessageBox("No PLATE object found.", "Export Failed", 'ERROR')
            return {"CANCELLED"}

        _deselect_all()
        _set_active(plate)
        plate.select_set(True)

        if plate.modifiers:
            for mod_name in ("Remesh", "SimpleDeform"):
                if mod_name in plate.modifiers:
                    try:
                        bpy.ops.object.modifier_apply(modifier=mod_name)
                    except Exception as exc:
                        _report_operator_error(f"Failed to apply modifier '{mod_name}'", exc)
                        return {"CANCELLED"}

        if 'FOV' in bpy.context.scene.objects:
            _deselect_all()
            _set_active(plate)
            plate.select_set(True)
            try:
                bpy.ops.object.modifier_add(type='BOOLEAN')
                bpy.context.object.modifiers["Boolean"].operation = 'DIFFERENCE'
                bpy.context.object.modifiers["Boolean"].solver = 'MANIFOLD'
                bpy.context.object.modifiers["Boolean"].object = bpy.data.objects[FOV_OBJECT]
                bpy.ops.object.modifier_apply(modifier="Boolean")
            except Exception as exc:
                _report_operator_error("Failed to apply FOV boolean", exc)
                return {"CANCELLED"}
            _safe_remove_object(FOV_OBJECT)

        select_main = MAIN_TEXT_OBJECT
        if bpy.context.scene.my_tool.eng_bot_text and MAIN_TEXT_OBJECT in bpy.context.scene.objects:
            ob = bpy.context.scene.objects[MAIN_TEXT_OBJECT]
            _deselect_all()
            _set_active(ob)
            ob.select_set(True)
            bpy.ops.object.duplicate(linked=False)
            bpy.ops.object.convert(target='MESH')
            bpy.context.active_object.name = MAIN_TEXT_BOOL_OBJECT

            _deselect_all()
            _set_active(plate)
            plate.select_set(True)
            try:
                bpy.ops.object.modifier_add(type='BOOLEAN')
                bpy.context.object.modifiers["Boolean"].operation = 'DIFFERENCE'
                bpy.context.object.modifiers["Boolean"].solver = 'MANIFOLD'
                bpy.context.object.modifiers["Boolean"].object = bpy.data.objects[MAIN_TEXT_BOOL_OBJECT]
                bpy.ops.object.modifier_apply(modifier="Boolean")
            except Exception as exc:
                _report_operator_error("Failed to apply main text boolean", exc)
                return {"CANCELLED"}
            _safe_remove_object(MAIN_TEXT_BOOL_OBJECT)
            select_main = ""

        select_upper = UPPER_TEXT_OBJECT
        if bpy.context.scene.my_tool.eng_top_text and UPPER_TEXT_OBJECT in bpy.context.scene.objects:
            ob = bpy.context.scene.objects[UPPER_TEXT_OBJECT]
            _deselect_all()
            _set_active(ob)
            ob.select_set(True)
            bpy.ops.object.duplicate(linked=False)
            bpy.ops.object.convert(target='MESH')
            bpy.context.active_object.name = UPPER_TEXT_BOOL_OBJECT

            _deselect_all()
            _set_active(plate)
            plate.select_set(True)
            try:
                bpy.ops.object.modifier_add(type='BOOLEAN')
                bpy.context.object.modifiers["Boolean"].operation = 'DIFFERENCE'
                bpy.context.object.modifiers["Boolean"].solver = 'MANIFOLD'
                bpy.context.object.modifiers["Boolean"].object = bpy.data.objects[UPPER_TEXT_BOOL_OBJECT]
                bpy.ops.object.modifier_apply(modifier="Boolean")
            except Exception as exc:
                _report_operator_error("Failed to apply upper text boolean", exc)
                return {"CANCELLED"}
            _safe_remove_object(UPPER_TEXT_BOOL_OBJECT)
            select_upper = ""

        _deselect_all()
        for o in bpy.data.objects:
            if o.name in (select_upper, select_main, PLATE_OBJECT, RIGHT_NUR_EXPORT_OBJECT, LEFT_NUR_EXPORT_OBJECT):
                o.select_set(True)

        try:
            if self.filepath.lower().endswith('.stl'):
                bpy.ops.wm.stl_export(filepath=self.filepath, export_selected_objects=True, apply_modifiers=True, check_existing=True)
            else:
                bpy.ops.wm.stl_export(filepath=self.filepath + ".stl", export_selected_objects=True, apply_modifiers=True, check_existing=True)
        except Exception as exc:
            print(f"wm.stl_export failed, trying legacy export_mesh.stl fallback: {exc}")
            try:
                if self.filepath.lower().endswith('.stl'):
                    bpy.ops.export_mesh.stl(filepath=self.filepath, use_selection=True, check_existing=True, use_mesh_modifiers=True)
                else:
                    bpy.ops.export_mesh.stl(filepath=self.filepath + ".stl", use_selection=True, check_existing=True, use_mesh_modifiers=True)
            except Exception as fallback_exc:
                _report_operator_error("Both STL export operators failed", fallback_exc)
                return {"CANCELLED"}

        for n in (LEFT_NUR_EXPORT_OBJECT, RIGHT_NUR_EXPORT_OBJECT):
            if n in bpy.context.scene.objects:
                bpy.data.objects.remove(bpy.data.objects[n], do_unlink=True)

        _deselect_all()
        _set_active(plate)
        plate.select_set(True)

        ShowMessageBox("Nameplate Saved", "Saved STL", 'DISK_DRIVE')
        return {"FINISHED"}


class WM_OT_ImportHelpWindow(Operator):
    bl_idname = "wm.importhelp"
    bl_label = "Note regarding imported bases"

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.label(text="------------------------------------------------------------------------------------------")
        layout.label(text="Some imported baseplates (mostly those designed")
        layout.label(text="by other creators) may not automatically align to the")
        layout.label(text="world centre. Please align the imported plate to the")
        layout.label(text="chosen base shape and size in the next step")
        layout.label(text="-----------------")
        layout.label(text="This is a slightly advanced step, and will require ")
        layout.label(text="you to know the basics of Blender to move and rotate")
        layout.label(text="the nameplate and viewport to suit your needs")

    def execute(self, context):
        return {'FINISHED'}


class INCREASETEXTVOXEL_OT_my_op(Operator):
    bl_label = "Increase Text Voxel"
    bl_idname = "increasevoxel.myop_operator"

    def execute(self, context):
        obj = bpy.context.object
        if not obj:
            return {'CANCELLED'}
        mod = obj.modifiers.get("Remesh")
        if not mod:
            return {'CANCELLED'}
        cur_size = mod.voxel_size
        new_size = cur_size - 0.01
        if cur_size > 0.019:
            mod.voxel_size = new_size
        return {'FINISHED'}


class DECREASETEXTVOXEL_OT_my_op(Operator):
    bl_label = "Decrease Text Voxel"
    bl_idname = "decreasevoxel.myop_operator"

    def execute(self, context):
        obj = bpy.context.object
        if not obj:
            return {'CANCELLED'}
        mod = obj.modifiers.get("Remesh")
        if not mod:
            return {'CANCELLED'}
        mod.voxel_size = mod.voxel_size + 0.01
        return {'FINISHED'}


class DRAW_OT_my_op(Operator):
    bl_label = "Draw"
    bl_idname = "draw.myop_operator"

    def execute(self, context):
        drawPlateTrue(self, context)
        return {'FINISHED'}


class CLEARSCENE_OT_my_op(Operator):
    bl_label = "Clear Scene"
    bl_idname = "clear_scene.myop_operator"
    bl_description = "Clear The Scene"

    def execute(self, context):
        _ensure_object_mode()
        if LEFT_NURNIE_OBJECT in bpy.context.scene.objects:
            unhidenurnieleft(self)
        if RIGHT_NURNIE_OBJECT in bpy.context.scene.objects:
            unhidenurnieright(self)
        _clear_nameplate_objects()
        return {'FINISHED'}


class SETNURNIERIGHT_OT_my_op(Operator):
    bl_label = "Set Nurnie"
    bl_idname = "setnurnieright.myop_operator"

    def execute(self, context):
        _ensure_object_mode()
        try:
            bpy.ops.object.duplicates_make_real()
        except Exception:
            pass

        _cleanup_realized_nurnie_target(
            REALIZED_RIGHT_NURNIE_OBJECT,
            (RIGHT_NURNIE_OBJECT, RIGHT_NUR_OBJECT),
        )

        return {'FINISHED'}


class MIRRORNURNIELEFT_OT_my_op(Operator):
    bl_label = "Mirror Nurnie Left"
    bl_idname = "mirrornurnieleft.myop_operator"

    def execute(self, context):
        return _mirror_nurnie('LEFT')


class MIRRORNURNIERIGHT_OT_my_op(Operator):
    bl_label = "Mirror Nurnie Right"
    bl_idname = "mirrornurnieright.myop_operator"

    def execute(self, context):
        return _mirror_nurnie('RIGHT')


class DELETENURNIELEFT_OT_my_op(Operator):
    bl_label = "Delete Nurnie"
    bl_idname = "deletenurnieleft.myop_operator"

    def execute(self, context):
        return _delete_nurnie('LEFT')


class DELETENURNIERIGHT_OT_my_op(Operator):
    bl_label = "Delete Nurnie"
    bl_idname = "deletenurnieright.myop_operator"

    def execute(self, context):
        return _delete_nurnie('RIGHT')


class CHANGENURNIELEFT_OT_my_op(Operator):
    bl_label = "Change Nurnie"
    bl_idname = "changenurnieleft.myop_operator"

    def execute(self, context):
        return _add_or_change_nurnie(context, "LEFT", preserve_anchor_state=True)


class CHANGENURNIERIGHT_OT_my_op(Operator):
    bl_label = "Change Nurnie"
    bl_idname = "changenurnieright.myop_operator"

    def execute(self, context):
        return _add_or_change_nurnie(context, "RIGHT", preserve_anchor_state=True)


class ADDNURNIELEFT_OT_my_op(Operator):
    bl_label = "Import Nurnie Left"
    bl_idname = "addnurnieleft.myop_operator"

    def execute(self, context):
        return _add_or_change_nurnie(context, "LEFT", preserve_anchor_state=False)


class ADDNURNIERIGHT_OT_my_op(Operator):
    bl_label = "Import Nurnie"
    bl_idname = "addnurnieright.myop_operator"

    def execute(self, context):
        return _add_or_change_nurnie(context, "RIGHT", preserve_anchor_state=False)


def _flip_nurnie(side):
    _ensure_object_mode()

    config = NURNIE_CONFIG.get(str(side).upper())
    if not config:
        return {'CANCELLED'}

    config["unhide"](None)

    source_obj = bpy.context.scene.objects.get(config["nur"])
    if not source_obj:
        return {'CANCELLED'}

    _deselect_all()
    _set_active(source_obj)
    source_obj.select_set(True)

    source_obj.rotation_euler[2] = pi
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

    parent_obj = bpy.context.scene.objects.get(config["nurnie"])
    if parent_obj:
        _deselect_all()
        _set_active(parent_obj)
        parent_obj.select_set(True)

    source_data_obj = bpy.data.objects.get(config["nur"])
    if source_data_obj:
        source_data_obj.hide_set(True)

    return {'FINISHED'}


def _delete_nurnie(side):
    config = NURNIE_CONFIG.get(str(side).upper())
    if not config:
        return {'CANCELLED'}

    for object_name in (config["nurnie"], config["nur"]):
        _safe_remove_object(object_name)

        base_obj = bpy.context.scene.objects.get(BASE_OBJECT)
    if base_obj:
        _deselect_all()
        _set_active(base_obj)
        base_obj.select_set(True)

    return {'FINISHED'}


def _mirror_nurnie(side):
    # Mirror contract:
    # - refresh and use the source anchor's stored plane basis plus its current live offset/scale
    # - do not rebuild the target from a fresh suggested endcap position during cleanup/refactors
    # - this preserves mirror behavior after plate resizes followed by manual nurnie repositioning
    _ensure_object_mode()
    base_obj = bpy.data.objects.get(BASE_OBJECT)
    if not base_obj:
        return {'CANCELLED'}

    base_type = base_obj.data.name[:1]
    base_size_x = int(base_obj.data.name[1:4])
    base_size_y = int(base_obj.data.name[4:7])
    side = str(side).upper()

    if side == 'LEFT':
        _safe_remove_object(RIGHT_NURNIE_OBJECT)
        _safe_remove_object(RIGHT_NUR_OBJECT)

        source_anchor = bpy.data.objects.get(LEFT_NURNIE_OBJECT)
        if not source_anchor:
            return {'CANCELLED'}
        store_nurnie_anchor_state(source_anchor)
        anchor_state = get_nurnie_anchor_state(source_anchor)
        nurnie_x = -anchor_state["x"]
        nurnie_y = anchor_state["y"]
        nurnie_z = anchor_state["z"]
        nurnie_s = anchor_state["scale"]

        unhidenurnieleft(None)

        ob = bpy.context.scene.objects.get(LEFT_NUR_OBJECT)
        if not ob:
            return {'CANCELLED'}
        _deselect_all()
        _set_active(ob)
        ob.select_set(True)
        bpy.ops.object.duplicate()
        bpy.ops.object.parent_clear(type='CLEAR')
        bpy.context.active_object.name = RIGHT_NUR_OBJECT

        anchor_location = _mirror_nurnie_plane_location("RIGHT", base_type, base_size_x, base_size_y, anchor_state)
        _create_nurnie_anchor_plane(RIGHT_NURNIE_OBJECT, anchor_location)
        bpy.context.object.location[0] = nurnie_x
        bpy.context.object.location[1] = nurnie_y
        bpy.context.object.location[2] = nurnie_z

        _configure_nurnie_anchor(RIGHT_NURNIE_OBJECT, RIGHT_NUR_OBJECT, nurnie_s)

        bpy.data.objects[LEFT_NUR_OBJECT].hide_set(True)
        bpy.data.objects[RIGHT_NUR_OBJECT].hide_set(True)

        ob = bpy.context.scene.objects.get(LEFT_NURNIE_OBJECT)
        if ob:
            _deselect_all()
            _set_active(ob)
            ob.select_set(True)
        return {'FINISHED'}

    if side == 'RIGHT':
        _safe_remove_object(LEFT_NURNIE_OBJECT)
        _safe_remove_object(LEFT_NUR_OBJECT)

        ob = bpy.context.scene.objects.get(RIGHT_NURNIE_OBJECT)
        if not ob:
            return {'CANCELLED'}
        _deselect_all()
        _set_active(ob)
        ob.select_set(True)

        source_anchor = bpy.data.objects[RIGHT_NURNIE_OBJECT]
        store_nurnie_anchor_state(source_anchor)
        anchor_state = get_nurnie_anchor_state(source_anchor)
        nurnie_x = anchor_state["x"]
        nurnie_y = anchor_state["y"]
        nurnie_z = anchor_state["z"]
        nurnie_s = anchor_state["scale"]

        unhidenurnieright(None)

        ob = bpy.context.scene.objects.get(RIGHT_NUR_OBJECT)
        if not ob:
            return {'CANCELLED'}
        _deselect_all()
        _set_active(ob)
        ob.select_set(True)
        bpy.ops.object.duplicate()
        bpy.ops.object.parent_clear(type='CLEAR')
        bpy.context.active_object.name = LEFT_NUR_OBJECT

        anchor_location = _mirror_nurnie_plane_location("LEFT", base_type, base_size_x, base_size_y, anchor_state)
        _create_nurnie_anchor_plane(LEFT_NURNIE_OBJECT, anchor_location)
        bpy.context.object.location[0] = -nurnie_x
        bpy.context.object.location[1] = nurnie_y
        bpy.context.object.location[2] = nurnie_z

        _configure_nurnie_anchor(LEFT_NURNIE_OBJECT, LEFT_NUR_OBJECT, nurnie_s)

        bpy.data.objects[LEFT_NUR_OBJECT].hide_set(True)
        bpy.data.objects[RIGHT_NUR_OBJECT].hide_set(True)

        ob = bpy.context.scene.objects.get(RIGHT_NURNIE_OBJECT)
        if ob:
            _deselect_all()
            _set_active(ob)
            ob.select_set(True)
        return {'FINISHED'}

    return {'CANCELLED'}


class FLIPNURNIELEFT_OT_my_op(Operator):
    bl_label = "Flip Nurnie Left"
    bl_idname = "flipnurnieleft.myop_operator"

    def execute(self, context):
        return _flip_nurnie("LEFT")


class FLIPNURNIERIGHT_OT_my_op(Operator):
    bl_label = "Flip Nurnie"
    bl_idname = "flipnurnieright.myop_operator"

    def execute(self, context):
        return _flip_nurnie("RIGHT")


class Getready_OT_my_op(Operator):
    bl_label = "Get it Ready"
    bl_idname = "getready.myop_operator"

    def execute(self, context):
        _ensure_object_mode()

        base = bpy.data.objects.get(BASE_OBJECT)
        if not base:
            return {'CANCELLED'}

        base_type = base.data.name[:1]
        base_size_x = int(base.data.name[1:4])
        base_size_y = int(base.data.name[4:7])

        if base_type == "Z":
            bpy.ops.object.empty_add(type='PLAIN_AXES', align='WORLD', location=(0, -base_size_x * .5, 0), scale=(1, 1, 1))
        else:
            bpy.ops.object.empty_add(type='PLAIN_AXES', align='WORLD', location=(0, -base_size_y * .5, 0), scale=(1, 1, 1))
        bpy.context.active_object.name = EMPTY_OBJECT

        if IMPORT_PLATE_OBJECT not in bpy.context.scene.objects:
            drawPlateTrue(self, context)
        else:
            bpy.data.objects[IMPORT_PLATE_OBJECT].name = PLATE_OBJECT
            bpy.ops.object.empty_add(type='PLAIN_AXES', align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
            bpy.context.active_object.name = IMPORT_PLATE_OBJECT

        bpy.ops.object.text_add(enter_editmode=True, align='WORLD', location=(0, -1.1, 0), rotation=(1.309, 0, 0))
        bpy.context.object.data.size = 3
        bpy.context.object.data.extrude = 0.6
        bpy.context.object.data.align_x = 'CENTER'
        bpy.context.object.data.align_y = 'CENTER'
        bpy.context.active_object.name = MAIN_TEXT_OBJECT
        bpy.ops.font.select_all()
        bpy.ops.font.case_set(case='UPPER')
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.object.data.body = ""

        if base_type == "S":
            bpy.context.object.location[1] = -(base_size_x * .5) - 1
            bpy.context.object.data.offset_y = 2.1
        else:
            bpy.context.object.data.offset_x = (base_size_x * pi) * .25
            bpy.ops.object.modifier_add(type='CURVE')
            bpy.context.object.modifiers["Curve"].object = bpy.data.objects.get(PATH_OBJECT)
            bpy.context.object.data.offset_y = 2.1

        bpy.ops.object.modifier_add(type='REMESH')
        bpy.context.object.modifiers["Remesh"].voxel_size = 0.04
        bpy.context.object.modifiers["Remesh"].use_remove_disconnected = False
        bpy.context.object.modifiers["Remesh"].use_smooth_shade = True

        bpy.ops.object.text_add(enter_editmode=True, align='WORLD', location=(0, -1.5, 0), rotation=(1.309, 0, 0))
        bpy.context.object.data.size = 2
        bpy.context.object.data.extrude = 0.6
        bpy.context.object.data.align_x = 'CENTER'
        bpy.context.object.data.align_y = 'CENTER'
        bpy.context.active_object.name = UPPER_TEXT_OBJECT
        bpy.ops.font.select_all()
        bpy.ops.font.case_set(case='UPPER')
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.object.data.body = ""

        if base_type == "S":
            bpy.context.object.location[1] = -(base_size_x * .5) - 1.5
            bpy.context.object.data.offset_y = 5.5
        else:
            bpy.ops.object.modifier_add(type='CURVE')
            bpy.context.object.modifiers["Curve"].object = bpy.data.objects.get(PATH_OBJECT)
            bpy.context.object.data.offset_x = (base_size_x * pi) * .25
            bpy.context.object.data.offset_y = 5.5

        bpy.ops.object.modifier_add(type='REMESH')
        bpy.context.object.modifiers["Remesh"].voxel_size = 0.04
        bpy.context.object.modifiers["Remesh"].use_remove_disconnected = False
        bpy.context.object.modifiers["Remesh"].use_smooth_shade = True

        try:
            bpy.ops.view3d.view_all(center=False)
        except Exception:
            pass

        plate = bpy.context.scene.objects.get(PLATE_OBJECT)
        if plate:
            _deselect_all()
            _set_active(plate)
            plate.select_set(True)

        return {'FINISHED'}


CLASSES = [
    NAMEPLATE_OT_open_font,
    WM_OT_ImportHelpWindow,
    FLIPNURNIELEFT_OT_my_op,
    ADDNURNIELEFT_OT_my_op,
    MIRRORNURNIELEFT_OT_my_op,
    SETNURNIERIGHT_OT_my_op,
    FLIPNURNIERIGHT_OT_my_op,
    ADDNURNIERIGHT_OT_my_op,
    MIRRORNURNIERIGHT_OT_my_op,
    CHANGENURNIERIGHT_OT_my_op,
    CHANGENURNIELEFT_OT_my_op,
    DELETENURNIELEFT_OT_my_op,
    DELETENURNIERIGHT_OT_my_op,
    CLEARSCENE_OT_my_op,
    DRAW_OT_my_op,
    Getready_OT_my_op,
    INCREASETEXTVOXEL_OT_my_op,
    DECREASETEXTVOXEL_OT_my_op,
    Import_STL_Custom,
    Export_STL_Custom,
]


def register():
    from bpy.types import WindowManager
    from bpy.props import EnumProperty

    bpy.utils.register_class(NAMEPLATE_AddonPreferences)

    saved_previews_dir = ""
    prefs = _get_addon_preferences()
    if prefs is not None:
        saved_previews_dir = getattr(prefs, "saved_previews_dir", "")

    WindowManager.my_previews_dir = StringProperty(
        name="",
        subtype='DIR_PATH',
        default=saved_previews_dir,
        update=_update_saved_previews_dir,
    )
    WindowManager.my_previews = EnumProperty(items=enum_previews_from_directory_items)

    try:
        from bpy.utils import previews
        pcoll = previews.new()
        pcoll.my_previews_dir = ""
        pcoll.my_previews = ()
        preview_collections["main"] = pcoll
    except Exception:
        preview_collections.clear()

    for cls in CLASSES:
        bpy.utils.register_class(cls)

    _apply_saved_previews_dir_to_window_manager()


def unregister():
    from bpy.types import WindowManager

    if hasattr(WindowManager, "my_previews"):
        del WindowManager.my_previews
    if hasattr(WindowManager, "my_previews_dir"):
        del WindowManager.my_previews_dir

    try:
        from bpy.utils import previews
        for pcoll in preview_collections.values():
            previews.remove(pcoll)
    except Exception:
        pass
    preview_collections.clear()

    for cls in reversed(CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass

    try:
        bpy.utils.unregister_class(NAMEPLATE_AddonPreferences)
    except Exception:
        pass
