import os

import bpy
from bpy.types import Operator

from .constants import pi
from .helpers import (
    NURNIE_CONFIG,
    _get_base_curve_data,
    _deselect_all,
    _ensure_object_mode,
    _safe_remove_object,
    _set_active,
    enum_previews_from_directory_items,
    get_nurnie_anchor_state,
    preview_collections,
    store_nurnie_anchor_state,
    unhidenurnieleft,
    unhidenurnieright,
)
from .plate import drawPlateTrue


def selectBase(self, context):
    return


def _get_nurnie_anchor_location(side, base_type, base_size_x, base_size_y):
    side = str(side).upper()
    user_z = int(bpy.context.scene.my_tool.my_user_z) * .5

    if base_type == "S":
        if side == "LEFT":
            return (2, -base_size_y * .5 - .5, -user_z)
        return (base_size_x - 2, -base_size_y * .5 - .5, -user_z)

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


def drawFOV(self, context):
    _ensure_object_mode()

    if bpy.context.scene.my_tool.fov_option:
        _safe_remove_object('FOV')

        base_obj = bpy.data.objects.get("BASE")
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
            bpy.context.active_object.name = 'FOV'
        except Exception:
            pass
    else:
        _safe_remove_object('FOV')

    ob = bpy.context.scene.objects.get("PLATE")
    if ob:
        _deselect_all()
        _set_active(ob)
        ob.select_set(True)


def SetNurnie(self, context):
    _ensure_object_mode()

    if 'NURNIE_LEFT' in bpy.context.scene.objects:
        ob = bpy.context.scene.objects["NURNIE_LEFT"]
        _deselect_all()
        _set_active(ob)
        ob.select_set(True)

        unhidenurnieleft(self)

        ob2 = bpy.context.scene.objects.get("NUR_LEFT")
        if ob2:
            _set_active(ob2)
            ob2.select_set(True)

        try:
            bpy.ops.object.duplicate()
            bpy.ops.object.duplicates_make_real()
        except Exception:
            pass

        for n in ('NURNIE_LEFT.001', 'NUR_LEFT.001'):
            if n in bpy.data.objects:
                bpy.data.objects.remove(bpy.data.objects[n], do_unlink=True)

        if "NUR_LEFT" in bpy.data.objects:
            bpy.data.objects["NUR_LEFT"].hide_set(True)

    if 'NURNIE_RIGHT' in bpy.context.scene.objects:
        ob = bpy.context.scene.objects["NURNIE_RIGHT"]
        _deselect_all()
        _set_active(ob)
        ob.select_set(True)

        unhidenurnieright(self)

        ob2 = bpy.context.scene.objects.get("NUR_RIGHT")
        if ob2:
            _set_active(ob2)
            ob2.select_set(True)

        try:
            bpy.ops.object.duplicate()
            bpy.ops.object.duplicates_make_real()
        except Exception:
            pass

        for n in ('NURNIE_RIGHT.001', 'NUR_RIGHT.001'):
            if n in bpy.data.objects:
                bpy.data.objects.remove(bpy.data.objects[n], do_unlink=True)

        if "NUR_RIGHT" in bpy.data.objects:
            bpy.data.objects["NUR_RIGHT"].hide_set(True)


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
            obj.name = "IMPORTPLATE"
            if obj.data:
                obj.data.name = "IMPORTPLATE"
        return {"FINISHED"}


