import bpy

from .constants import BASE_OBJECT, EMPTY_OBJECT, PLATE_OBJECT, pi
from .helpers import (
    _bevel_end_cap_profile,
    _bevel_top_plate_profile,
    _deselect_all,
    _ensure_object_mode,
    _safe_remove_object,
    _set_active,
    delete_managed_objects,
)


def drawPlate(self, context):
    if bpy.context.scene.my_tool.autodraw:
        drawPlateTrue(self, context)


def drawPlateTrue(self, context):
    # Legacy geometry contract:
    # - keep object names, selection flow, join order, and modifier order aligned with legacy behavior
    # - base-type math here drives the produced plate shape and must not be "simplified" casually
    # - selection-sensitive bpy.ops calls are part of the algorithm, not incidental cleanup targets
    _ensure_object_mode()

    def halfscale(x, y, z):
        return (x * 0.5, y * 0.5, z * 0.5)

    L060 = ((30.3, 34.4), (44.1, 54.7), (51.7, 67))
    L075 = ((36.9, 33), (54, 51), (63.3, 63.3))
    L090 = ((45.5, 34.8), (65.8, 53.7), (77.4, 66.3))
    L105 = ((59.4, 46.3), (83.8, 67.9), (96.8, 81.3))
    L120 = ((76.1, 58.1), (105, 83.5), (120, 98.2))
    L150 = ((81.9, 41.7), (116, 62.6), (135, 76.1))
    L170 = ((87.5, 40.5), (125, 60.3), (145, 73.1))

    if BASE_OBJECT not in bpy.data.objects:
        return

    base_obj = bpy.data.objects[BASE_OBJECT]
    base_type = base_obj.data.name[:1]
    base_size_x = int(base_obj.data.name[1:4])
    base_string_x = base_obj.data.name[1:4]
    base_size_y = int(base_obj.data.name[4:7])

    end_length = int(bpy.context.scene.my_tool.end_length)
    circle_curve = int(bpy.context.scene.my_tool.angles) * 0.01
    if circle_curve == 0.41:
        circle_curve = 0.415

    oval_choice = int(bpy.context.scene.my_tool.o_angles)
    my_main_ends = bpy.context.scene.my_tool.my_main_ends
    user_z = int(bpy.context.scene.my_tool.my_user_z)
    top_height = int(bpy.context.scene.my_tool.my_top_height) * 0.5
    top_panel_curve = int(bpy.context.scene.my_tool.top_angles) * 0.01
    user_y = 1.0
    border_thickness = 0.5
    border_depth = 0.5

    drop_top_halfway = bool(getattr(bpy.context.scene.my_tool, 'drop_top_halfway', False))
    top_position = (user_z - (border_thickness * 0.5)) if drop_top_halfway else (user_z + (top_height * 0.5))

    if base_type == "C":
        radius = base_size_x * 0.5
        circumference = 2.0 * pi * radius
        arc_length = circumference * circle_curve
        user_x = arc_length - (end_length * 2.0)
        curve_x = arc_length / radius

    elif base_type == "O":
        base_selected = eval(base_type + base_string_x)
        user_x = base_selected[0] - (end_length * 2.0)
        curve_x = base_selected[1] * pi / 180.0

    elif base_type == "L":
        base_selected = eval(base_type + base_string_x)
        user_x = base_selected[oval_choice][0] - (end_length * 2.0)
        curve_x = base_selected[oval_choice][1] * pi / 180.0

    elif base_type == "S":
        user_x = base_size_y - (end_length * 2.0)
        curve_x = 0.0

    elif base_type == "Z":
        base_size_y = base_size_x
        radius = base_size_x * 0.5
        arc_length = (2.0 * pi * radius) * circle_curve
        user_x = arc_length - (end_length * 2.0)
        curve_x = arc_length / radius

    else:
        return

    delete_managed_objects()

    loc_y = -base_size_y * 0.5

    if bpy.context.scene.my_tool.eng_bot:
        bpy.ops.mesh.primitive_cube_add(align='WORLD', location=(0, loc_y - 0.25, user_z * 0.5),
                                        scale=halfscale(user_x, 1.5, user_z))
    else:
        bpy.ops.mesh.primitive_cube_add(align='WORLD', location=(0, loc_y, user_z * 0.5),
                                        scale=halfscale(user_x, user_y, user_z))
    base_piece = bpy.context.active_object
    base_piece.name = 'NameplateBase'
    base_piece["nameplate_managed"] = True
    base_piece["nameplate_role"] = "NameplateBase"

    bpy.ops.mesh.primitive_cube_add(
        align='WORLD',
        location=(0, loc_y - (user_y - border_thickness * 0.5), user_z - (border_thickness * 0.5)),
        scale=halfscale(user_x, border_depth, border_thickness)
    )
    top_border = bpy.context.active_object
    top_border.name = 'NameplateTop'
    top_border["nameplate_managed"] = True
    top_border["nameplate_role"] = "NameplateTop"

    bpy.ops.mesh.primitive_cube_add(
        align='WORLD',
        location=(0, loc_y - (user_y - border_thickness * 0.5), border_thickness * 0.5),
        scale=halfscale(user_x, border_depth, border_thickness)
    )
    bottom_border = bpy.context.active_object
    bottom_border.name = 'NameplateBottom'
    bottom_border["nameplate_managed"] = True
    bottom_border["nameplate_role"] = "NameplateBottom"

    if bpy.context.scene.my_tool.add_top:
        _safe_remove_object('TopBit')

        bpy.ops.mesh.primitive_cube_add(
            align='WORLD',
            location=(0, loc_y - border_thickness * 0.5, top_position),
            scale=halfscale(user_x * top_panel_curve, user_y + border_thickness, top_height)
        )
        c = bpy.context.active_object
        c.name = 'TopBit'
        c["nameplate_managed"] = True
        c["nameplate_role"] = "TopBit"

        try:
            _bevel_top_plate_profile(c, bpy.context.scene.my_tool.my_top_ends, bpy.context.scene.my_tool.drop_top_halfway)
        except Exception:
            _ensure_object_mode()
    else:
        _safe_remove_object('TopBit')

    ends_def = (
        (-1.0, 'END_LEFT'),
        (1.0, 'END_RIGHT'),
    )
    for sign, name in ends_def:
        _safe_remove_object(name)

        loc = (
            sign * ((user_x * 0.5) + (end_length * 0.5)),
            -((base_size_y + border_thickness) * 0.5),
            user_z * 0.5
        )

        bpy.ops.mesh.primitive_cube_add(
            align='WORLD',
            location=loc,
            scale=halfscale(end_length, (user_y + border_thickness), user_z)
        )
        c = bpy.context.active_object

        _bevel_end_cap_profile(c, sign, my_main_ends)

        c.name = name
        c["nameplate_managed"] = True
        c["nameplate_role"] = name

    bpy.context.scene.cursor.location = (0, -base_size_y * 0.5, 0)

    _deselect_all()
    join_order = ("NameplateBottom", "NameplateTop", "END_LEFT", "END_RIGHT", "TopBit", "NameplateBase")
    for nm in join_order:
        obj = bpy.context.scene.objects.get(nm)
        if obj:
            obj.select_set(True)
            _set_active(obj)

    try:
        bpy.ops.object.join()
    except Exception:
        return

    plate = bpy.context.active_object
    if not plate:
        return
    plate.name = PLATE_OBJECT
    plate["nameplate_managed"] = True
    plate["nameplate_role"] = PLATE_OBJECT

    plate.rotation_euler[0] = -0.261799
    plate.rotation_euler[1] = 0.0
    plate.rotation_euler[2] = 0.0

    plate.location[2] = -0.15
    try:
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
    except Exception:
        pass

    try:
        rem = plate.modifiers.new(name="Remesh", type='REMESH')
        rem.voxel_size = 0.05
    except Exception:
        pass

    try:
        simp = plate.modifiers.new(name="SimpleDeform", type='SIMPLE_DEFORM')
        simp.deform_method = 'BEND'
        simp.deform_axis = 'Z'
        simp.origin = bpy.data.objects.get(EMPTY_OBJECT)
        simp.angle = curve_x
    except Exception:
        pass

    plate.location[2] = user_z * 0.5 + 0.2