def ShowMessageBox(message="", title="", icon='INFO'):
    def draw(self, context):
        self.layout.label(text=message)
    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)


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

        plate = bpy.context.scene.objects.get("PLATE")
        if not plate:
            ShowMessageBox("No PLATE object found.", "Export Failed", 'ERROR')
            return {"CANCELLED"}

        _deselect_all()
        _set_active(plate)
        plate.select_set(True)

        if plate.modifiers:
            try:
                dec = plate.modifiers.new(name="Decimate", type='DECIMATE')
                dec.ratio = 0.01
            except Exception:
                pass

            for mod_name in ("Remesh", "SimpleDeform", "Decimate"):
                if mod_name in plate.modifiers:
                    try:
                        bpy.ops.object.modifier_apply(modifier=mod_name)
                    except Exception:
                        pass

        if 'FOV' in bpy.context.scene.objects:
            try:
                boolm = plate.modifiers.new(name="Boolean", type='BOOLEAN')
                boolm.operation = 'DIFFERENCE'
                boolm.solver = 'FAST'
                boolm.object = bpy.data.objects.get("FOV")
                bpy.ops.object.modifier_apply(modifier=boolm.name)
            except Exception:
                pass
            _safe_remove_object('FOV')

        select_main = "MAINTEXT"
        if bpy.context.scene.my_tool.eng_bot_text and 'MAINTEXT' in bpy.context.scene.objects:
            ob = bpy.context.scene.objects["MAINTEXT"]
            _deselect_all()
            _set_active(ob)
            ob.select_set(True)
            bpy.ops.object.duplicate(linked=False)
            bpy.ops.object.convert(target='MESH')
            bpy.context.active_object.name = 'MAINTEXTBOOL'

            _deselect_all()
            _set_active(plate)
            plate.select_set(True)

            try:
                boolm = plate.modifiers.new(name="BooleanTextMain", type='BOOLEAN')
                boolm.operation = 'DIFFERENCE'
                boolm.solver = 'FAST'
                boolm.object = bpy.data.objects.get("MAINTEXTBOOL")
                bpy.ops.object.modifier_apply(modifier=boolm.name)
            except Exception:
                pass
            _safe_remove_object('MAINTEXTBOOL')
            select_main = ""

        select_upper = "UPPERTEXT"
        if bpy.context.scene.my_tool.eng_top_text and 'UPPERTEXT' in bpy.context.scene.objects:
            ob = bpy.context.scene.objects["UPPERTEXT"]
            _deselect_all()
            _set_active(ob)
            ob.select_set(True)
            bpy.ops.object.duplicate(linked=False)
            bpy.ops.object.convert(target='MESH')
            bpy.context.active_object.name = 'UPPERTEXTBOOL'

            _deselect_all()
            _set_active(plate)
            plate.select_set(True)

            try:
                boolm = plate.modifiers.new(name="BooleanTextUpper", type='BOOLEAN')
                boolm.operation = 'DIFFERENCE'
                boolm.solver = 'FAST'
                boolm.object = bpy.data.objects.get("UPPERTEXTBOOL")
                bpy.ops.object.modifier_apply(modifier=boolm.name)
            except Exception:
                pass
            _safe_remove_object('UPPERTEXTBOOL')
            select_upper = ""

        _deselect_all()
        for o in bpy.data.objects:
            if o.name in (select_upper, select_main, "PLATE", "NUR_RIGHT.002", "NUR_LEFT.002"):
                o.select_set(True)

        try:
            if self.filepath.lower().endswith('.stl'):
                bpy.ops.wm.stl_export(filepath=self.filepath, export_selected_objects=True, apply_modifiers=True, check_existing=True)
            else:
                bpy.ops.wm.stl_export(filepath=self.filepath + ".stl", export_selected_objects=True, apply_modifiers=True, check_existing=True)
        except Exception:
            if self.filepath.lower().endswith('.stl'):
                bpy.ops.export_mesh.stl(filepath=self.filepath, use_selection=True, check_existing=True, use_mesh_modifiers=True)
            else:
                bpy.ops.export_mesh.stl(filepath=self.filepath + ".stl", use_selection=True, check_existing=True, use_mesh_modifiers=True)

        for n in ('NUR_LEFT.002', 'NUR_RIGHT.002'):
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
        if 'NURNIE_LEFT' in bpy.context.scene.objects:
            unhidenurnieleft(self)
        if 'NURNIE_RIGHT' in bpy.context.scene.objects:
            unhidenurnieright(self)
        try:
            bpy.ops.object.select_all(action='SELECT')
            bpy.ops.object.delete(use_global=False)
        except Exception:
            pass
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

        ob = bpy.context.scene.objects.get("NUR_RIGHT.001")
        if ob:
            _deselect_all()
            _set_active(ob)
            ob.select_set(True)
            bpy.context.active_object.name = 'RIGHT_NURNIE'

        for n in ('NURNIE_RIGHT', 'NUR_RIGHT'):
            if n in bpy.context.scene.objects:
                bpy.data.objects.remove(bpy.data.objects[n], do_unlink=True)

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
        _ensure_object_mode()
        base = bpy.data.objects.get("BASE")
        if not base:
            return {'CANCELLED'}

        base_type = base.data.name[:1]
        base_size_x = int(base.data.name[1:4])
        base_size_y = int(base.data.name[4:7])

        anchor = bpy.data.objects.get('NURNIE_LEFT')
        if not anchor:
            return {'CANCELLED'}

        anchor_state = get_nurnie_anchor_state(anchor)
        nurnie_x = anchor_state["x"]
        nurnie_y = anchor_state["y"]
        nurnie_z = anchor_state["z"]
        nurnie_s = anchor_state["scale"]

        wm = context.window_manager
        import_dir = wm.my_previews_dir
        import_file = bpy.data.window_managers["WinMan"].my_previews[:-4]

        bpy.ops.wm.stl_import(filepath=os.path.join(import_dir, import_file + ".stl"))

        _safe_remove_object('NURNIE_LEFT')
        _safe_remove_object('NUR_LEFT')
        bpy.context.active_object.name = 'NUR_LEFT'

        anchor_location = _get_nurnie_anchor_location("LEFT", base_type, base_size_x, base_size_y)
        bpy.ops.mesh.primitive_plane_add(
            enter_editmode=False,
            align='WORLD',
            location=anchor_location
        )

        bpy.ops.transform.resize(value=(0.1, 0.1, 0.1), orient_type='GLOBAL')
        bpy.ops.object.transform_apply(location=True, rotation=False, scale=True)
        bpy.context.active_object.name = 'NURNIE_LEFT'
        bpy.context.object.location[0] = nurnie_x
        bpy.context.object.location[1] = nurnie_y
        bpy.context.object.location[2] = nurnie_z

        bpy.data.objects['NUR_LEFT'].parent = bpy.data.objects['NURNIE_LEFT']
        bpy.ops.object.modifier_add(type='CURVE')
        bpy.context.object.modifiers["Curve"].object = bpy.data.objects.get("PATH")
        bpy.context.object.instance_type = 'FACES'

        bpy.context.object.show_instancer_for_render = False
        bpy.context.object.show_instancer_for_viewport = False
        bpy.context.object.use_instance_faces_scale = True
        bpy.context.object.instance_faces_scale = nurnie_s
        bpy.context.object.rotation_euler[0] = -0.261799
        store_nurnie_anchor_state(bpy.data.objects['NURNIE_LEFT'])

        if "NUR_LEFT" in bpy.data.objects:
            bpy.data.objects["NUR_LEFT"].hide_set(True)

        return {'FINISHED'}


class CHANGENURNIERIGHT_OT_my_op(Operator):
    bl_label = "Change Nurnie"
    bl_idname = "changenurnieright.myop_operator"

    def execute(self, context):
        _ensure_object_mode()
        base = bpy.data.objects.get("BASE")
        if not base:
            return {'CANCELLED'}

        base_type = base.data.name[:1]
        base_size_x = int(base.data.name[1:4])
        base_size_y = int(base.data.name[4:7])

        anchor = bpy.data.objects.get('NURNIE_RIGHT')
        if not anchor:
            return {'CANCELLED'}

        anchor_state = get_nurnie_anchor_state(anchor)
        nurnie_x = anchor_state["x"]
        nurnie_y = anchor_state["y"]
        nurnie_z = anchor_state["z"]
        nurnie_s = anchor_state["scale"]

        wm = context.window_manager
        import_dir = wm.my_previews_dir
        import_file = bpy.data.window_managers["WinMan"].my_previews[:-4]

        bpy.ops.wm.stl_import(filepath=os.path.join(import_dir, import_file + ".stl"))

        _safe_remove_object('NURNIE_RIGHT')
        _safe_remove_object('NUR_RIGHT')
        bpy.context.active_object.name = 'NUR_RIGHT'

        anchor_location = _get_nurnie_anchor_location("RIGHT", base_type, base_size_x, base_size_y)
        bpy.ops.mesh.primitive_plane_add(
            enter_editmode=False,
            align='WORLD',
            location=anchor_location
        )

        bpy.ops.transform.resize(value=(0.1, 0.1, 0.1), orient_type='GLOBAL')
        bpy.ops.object.transform_apply(location=True, rotation=False, scale=True)
        bpy.context.active_object.name = 'NURNIE_RIGHT'
        bpy.context.object.location[0] = nurnie_x
        bpy.context.object.location[1] = nurnie_y
        bpy.context.object.location[2] = nurnie_z

        bpy.data.objects['NUR_RIGHT'].parent = bpy.data.objects['NURNIE_RIGHT']
        bpy.ops.object.modifier_add(type='CURVE')
        bpy.context.object.modifiers["Curve"].object = bpy.data.objects.get("PATH")
        bpy.context.object.instance_type = 'FACES'

        bpy.context.object.show_instancer_for_render = False
        bpy.context.object.show_instancer_for_viewport = False
        bpy.context.object.use_instance_faces_scale = True
        bpy.context.object.instance_faces_scale = nurnie_s
        bpy.context.object.rotation_euler[0] = -0.261799
        store_nurnie_anchor_state(bpy.data.objects['NURNIE_RIGHT'])

        if "NUR_RIGHT" in bpy.data.objects:
            bpy.data.objects["NUR_RIGHT"].hide_set(True)

        return {'FINISHED'}


class ADDNURNIELEFT_OT_my_op(Operator):
    bl_label = "Import Nurnie Left"
    bl_idname = "addnurnieleft.myop_operator"

    def execute(self, context):
        _ensure_object_mode()
        base = bpy.data.objects.get("BASE")
        if not base:
            return {'CANCELLED'}

        base_type = base.data.name[:1]
        base_size_x = int(base.data.name[1:4])
        base_size_y = int(base.data.name[4:7])

        wm = context.window_manager
        import_dir = wm.my_previews_dir
        import_file = bpy.data.window_managers["WinMan"].my_previews[:-4]

        bpy.ops.wm.stl_import(filepath=os.path.join(import_dir, import_file + ".stl"))
        bpy.context.active_object.name = 'NUR_LEFT'

        anchor_location = _get_nurnie_anchor_location("LEFT", base_type, base_size_x, base_size_y)
        bpy.ops.mesh.primitive_plane_add(
            enter_editmode=False,
            align='WORLD',
            location=anchor_location
        )

        bpy.ops.transform.resize(value=(0.1, 0.1, 0.1), orient_type='GLOBAL')
        bpy.ops.object.transform_apply(location=True, rotation=False, scale=True)
        bpy.context.active_object.name = 'NURNIE_LEFT'

        bpy.data.objects['NUR_LEFT'].parent = bpy.data.objects['NURNIE_LEFT']
        bpy.ops.object.modifier_add(type='CURVE')
        bpy.context.object.modifiers["Curve"].object = bpy.data.objects.get("PATH")
        bpy.context.object.instance_type = 'FACES'

        bpy.context.object.show_instancer_for_render = False
        bpy.context.object.show_instancer_for_viewport = False
        bpy.context.object.use_instance_faces_scale = True
        bpy.context.object.instance_faces_scale = float(bpy.context.scene.my_tool.my_user_z)
        bpy.context.object.rotation_euler[0] = -0.261799
        store_nurnie_anchor_state(bpy.data.objects['NURNIE_LEFT'])

        if "NUR_LEFT" in bpy.data.objects:
            bpy.data.objects["NUR_LEFT"].hide_set(True)

        return {'FINISHED'}


class ADDNURNIERIGHT_OT_my_op(Operator):
    bl_label = "Import Nurnie"
    bl_idname = "addnurnieright.myop_operator"

    def execute(self, context):
        _ensure_object_mode()
        base = bpy.data.objects.get("BASE")
        if not base:
            return {'CANCELLED'}

        base_type = base.data.name[:1]
        base_size_x = int(base.data.name[1:4])
        base_size_y = int(base.data.name[4:7])

        wm = context.window_manager
        import_dir = wm.my_previews_dir
        import_file = bpy.data.window_managers["WinMan"].my_previews[:-4]

        bpy.ops.wm.stl_import(filepath=os.path.join(import_dir, import_file + ".stl"))
        bpy.context.active_object.name = 'NUR_RIGHT'

        anchor_location = _get_nurnie_anchor_location("RIGHT", base_type, base_size_x, base_size_y)
        bpy.ops.mesh.primitive_plane_add(
            enter_editmode=False,
            align='WORLD',
            location=anchor_location
        )

        bpy.ops.transform.resize(value=(0.1, 0.1, 0.1), orient_type='GLOBAL')
        bpy.ops.object.transform_apply(location=True, rotation=False, scale=True)
        bpy.context.active_object.name = 'NURNIE_RIGHT'

        bpy.data.objects['NUR_RIGHT'].parent = bpy.data.objects['NURNIE_RIGHT']
        bpy.ops.object.modifier_add(type='CURVE')
        bpy.context.object.modifiers["Curve"].object = bpy.data.objects.get("PATH")
        bpy.context.object.instance_type = 'FACES'

        bpy.context.object.show_instancer_for_render = False
        bpy.context.object.show_instancer_for_viewport = False
        bpy.context.object.use_instance_faces_scale = True
        bpy.context.object.instance_faces_scale = float(bpy.context.scene.my_tool.my_user_z)
        bpy.context.object.rotation_euler[0] = -0.261799
        store_nurnie_anchor_state(bpy.data.objects['NURNIE_RIGHT'])

        if "NUR_RIGHT" in bpy.data.objects:
            bpy.data.objects["NUR_RIGHT"].hide_set(True)

        return {'FINISHED'}


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

    base_obj = bpy.context.scene.objects.get("BASE")
    if base_obj:
        _deselect_all()
        _set_active(base_obj)
        base_obj.select_set(True)

    return {'FINISHED'}


def _mirror_nurnie(side):
    _ensure_object_mode()
    base_obj = bpy.data.objects.get("BASE")
    if not base_obj:
        return {'CANCELLED'}

    base_type = base_obj.data.name[:1]
    base_size_x = int(base_obj.data.name[1:4])
    base_size_y = int(base_obj.data.name[4:7])
    side = str(side).upper()

    if side == 'LEFT':
        _safe_remove_object('NURNIE_RIGHT')
        _safe_remove_object('NUR_RIGHT')

        source_anchor = bpy.data.objects.get('NURNIE_LEFT')
        if not source_anchor:
            return {'CANCELLED'}
        store_nurnie_anchor_state(source_anchor)
        anchor_state = get_nurnie_anchor_state(source_anchor)
        nurnie_x = -anchor_state["x"]
        nurnie_y = anchor_state["y"]
        nurnie_z = anchor_state["z"]
        nurnie_s = anchor_state["scale"]

        unhidenurnieleft(None)

        ob = bpy.context.scene.objects.get("NUR_LEFT")
        if not ob:
            return {'CANCELLED'}
        _deselect_all()
        _set_active(ob)
        ob.select_set(True)
        bpy.ops.object.duplicate()
        bpy.ops.object.parent_clear(type='CLEAR')
        bpy.context.active_object.name = 'NUR_RIGHT'

        anchor_location = _mirror_nurnie_plane_location("RIGHT", base_type, base_size_x, base_size_y, anchor_state)
        bpy.ops.mesh.primitive_plane_add(
            enter_editmode=False,
            align='WORLD',
            location=anchor_location
        )
        bpy.ops.transform.resize(value=(0.1, 0.1, 0.1), orient_type='GLOBAL')
        bpy.ops.object.transform_apply(location=True, rotation=False, scale=True)
        bpy.context.active_object.name = 'NURNIE_RIGHT'
        bpy.context.object.location[0] = nurnie_x
        bpy.context.object.location[1] = nurnie_y
        bpy.context.object.location[2] = nurnie_z

        bpy.data.objects['NUR_RIGHT'].parent = bpy.data.objects['NURNIE_RIGHT']
        bpy.ops.object.modifier_add(type='CURVE')
        bpy.context.object.modifiers["Curve"].object = bpy.data.objects["PATH"]
        bpy.context.object.instance_type = 'FACES'
        bpy.context.object.show_instancer_for_render = False
        bpy.context.object.show_instancer_for_viewport = False
        bpy.context.object.use_instance_faces_scale = True
        bpy.context.object.instance_faces_scale = nurnie_s
        bpy.context.object.rotation_euler[0] = -0.261799
        store_nurnie_anchor_state(bpy.data.objects['NURNIE_RIGHT'])

        bpy.data.objects["NUR_LEFT"].hide_set(True)
        bpy.data.objects["NUR_RIGHT"].hide_set(True)

        ob = bpy.context.scene.objects.get("NURNIE_LEFT")
        if ob:
            _deselect_all()
            _set_active(ob)
            ob.select_set(True)
        return {'FINISHED'}

    if side == 'RIGHT':
        _safe_remove_object('NURNIE_LEFT')
        _safe_remove_object('NUR_LEFT')

        ob = bpy.context.scene.objects.get("NURNIE_RIGHT")
        if not ob:
            return {'CANCELLED'}
        _deselect_all()
        _set_active(ob)
        ob.select_set(True)

        source_anchor = bpy.data.objects['NURNIE_RIGHT']
        store_nurnie_anchor_state(source_anchor)
        anchor_state = get_nurnie_anchor_state(source_anchor)
        nurnie_x = anchor_state["x"]
        nurnie_y = anchor_state["y"]
        nurnie_z = anchor_state["z"]
        nurnie_s = anchor_state["scale"]

        unhidenurnieright(None)

        ob = bpy.context.scene.objects.get("NUR_RIGHT")
        if not ob:
            return {'CANCELLED'}
        _deselect_all()
        _set_active(ob)
        ob.select_set(True)
        bpy.ops.object.duplicate()
        bpy.ops.object.parent_clear(type='CLEAR')
        bpy.context.active_object.name = 'NUR_LEFT'

        anchor_location = _mirror_nurnie_plane_location("LEFT", base_type, base_size_x, base_size_y, anchor_state)
        bpy.ops.mesh.primitive_plane_add(
            enter_editmode=False,
            align='WORLD',
            location=anchor_location
        )
        bpy.ops.transform.resize(value=(0.1, 0.1, 0.1), orient_type='GLOBAL')
        bpy.ops.object.transform_apply(location=True, rotation=False, scale=True)
        bpy.context.active_object.name = 'NURNIE_LEFT'
        bpy.context.object.location[0] = -nurnie_x
        bpy.context.object.location[1] = nurnie_y
        bpy.context.object.location[2] = nurnie_z

        bpy.data.objects['NUR_LEFT'].parent = bpy.data.objects['NURNIE_LEFT']
        bpy.ops.object.modifier_add(type='CURVE')
        bpy.context.object.modifiers["Curve"].object = bpy.data.objects["PATH"]
        bpy.context.object.instance_type = 'FACES'
        bpy.context.object.show_instancer_for_render = False
        bpy.context.object.show_instancer_for_viewport = False
        bpy.context.object.use_instance_faces_scale = True
        bpy.context.object.instance_faces_scale = nurnie_s
        bpy.context.object.rotation_euler[0] = -0.261799
        store_nurnie_anchor_state(bpy.data.objects['NURNIE_LEFT'])

        bpy.data.objects["NUR_LEFT"].hide_set(True)
        bpy.data.objects["NUR_RIGHT"].hide_set(True)

        ob = bpy.context.scene.objects.get("NURNIE_RIGHT")
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

        for nm in ('Cube', 'Camera', 'Light'):
            if nm in bpy.context.scene.objects:
                _deselect_all()
                bpy.data.objects[nm].select_set(True)
                try:
                    bpy.ops.object.delete()
                except Exception:
                    pass

        base = bpy.data.objects.get("BASE")
        if not base:
            return {'CANCELLED'}

        base_type = base.data.name[:1]
        base_size_x = int(base.data.name[1:4])
        base_size_y = int(base.data.name[4:7])

        if base_type == "Z":
            bpy.ops.object.empty_add(type='PLAIN_AXES', align='WORLD', location=(0, -base_size_x * .5, 0), scale=(1, 1, 1))
        else:
            bpy.ops.object.empty_add(type='PLAIN_AXES', align='WORLD', location=(0, -base_size_y * .5, 0), scale=(1, 1, 1))
        bpy.context.active_object.name = 'EMPTY'

        if 'IMPORTPLATE' not in bpy.context.scene.objects:
            drawPlateTrue(self, context)
        else:
            bpy.data.objects['IMPORTPLATE'].name = 'PLATE'
            bpy.ops.object.empty_add(type='PLAIN_AXES', align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
            bpy.context.active_object.name = 'IMPORTPLATE'

        bpy.ops.object.text_add(enter_editmode=True, align='WORLD', location=(0, -1.1, 0), rotation=(1.309, 0, 0))
        bpy.context.object.data.size = 3
        bpy.context.object.data.extrude = 0.6
        bpy.context.object.data.align_x = 'CENTER'
        bpy.context.object.data.align_y = 'CENTER'
        bpy.context.active_object.name = 'MAINTEXT'
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
            bpy.context.object.modifiers["Curve"].object = bpy.data.objects.get("PATH")
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
        bpy.context.active_object.name = 'UPPERTEXT'
        bpy.ops.font.select_all()
        bpy.ops.font.case_set(case='UPPER')
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.object.data.body = ""

        if base_type == "S":
            bpy.context.object.location[1] = -(base_size_x * .5) - 1.5
            bpy.context.object.data.offset_y = 5.5
        else:
            bpy.ops.object.modifier_add(type='CURVE')
            bpy.context.object.modifiers["Curve"].object = bpy.data.objects.get("PATH")
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

        plate = bpy.context.scene.objects.get("PLATE")
        if plate:
            _deselect_all()
            _set_active(plate)
            plate.select_set(True)

        return {'FINISHED'}


CLASSES = [
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
    from bpy.props import EnumProperty, StringProperty

    WindowManager.my_previews_dir = StringProperty(name="", subtype='DIR_PATH', default="")
    WindowManager.my_previews = EnumProperty(items=enum_previews_from_directory_items)

    try:
        import bpy.utils.previews
        pcoll = bpy.utils.previews.new()
        pcoll.my_previews_dir = ""
        pcoll.my_previews = ()
        preview_collections["main"] = pcoll
    except Exception:
        preview_collections.clear()

    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    from bpy.types import WindowManager

    if hasattr(WindowManager, "my_previews"):
        del WindowManager.my_previews
    if hasattr(WindowManager, "my_previews_dir"):
        del WindowManager.my_previews_dir

    try:
        import bpy.utils.previews
        for pcoll in preview_collections.values():
            bpy.utils.previews.remove(pcoll)
    except Exception:
        pass
    preview_collections.clear()

    for cls in reversed(CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass
