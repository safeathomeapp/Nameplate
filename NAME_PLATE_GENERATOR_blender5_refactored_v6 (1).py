# ~~~~~~~~~ BEGIN LICENSE BLOCK ~~~~~~~~~
#
#  Attribution-NonCommercial-NoDerivatives 4.0 International (CC BY-NC-ND 4.0)
#
#  This work is licensed under the Creative Commons
#  Attribution-NonCommercial-NoDerivatives 4.0 International License.
#
#  To view a copy of this license,
#  visit http://creativecommons.org/licenses/by-nc-nd/4.0/.
#
#  Email : kevthomas2712@gmail.com
#
#  Interested in entering in to partnerships or collaborations, just email
#
# ~~~~~~~~~ END LICENSE BLOCK ~~~~~~~~~

bl_info = {
    "name": "NamePlate Generator",
    "author": "Kev Thomas",
    "version": (1, 15, 2),
    "blender": (4, 0, 0),  # Target: Blender 4+ (works in Blender 5.x)
    "location": "View3D > Sidebar > Name Plate",
    "description": "Adds a new NamePlate Object with user defined properties",
    "warning": "",
    "wiki_url": "",
    "category": "User Interface",
}

import bpy
import bmesh
import os
from mathutils import Vector
from bpy.types import Panel, Operator, PropertyGroup
from bpy.props import FloatProperty

# -------------------------------------------------------------------
# Constants / small utilities
# -------------------------------------------------------------------

PI = 3.141592653589793

preview_collections = {}

BASE_CURVE_DATA = {
    "L060": ((30.3, 34.4), (44.1, 54.7), (51.7, 67.0)),
    "L075": ((36.9, 33.0), (54.0, 51.0), (63.3, 63.3)),
    "L090": ((45.5, 34.8), (65.8, 53.7), (77.4, 66.3)),
    "L105": ((59.4, 46.3), (83.8, 67.9), (96.8, 81.3)),
    "L120": ((76.1, 58.1), (105.0, 83.5), (120.0, 98.2)),
    "L150": ((81.9, 41.7), (116.0, 62.6), (135.0, 76.1)),
    "L170": ((87.5, 40.5), (125.0, 60.3), (145.0, 73.1)),
}

STYLE_BEVEL_SETTINGS = {
    "BEVEL": {"offset": 1.85688, "segments": 10, "profile": 0.5},
    "CHAMFER": {"offset": 1.0, "segments": 10, "profile": 0.1},
    "SLANT": {"offset": 1.1, "segments": 1, "profile": 0.5},
}

def _deselect_all():
    try:
        bpy.ops.object.select_all(action='DESELECT')
    except Exception:
        # If not in OBJECT mode, force it.
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
        except Exception:
            pass

def _set_active(obj):
    if obj is None:
        return
    try:
        bpy.context.view_layer.objects.active = obj
    except Exception:
        pass

def _safe_remove_object(name: str):
    obj = bpy.context.scene.objects.get(name)
    if obj:
        try:
            bpy.data.objects.remove(obj, do_unlink=True)
        except Exception:
            pass

def _get_view3d_area():
    # Safest way to set viewport shading options without assuming context.space_data
    for area in getattr(bpy.context, "screen", None).areas if bpy.context.screen else []:
        if area.type == 'VIEW_3D':
            return area
    return None

def _set_random_viewport_color():
    area = _get_view3d_area()
    if not area:
        return
    for space in area.spaces:
        if space.type == 'VIEW_3D':
            try:
                space.shading.color_type = 'RANDOM'
            except Exception:
                pass

def _ensure_object_mode():
    try:
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
    except Exception:
        pass


def _halfscale(x, y, z):
    return (x * 0.5, y * 0.5, z * 0.5)

def _get_style_bevel_settings(style):
    return STYLE_BEVEL_SETTINGS.get(style)

def _bevel_mesh_edges_by_index(obj, edge_indices, style):
    settings = _get_style_bevel_settings(style)
    if not obj or obj.type != 'MESH' or not settings:
        return False

    mesh = obj.data
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        bm.edges.ensure_lookup_table()

        edges = []
        for edge_index in edge_indices:
            if 0 <= edge_index < len(bm.edges):
                edges.append(bm.edges[edge_index])

        if not edges:
            return False

        bmesh.ops.bevel(
            bm,
            geom=edges,
            affect='EDGES',
            offset=settings["offset"],
            offset_type='OFFSET',
            segments=settings["segments"],
            profile=settings["profile"],
            clamp_overlap=True,
        )
        bm.to_mesh(mesh)
        mesh.update()
        return True
    finally:
        bm.free()

def _get_base_curve_data(base_key, oval_choice):
    base_selected = BASE_CURVE_DATA.get(base_key)
    if base_selected is None:
        return None
    try:
        return base_selected[int(oval_choice)]
    except (IndexError, TypeError, ValueError):
        return None

def _find_outer_face_by_x(bm, sign):
    if not bm.faces:
        return None

    def _face_center_x(face):
        return sum(v.co.x for v in face.verts) / len(face.verts)

    return max(bm.faces, key=_face_center_x) if sign > 0 else min(bm.faces, key=_face_center_x)

def _get_end_cap_profile_edges(face):
    if face is None:
        return []

    profile_edges = []
    for edge in face.edges:
        delta = edge.verts[1].co - edge.verts[0].co
        abs_x = abs(delta.x)
        abs_y = abs(delta.y)
        abs_z = abs(delta.z)

        if abs_y > abs_z and abs_y >= abs_x:
            profile_edges.append(edge)

    if len(profile_edges) == 2:
        return profile_edges

    face_edges = list(face.edges)
    face_edges.sort(
        key=lambda edge: abs(edge.verts[1].co.y - edge.verts[0].co.y),
        reverse=True,
    )
    return face_edges[:2]

def _bevel_end_cap_profile(obj, sign, style):
    settings = _get_style_bevel_settings(style)
    if not obj or obj.type != 'MESH' or not settings:
        return False

    mesh = obj.data
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        bm.faces.ensure_lookup_table()
        bm.edges.ensure_lookup_table()

        target_face = _find_outer_face_by_x(bm, sign)
        profile_edges = _get_end_cap_profile_edges(target_face)
        if not profile_edges:
            return False

        bmesh.ops.bevel(
            bm,
            geom=profile_edges,
            affect='EDGES',
            offset=settings["offset"],
            offset_type='OFFSET',
            segments=settings["segments"],
            profile=settings["profile"],
            clamp_overlap=True,
        )
        bm.to_mesh(mesh)
        mesh.update()
        return True
    finally:
        bm.free()


# -------------------------------------------------------------------
# NURNIE ICON PREVIEW MENU
# NOTE: bpy.utils.previews is still present in Blender 4/5 in many builds,
# but can be removed/changed by Blender. This code keeps it isolated.
# If previews fail, the add-on remains usable (no crash) and UI still draws.
# -------------------------------------------------------------------

def enum_previews_from_directory_items(self, context):
    enum_items = []
    if context is None:
        return enum_items

    wm = context.window_manager
    directory = getattr(wm, "my_previews_dir", "")

    pcoll = preview_collections.get("main")
    if pcoll is None:
        # Previews not available/initialized; return empty list safely.
        return enum_items

    if directory == getattr(pcoll, "my_previews_dir", ""):
        return getattr(pcoll, "my_previews", enum_items)

    # Scan directory
    if directory and os.path.exists(directory):
        image_paths = [fn for fn in os.listdir(directory) if fn.lower().endswith(".png")]
        image_paths.sort()

        for i, name in enumerate(image_paths):
            filepath = os.path.join(directory, name)
            try:
                icon = pcoll.get(name)
                if not icon:
                    thumb = pcoll.load(name, filepath, 'IMAGE')
                else:
                    thumb = pcoll[name]
                enum_items.append((name, name, "", thumb.icon_id, i))
            except Exception:
                # If preview loading fails, still list the item (no icon)
                enum_items.append((name, name, "", 'FILE_IMAGE', i))

    pcoll.my_previews = enum_items
    pcoll.my_previews_dir = directory
    return getattr(pcoll, "my_previews", enum_items)

# -------------------------------------------------------------------
# Italics (text shear)
# -------------------------------------------------------------------

def italicText(self, context):
    obj = bpy.context.object
    if not obj or obj.type != 'FONT':
        return
    try:
        if bpy.context.scene.my_tool.it_bot_text:
            obj.data.shear = 0.2
        else:
            obj.data.shear = 0.0
    except Exception:
        pass

# -------------------------------------------------------------------
# Unhide helpers
# -------------------------------------------------------------------

def unhidenurnieleft(_self=None):
    obj = bpy.data.objects.get("NUR_LEFT")
    if obj:
        obj.hide_set(False)

def unhidenurnieright(_self=None):
    obj = bpy.data.objects.get("NUR_RIGHT")
    if obj:
        obj.hide_set(False)

# -------------------------------------------------------------------
# Move objects on their LOCAL axis rather than world
# -------------------------------------------------------------------

def get_locationZ(self):
    return self.get('locationZ', 0.0)

def set_locationZ(self, value):
    # This is actually local Y in your coordinate convention; keep original behaviour.
    z_axis = Vector((0, 1, 0))
    delta = value - self.get('locationZ', 0.0)
    v = (self.matrix_world.to_3x3() @ z_axis).normalized()
    self.matrix_world.translation += delta * v
    self['locationZ'] = float(value)

def get_locationY(self):
    return self.get('locationY', 0.0)

def set_locationY(self, value):
    y_axis = Vector((0, 0, 1))
    delta = value - self.get('locationY', 0.0)
    v = (self.matrix_world.to_3x3() @ y_axis).normalized()
    self.matrix_world.translation += delta * v
    self['locationY'] = float(value)

# -------------------------------------------------------------------
# Pointer menu: what to edit
# -------------------------------------------------------------------

def selectItem(self, context):
    name = str(bpy.context.scene.my_tool.my_item)
    menu = bpy.context.scene.objects.get(name)
    if menu:
        _deselect_all()
        _set_active(menu)
        menu.select_set(True)
        return

    default = bpy.context.scene.objects.get("BASE")
    if default:
        _deselect_all()
        _set_active(default)
        default.select_set(True)

# -------------------------------------------------------------------
# Base type dropdown hook
# -------------------------------------------------------------------

def selectBase(self, context):
    # Kept for compatibility with your UI; no-op is fine.
    return

# -------------------------------------------------------------------
# Autodraw toggle hook
# -------------------------------------------------------------------

def drawPlate(self, context):
    if bpy.context.scene.my_tool.autodraw:
        drawPlateTrue(self, context)

# -------------------------------------------------------------------
# Make duplicates real (NURNIES)
# -------------------------------------------------------------------

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

# -------------------------------------------------------------------
# Draw plate (core)
# -------------------------------------------------------------------

def drawPlateTrue(self, context):
    _ensure_object_mode()

    def halfscale(x, y, z):
        return (x * 0.5, y * 0.5, z * 0.5)

    # Oval / Lobed data (kept as-is; you said O-path is historical)
    O035 = ()
    O042 = ()
    O052 = ()
    O070 = ()
    O092 = ()
    O095 = ()
    O105 = ()
    L060 = ((30.3, 34.4), (44.1, 54.7), (51.7, 67))
    L075 = ((36.9, 33), (54, 51), (63.3, 63.3))
    L090 = ((45.5, 34.8), (65.8, 53.7), (77.4, 66.3))
    L105 = ((59.4, 46.3), (83.8, 67.9), (96.8, 81.3))
    L120 = ((76.1, 58.1), (105, 83.5), (120, 98.2))
    L150 = ((81.9, 41.7), (116, 62.6), (135, 76.1))
    L170 = ((87.5, 40.5), (125, 60.3), (145, 73.1))

    if "BASE" not in bpy.data.objects:
        # No base yet => nothing to build.
        return

    # Parameters from UI / objects
    base_obj = bpy.data.objects["BASE"]
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

    # Keep previous intent: if toggle enabled, top sits at user_z (on-top) else half-drop.
    top_position = user_z + top_height * 0.5 if not bpy.context.window_manager.my_operator_toggle else user_z

    # Length and curvature calculation
    if base_type == "C":
        radius = base_size_x * 0.5
        circumference = 2.0 * PI * radius
        arc_length = circumference * circle_curve
        user_x = arc_length - (end_length * 2.0)
        curve_x = arc_length / radius

    elif base_type == "O":
        base_selected = eval(base_type + base_string_x)
        user_x = base_selected[0] - (end_length * 2.0)
        curve_x = base_selected[1] * PI / 180.0

    elif base_type == "L":
        base_selected = eval(base_type + base_string_x)
        user_x = base_selected[oval_choice][0] - (end_length * 2.0)
        curve_x = base_selected[oval_choice][1] * PI / 180.0

    elif base_type == "S":
        user_x = base_size_y - (end_length * 2.0)
        curve_x = 0.0

    elif base_type == "Z":
        base_size_y = base_size_x
        radius = base_size_x * 0.5
        arc_length = (2.0 * PI * radius) * circle_curve
        user_x = arc_length - (end_length * 2.0)
        curve_x = arc_length / radius

    else:
        # Unknown base type
        return

    # Remove existing plate pieces
    for name in ['NameplateBase', 'NameplateTop', 'NameplateBottom', 'END_LEFT', 'END_RIGHT', 'TopBit', 'PLATE']:
        _safe_remove_object(name)

    # Build base plate pieces
    loc_y = -base_size_y * 0.5

    if bpy.context.scene.my_tool.eng_bot:
        bpy.ops.mesh.primitive_cube_add(align='WORLD', location=(0, loc_y - 0.25, user_z * 0.5),
                                        scale=halfscale(user_x, 1.5, user_z))
    else:
        bpy.ops.mesh.primitive_cube_add(align='WORLD', location=(0, loc_y, user_z * 0.5),
                                        scale=halfscale(user_x, user_y, user_z))
    base_piece = bpy.context.active_object
    base_piece.name = 'NameplateBase'

    bpy.ops.mesh.primitive_cube_add(
        align='WORLD',
        location=(0, loc_y - (user_y - border_thickness * 0.5), user_z - (border_thickness * 0.5)),
        scale=halfscale(user_x, border_depth, border_thickness)
    )
    top_border = bpy.context.active_object
    top_border.name = 'NameplateTop'

    bpy.ops.mesh.primitive_cube_add(
        align='WORLD',
        location=(0, loc_y - (user_y - border_thickness * 0.5), border_thickness * 0.5),
        scale=halfscale(user_x, border_depth, border_thickness)
    )
    bottom_border = bpy.context.active_object
    bottom_border.name = 'NameplateBottom'

    # Optional top section
    if bpy.context.scene.my_tool.add_top:
        _safe_remove_object('TopBit')

        bpy.ops.mesh.primitive_cube_add(
            align='WORLD',
            location=(0, loc_y - border_thickness * 0.5, top_position),
            scale=halfscale(user_x * top_panel_curve, user_y + border_thickness, top_height)
        )
        c = bpy.context.active_object
        c.name = 'TopBit'

        # Bevel edges in edit mode
        try:
            _set_active(c)
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.select_mode(type="EDGE")
            bpy.ops.object.mode_set(mode='OBJECT')
            # These indices match cube edge ordering; keep as-is.
            c.data.edges[2].select = True
            c.data.edges[8].select = True
            bpy.ops.object.mode_set(mode='EDIT')

            bevel_type = bpy.context.scene.my_tool.my_top_ends
            if bevel_type == "BEVEL":
                bpy.ops.mesh.bevel(offset=1.85688, segments=10)
            elif bevel_type == "CHAMFER":
                bpy.ops.mesh.bevel(offset=1.0, segments=10, affect='EDGES', profile=0.1)
            elif bevel_type == "SLANT":
                bpy.ops.mesh.bevel(offset=1.1, segments=0)

            bpy.ops.object.mode_set(mode='OBJECT')
        except Exception:
            _ensure_object_mode()
    else:
        _safe_remove_object('TopBit')

    # Ends (left/right)
    # Match original intent: only the two outer profile edges are styled.
    ends_def = [
        ("LEFT",  -1.0, 'END_LEFT'),
        ("RIGHT",  1.0, 'END_RIGHT'),
    ]
    for _side, sign, name in ends_def:
        if name in bpy.context.scene.objects:
            bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)

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

        # Apply end styling directly on the two outer profile edges.
        _bevel_end_cap_profile(c, sign, my_main_ends)

        c.name = name

    # Plate assembly
    # Plate assembly: join pieces
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
    plate.name = 'PLATE'

    # Always force deterministic orientation (prevents cumulative flips between redraws)
    # This is the key "tilt" fix: DO NOT use transform.rotate operator (context-sensitive).
    plate.rotation_euler[0] = -0.261799  # -15 degrees on X
    plate.rotation_euler[1] = 0.0
    plate.rotation_euler[2] = 0.0

    # Location and origin
    plate.location[2] = -0.15
    try:
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
    except Exception:
        pass

    # Modifiers
    try:
        rem = plate.modifiers.new(name="Remesh", type='REMESH')
        rem.voxel_size = 0.05
    except Exception:
        pass

    try:
        simp = plate.modifiers.new(name="SimpleDeform", type='SIMPLE_DEFORM')
        simp.deform_method = 'BEND'
        simp.deform_axis = 'Z'
        simp.origin = bpy.data.objects.get("EMPTY")
        simp.angle = curve_x
    except Exception:
        pass

    # Final placement
    plate.location[2] = user_z * 0.5 + 0.2

# -------------------------------------------------------------------
# Draw 90-degree FOV arc
# -------------------------------------------------------------------

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

# -------------------------------------------------------------------
# Draw base shapes + PATH
# -------------------------------------------------------------------

def drawCBase(self, context):
    _ensure_object_mode()
    for name in ['PATH', 'BASE', 'EMPTY', 'PLATE', 'FOV', 'MAINTEXT', 'UPPERTEXT', 'NURNIE_LEFT', 'NURNIE_RIGHT', 'NUR_LEFT', 'NUR_RIGHT']:
        _safe_remove_object(name)

    base_size_x = int(bpy.context.scene.my_tool.my_BCIRCLE[1:4])  # diameter
    base_size_y = int(bpy.context.scene.my_tool.my_BCIRCLE[4:])   # diameter

    bpy.ops.curve.primitive_bezier_circle_add(radius=base_size_x * 0.5, enter_editmode=False, align='WORLD', location=(0, 0, 0))
    path = bpy.context.active_object
    _set_active(path)
    try:
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.curve.switch_direction()
        bpy.ops.object.mode_set(mode='OBJECT')
    except Exception:
        _ensure_object_mode()
    path.name = 'PATH'

    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=base_size_x * 0.5, depth=4, enter_editmode=False, align='WORLD', location=(0, 0, 2))
    base = bpy.context.active_object
    base.name = 'BASE'
    base.data.name = bpy.context.scene.my_tool.my_BCIRCLE

    # Select top face and inset
    try:
        _set_active(base)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_mode(type='FACE')
        bpy.ops.object.mode_set(mode='OBJECT')

        # Find highest-z face
        top_index = max(
            range(len(base.data.polygons)),
            key=lambda i: sum(base.data.vertices[v].co.z for v in base.data.polygons[i].vertices) / len(base.data.polygons[i].vertices)
        )
        base.data.polygons[top_index].select = True

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.transform.resize(value=((base_size_x - 2) / base_size_x, (base_size_y - 2) / base_size_y, 1), orient_type='GLOBAL')
        bpy.ops.object.mode_set(mode='OBJECT')
    except Exception:
        _ensure_object_mode()

    _set_random_viewport_color()

def drawOBase(self, context):
    _ensure_object_mode()
    _safe_remove_object('PATH')
    _safe_remove_object('BASE')

    base_size_x = int(bpy.context.scene.my_tool.my_BOVAL[1:4])
    base_size_y = int(bpy.context.scene.my_tool.my_BOVAL[4:7])

    bpy.ops.curve.primitive_bezier_circle_add(radius=1, enter_editmode=True, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
    try:
        bpy.ops.curve.switch_direction()
    except Exception:
        pass
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.object.scale[0] = base_size_x * 0.5
    bpy.context.object.scale[1] = base_size_y * 0.5
    bpy.context.active_object.name = 'PATH'

    bpy.ops.mesh.primitive_cylinder_add(vertices=64, enter_editmode=True, align='WORLD', location=(0, 0, 2), scale=(base_size_x, base_size_y, 4))
    c = bpy.context.active_object

    try:
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        # Original assumed polygon index 62; keep but guard
        if len(c.data.polygons) > 62:
            c.data.polygons[62].select = True
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.transform.resize(value=((base_size_x - 2) / base_size_x, (base_size_y - 2) / base_size_y, 0), orient_type='GLOBAL')
        bpy.ops.object.mode_set(mode='OBJECT')
    except Exception:
        _ensure_object_mode()

    c.name = 'BASE'
    c.data.name = bpy.context.scene.my_tool.my_BOVAL

    _set_random_viewport_color()

def drawSBase(self, context):
    _ensure_object_mode()
    _safe_remove_object('PATH')
    _safe_remove_object('BASE')

    base_size_x = int(bpy.context.scene.my_tool.my_BSQUARE[1:4])
    base_size_y = int(bpy.context.scene.my_tool.my_BSQUARE[4:7])

    bpy.ops.curve.primitive_nurbs_path_add(radius=base_size_x * .25, enter_editmode=False, align='WORLD', location=(0, -base_size_y * .5, 0), scale=(1, 1, 1))
    bpy.context.active_object.name = 'PATH'

    bpy.ops.mesh.primitive_cube_add(enter_editmode=True, align='WORLD', location=(0, 0, 2), scale=(base_size_x, base_size_y, 4))
    c = bpy.context.active_object

    try:
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        if len(c.data.polygons) > 5:
            c.data.polygons[5].select = True
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.transform.resize(value=((base_size_x - 2) / base_size_x, (base_size_y - 2) / base_size_y, 0), orient_type='GLOBAL')
        bpy.ops.object.mode_set(mode='OBJECT')
    except Exception:
        _ensure_object_mode()

    c.name = 'BASE'
    c.data.name = bpy.context.scene.my_tool.my_BSQUARE

    _set_random_viewport_color()

def drawZBase(self, context):
    _ensure_object_mode()
    _safe_remove_object('PATH')
    _safe_remove_object('BASE')

    base_size_x = int(bpy.context.scene.my_tool.my_BSPECIAL[1:4])
    base_size_y = int(bpy.context.scene.my_tool.my_BSPECIAL[4:7])

    bpy.ops.curve.primitive_bezier_circle_add(radius=base_size_x * .5, enter_editmode=True, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
    try:
        bpy.ops.curve.switch_direction()
    except Exception:
        pass
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.active_object.name = 'PATH'

    bpy.ops.mesh.primitive_cylinder_add(vertices=64, enter_editmode=True, align='WORLD', location=(0, 0, 2), scale=(base_size_x, base_size_x, 4))
    c = bpy.context.active_object

    try:
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.object.mode_set(mode='OBJECT')
        if len(c.data.polygons) > 62:
            c.data.polygons[62].select = True
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.transform.resize(value=((base_size_x - 2) / base_size_x, (base_size_x - 2) / base_size_x, 0), orient_type='GLOBAL')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')

        # Keep original face selections, but guard index ranges
        for x in range(0, min(16, len(c.data.polygons))):
            c.data.polygons[x].select = True
        for x in range(48, min(62, len(c.data.polygons))):
            c.data.polygons[x].select = True
        for x in range(63, min(65, len(c.data.polygons))):
            c.data.polygons[x].select = True

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.transform.translate(value=(0, base_size_y - base_size_x, 0), orient_type='GLOBAL', constraint_axis=(False, True, False))
        bpy.ops.object.mode_set(mode='OBJECT')
    except Exception:
        _ensure_object_mode()

    c.name = 'BASE'
    c.data.name = bpy.context.scene.my_tool.my_BSPECIAL

    _set_random_viewport_color()

# -------------------------------------------------------------------
# Property group
# -------------------------------------------------------------------

class MyProperties(PropertyGroup):
    basic_options: bpy.props.BoolProperty(name="", default=True)
    addit_options: bpy.props.BoolProperty(name="", default=False)
    top_options: bpy.props.BoolProperty(name="", default=False)
    maintext_options: bpy.props.BoolProperty(name="", default=False)
    toptext_options: bpy.props.BoolProperty(name="", default=False)

    add_top: bpy.props.BoolProperty(name="", default=False, update=drawPlate)
    top_position: bpy.props.BoolProperty(name="", default=True, update=drawPlate)
    eng_bot: bpy.props.BoolProperty(name="", default=False, update=drawPlate)

    eng_top_text: bpy.props.BoolProperty(name="", default=False)
    it_top_text: bpy.props.BoolProperty(name="", default=False, update=italicText)
    eng_bot_text: bpy.props.BoolProperty(name="", default=False)
    it_bot_text: bpy.props.BoolProperty(name="", default=False, update=italicText)

    fov_option: bpy.props.BoolProperty(name="", default=False, update=drawFOV)
    autodraw: bpy.props.BoolProperty(name="", default=True, update=drawPlate)

    my_baselist: bpy.props.EnumProperty(
        items=[
            ('BCIRCLE', "Circle Bases", ""),
            ('BOVAL', "Oval Bases", ""),
            ('BSQUARE', "Square Bases", ""),
            ('BSPECIAL', "Special Bases", ""),
        ],
        default="BCIRCLE",
        update=selectBase
    )

    my_BSPECIAL: bpy.props.EnumProperty(
        items=[
            ('Z025070', "70X25 40K BIKE", ""),
            ('Z040095', "95X40 40K BIKE", ""),
        ],
        update=drawZBase
    )

    my_BCIRCLE: bpy.props.EnumProperty(
        items=[
            ('C025025', "25mm Circle", ""),
            ('C032032', "32mm Circle", ""),
            ('C040040', "40mm Circle", ""),
            ('C050050', "50mm Circle", ""),
            ('C060060', "60mm Circle", ""),
            ('C080080', "80mm Circle", ""),
            ('C100100', "100mm Circle", ""),
            ('C130130', "130mm Circle", ""),
            ('C160160', "160mm Circle", ""),
        ],
        update=drawCBase
    )

    my_BSQUARE: bpy.props.EnumProperty(
        items=[
            ('S025025', "25mm Square", ""),
            ('S032032', "32mm Square", ""),
            ('S040040', "40mm Square", ""),
            ('S050050', "50mm Square", ""),
            ('S060060', "60mm Square", ""),
            ('S080080', "80mm Square", ""),
            ('S100100', "100mm Square", ""),
            ('S130130', "130mm Square", ""),
            ('S160160', "160mm Square", ""),
        ],
        update=drawSBase
    )

    my_BOVAL: bpy.props.EnumProperty(
        items=[
            ('L060035', "60x35mm Oval Long Edge", ""),
            ('L075042', "75x42mm Oval Long Edge", ""),
            ('L090052', "90x52mm Oval Long Edge", ""),
            ('L105070', "105x70mm Oval Long Edge", ""),
            ('L120092', "120x92mm Oval Long Edge", ""),
            ('L150095', "150x95mm Oval Long Edge", ""),
            ('L170105', "170x105mm Oval Long Edge", ""),
        ],
        update=drawOBase
    )

    my_user_z: bpy.props.EnumProperty(
        items=[('3', "3mm", ""), ('4', "4mm", ""), ('5', "5mm", ""), ('6', "6mm", "")],
        default='4',
        update=drawPlate
    )

    my_main_ends: bpy.props.EnumProperty(
        items=[('PLAIN', "Plain", ""), ('BEVEL', "Round", ""), ('SLANT', "Slanted", ""), ('CHAMFER', "Chamfered", "")],
        default='PLAIN',
        update=drawPlate
    )

    my_top_ends: bpy.props.EnumProperty(
        items=[('PLAIN', "Plain", ""), ('BEVEL', "Round", ""), ('SLANT', "Slanted", ""), ('CHAMFER', "Chamfered", "")],
        default='PLAIN',
        update=drawPlate
    )

    my_top_height: bpy.props.EnumProperty(
        items=[('3', "1.5mm", ""), ('4', "2mm", ""), ('5', "2.5mm", ""), ('6', "3mm", "")],
        default='4',
        update=drawPlate
    )

    end_length: bpy.props.EnumProperty(
        items=[('2', "2mm End Caps", ""), ('3', "3mm End Caps", ""), ('4', "4mm End Caps", ""), ('5', "5mm End Caps", ""), ('6', "6mm End Caps", "")],
        default='4',
        update=drawPlate
    )

    top_angles: bpy.props.EnumProperty(
        items=[("25", "1/4 Base Coverage", ""), ("50", "1/2 Base Coverage", ""), ("75", "3/4 Coverage", ""), ("100", "Full Coverage", "")],
        default="50",
        update=drawPlate
    )

    o_angles: bpy.props.EnumProperty(
        items=[("0", "90 Degrees", "90 Degrees"), ("1", "120 Degrees", "120 Degrees"), ("2", "135 Degrees", "135 Degrees")],
        default="0",
        update=drawPlate
    )

    angles: bpy.props.EnumProperty(
        items=[("25", "90 Degrees", "90 Degrees"), ("33", "120 Degrees", "120 Degrees"), ("41", "150 Degrees", "150 Degrees"), ("50", "180 Degrees", "180 Degrees")],
        default="41",
        update=drawPlate
    )

    my_item: bpy.props.EnumProperty(
        items=[
            ('PLATE', "Nameplate", ""),
            ('UPPERTEXT', "Upper Text", ""),
            ('MAINTEXT', "Main Text", ""),
            ('NURNIE_LEFT', "Left Nurnie", ""),
            ('NURNIE_RIGHT', "Right Nurnie", ""),
        ],
        default="PLATE",
        update=selectItem
    )

    my_newbase: bpy.props.EnumProperty(
        items=[("NEW", "NEW", "NEW"), ("IMPORT", "IMPORT", "IMPORT")],
        default="NEW",
    )

# -------------------------------------------------------------------
# Import / Export + MessageBox
# -------------------------------------------------------------------

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
            # Older operator name fallback
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

        # Apply modifiers in a stable order if present
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

        # Optional boolean (FOV)
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

        # Optional text engrave on export
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

        # Select export objects
        _deselect_all()
        for o in bpy.data.objects:
            if o.name in (select_upper, select_main, "PLATE", "NUR_RIGHT.002", "NUR_LEFT.002"):
                o.select_set(True)

        # Export STL (support both operator names across versions)
        try:
            if self.filepath.lower().endswith('.stl'):
                bpy.ops.wm.stl_export(filepath=self.filepath, export_selected_objects=True, apply_modifiers=True, check_existing=True)
            else:
                bpy.ops.wm.stl_export(filepath=self.filepath + ".stl", export_selected_objects=True, apply_modifiers=True, check_existing=True)
        except Exception:
            # older
            if self.filepath.lower().endswith('.stl'):
                bpy.ops.export_mesh.stl(filepath=self.filepath, use_selection=True, check_existing=True, use_mesh_modifiers=True)
            else:
                bpy.ops.export_mesh.stl(filepath=self.filepath + ".stl", use_selection=True, check_existing=True, use_mesh_modifiers=True)

        # Cleanup temp objects
        for n in ('NUR_LEFT.002', 'NUR_RIGHT.002'):
            if n in bpy.context.scene.objects:
                bpy.data.objects.remove(bpy.data.objects[n], do_unlink=True)

        _deselect_all()
        _set_active(plate)
        plate.select_set(True)

        ShowMessageBox("Nameplate Saved", "Saved STL", 'DISK_DRIVE')
        return {"FINISHED"}

# -------------------------------------------------------------------
# UI Panel
# -------------------------------------------------------------------

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
        obj = context.object

        # Safety: if something errors in draw() Blender will show header only.
        # So we try hard not to throw.
        try:
            base_obj = bpy.context.scene.objects.get("BASE")
            plate_obj = bpy.context.scene.objects.get("PLATE")
            empty_obj = bpy.context.scene.objects.get("EMPTY")
            import_plate = bpy.context.scene.objects.get("IMPORTPLATE")
            base_type = base_obj.data.name[:1] if base_obj else ""

            # Main state: PLATE exists
            if plate_obj:
                box = layout.box()
                box.label(text="Choose what to edit", icon='GREASEPENCIL')
                box.prop(mytool, "my_item", expand=True)
                box.label(text="Options:", icon='LIGHT_DATA')
                box.operator("object.export_stl_custom", text="Save Your STL", icon='DISK_DRIVE')
                box.operator("clear_scene.myop_operator", text="Start Over", icon='RECOVER_LAST')
                if not import_plate:
                    box.operator("draw.myop_operator", text="Clear Any Engraves", icon='BRUSH_DATA')

                # Nurnie left controls
                if obj and obj.name == 'NURNIE_LEFT':
                    box = layout.box()
                    box.label(text="Edit Nurnie position:", icon='SMALL_CAPS')
                    loc_text = "<< Left / Right >>" if base_type == "S" else "<< Around Circle >>"
                    box.prop(obj, 'location', index=0, text=loc_text)
                    box.prop(obj, 'myNurnZFloat', slider=False)
                    box.prop(obj, 'myNurnYFloat', slider=False)
                    box.prop(obj, "instance_faces_scale", text="<< Scale >>", slider=False)
                    box.operator("flipnurnieleft.myop_operator", text="Flip Nurnie", icon='MOD_MIRROR')
                    box.operator("mirrornurnieleft.myop_operator", text="Mirror Nurnie On Plate", icon='UV_SYNC_SELECT')

                    box = layout.box()
                    box.label(text="Change Your Nurnie")
                    box.prop(wm, "my_previews_dir")
                    box.template_icon_view(wm, "my_previews")
                    box.operator("changenurnieleft.myop_operator", text="Change Nurnie", icon='FILE_REFRESH')

                    box = layout.box()
                    box.operator("deletenurnieleft.myop_operator", text="Remove Nurnie", icon='TRASH')

                elif mytool.my_item == 'NURNIE_LEFT' and 'NURNIE_LEFT' not in bpy.context.scene.objects and obj and obj.name == "BASE":
                    box = layout.box()
                    box.label(text="Add your Left Hand Nurnie")
                    box.prop(wm, "my_previews_dir")
                    box.template_icon_view(wm, "my_previews")
                    box.operator("addnurnieleft.myop_operator")

                # Nurnie right controls
                if obj and obj.name == 'NURNIE_RIGHT':
                    box = layout.box()
                    box.label(text="Edit Nurnie position:", icon='SMALL_CAPS')
                    loc_text = "<< Left / Right >>" if base_type == "S" else "<< Around Circle >>"
                    box.prop(obj, 'location', index=0, text=loc_text)
                    box.prop(obj, 'myNurnZFloat', slider=False)
                    box.prop(obj, 'myNurnYFloat', slider=False)
                    box.prop(obj, "instance_faces_scale", text="<< Scale >>", slider=False)
                    box.operator("flipnurnieright.myop_operator", text="Flip Nurnie", icon='MOD_MIRROR')
                    box.operator("mirrornurnieright.myop_operator", text="Mirror Nurnie On Plate", icon='UV_SYNC_SELECT')

                    box = layout.box()
                    box.label(text="Change Your Nurnie")
                    box.prop(wm, "my_previews_dir")
                    box.template_icon_view(wm, "my_previews")
                    box.operator("changenurnieright.myop_operator", text="Change Nurnie", icon='FILE_REFRESH')

                    box = layout.box()
                    box.operator("deletenurnieright.myop_operator", text="Remove Nurnie", icon='TRASH')

                elif mytool.my_item == 'NURNIE_RIGHT' and 'NURNIE_RIGHT' not in bpy.context.scene.objects and obj and obj.name == "BASE":
                    box = layout.box()
                    box.label(text="Add your Right Hand Nurnie")
                    box.prop(wm, "my_previews_dir")
                    box.template_icon_view(wm, "my_previews")
                    box.operator("addnurnieright.myop_operator")

                # Upper text controls
                if obj and obj.name == 'UPPERTEXT':
                    box = layout.box()
                    text = context.object.data
                    box.label(text="Edit your text:", icon='SMALL_CAPS')
                    box.prop(text, 'body', text="")

                    box = layout.box()
                    box.label(text="Choose Font:", icon='SMALL_CAPS')
                    box.template_ID(text, "font", open="font.open", unlink="font.unlink")

                    row = box.row()
                    row.label(text="Engrave Text On Export?")
                    row.prop(mytool, "eng_top_text")

                    row = box.row()
                    row.label(text="Italic")
                    row.prop(mytool, "it_bot_text")

                    box.prop(text, "size", text="Text Size")
                    box.label(text="Adjust Text Position:", icon='ORIENTATION_GLOBAL')
                    box.prop(obj, 'myZFloat', slider=False)
                    box.prop(obj, 'myYFloat', slider=False)

                    box = layout.box()
                    row = box.row()
                    row.prop(mytool, "maintext_options")
                    row.label(text="Text Extra Options")
                    if mytool.maintext_options:
                        box.label(text="Set the Spacing Options:", icon='CENTER_ONLY')
                        row = box.row()
                        row.label(text="Character:")
                        row.prop(text, "space_character", text="")
                        row = box.row()
                        row.label(text="Words:")
                        row.prop(text, "space_word", text="")
                        box.operator("increasevoxel.myop_operator", text="Increase Text Clarity", icon='MOD_THICKNESS')
                        box.operator("decreasevoxel.myop_operator", text="Decrease Text Clarity", icon='MOD_SMOOTH')

                # Main text controls
                if obj and obj.name == 'MAINTEXT':
                    box = layout.box()
                    text = context.object.data
                    box.label(text="Edit your text:", icon='SMALL_CAPS')
                    box.prop(text, 'body', text="")

                    box = layout.box()
                    box.label(text="Choose Font:", icon='SMALL_CAPS')
                    box.template_ID(text, "font", open="font.open", unlink="font.unlink")

                    row = box.row()
                    row.label(text="Engrave Text On Export?")
                    row.prop(mytool, "eng_bot_text")

                    row = box.row()
                    row.label(text="Italic")
                    row.prop(mytool, "it_bot_text")

                    box.prop(text, "size", text="Text Size")
                    box.label(text="Adjust Text Position:", icon='ORIENTATION_GLOBAL')
                    box.prop(obj, 'myZFloat', slider=False)
                    box.prop(obj, 'myYFloat', slider=False)

                    box = layout.box()
                    row = box.row()
                    row.prop(mytool, "maintext_options")
                    row.label(text="Text Extra Options")
                    if mytool.maintext_options:
                        box.label(text="Set the Spacing Options:", icon='CENTER_ONLY')
                        row = box.row()
                        row.label(text="Character:")
                        row.prop(text, "space_character", text="")
                        row = box.row()
                        row.label(text="Words:")
                        row.prop(text, "space_word", text="")
                        box.operator("increasevoxel.myop_operator", text="Increase Text Clarity", icon='MOD_THICKNESS')
                        box.operator("decreasevoxel.myop_operator", text="Decrease Text Clarity", icon='MOD_SMOOTH')

                # Plate controls
                if obj and obj.name == 'PLATE':
                    if import_plate:
                        box = layout.box()
                        box.label(text="Edit your nameplate position", icon='ORIENTATION_GLOBAL')
                        box.prop(obj, 'location', index=2, text='Adjust Up/Down:')
                        box.prop(obj, 'location', index=1, text='Adjust Back/Forward:')
                    else:
                        # Autodraw section
                        row = layout.row()
                        row.label(text="Autodraw")
                        row.prop(mytool, "autodraw")
                        if not mytool.autodraw:
                            layout.operator("draw.myop_operator", text="Create Plate", icon='GREASEPENCIL')

                        # Basic options
                        box = layout.box()
                        row = box.row()
                        row.prop(mytool, "basic_options")
                        row.label(text="Basic Plate Options")
                        if mytool.basic_options:
                            row = box.row()
                            row.label(text="Engravable/Plain Plate")
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

                            box.label(text="Choose your basic design", icon='IMAGE_ALPHA')
                            box.prop(mytool, "my_main_ends", expand=True)
                            box.label(text="Choose your end cap width", icon='FACE_MAPS')
                            box.prop(mytool, "end_length", expand=True)
                            box.label(text="Choose your height", icon='EMPTY_SINGLE_ARROW')
                            box.prop(mytool, "my_user_z", expand=True)

                        # Top options
                        box = layout.box()
                        row = box.row()
                        row.prop(mytool, "top_options")
                        row.label(text="Top Plate Options")
                        if mytool.top_options:
                            row = box.row()
                            row.label(text="Add top plate")
                            row.prop(mytool, "add_top")
                            box.label(text="Choose top plate height!", icon='EXPORT')
                            box.prop(mytool, "my_top_height", expand=True)
                            box.label(text="Length of plate", icon='PROP_PROJECTED')
                            box.prop(mytool, "top_angles", expand=True)
                            box.label(text="Choose position of top plate!")
                            label = "Put On Top" if wm.my_operator_toggle else "Drop Half Way"
                            icon = 'ANCHOR_TOP' if wm.my_operator_toggle else 'ANCHOR_CENTER'
                            box.prop(wm, 'my_operator_toggle', text=label, icon=icon, toggle=True)
                            box.label(text="Choose top plate design!")
                            box.prop(mytool, "my_top_ends", expand=True)

                        # Advanced options
                        box = layout.box()
                        row = box.row()
                        row.prop(mytool, "addit_options")
                        row.label(text="Advanced options")
                        if mytool.addit_options:
                            row = box.row()
                            row.label(text="Add FOV cut out", icon='LINCURVE')
                            row.prop(mytool, "fov_option")

                return

            # Import plate state
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

            # Start state
            if not empty_obj:
                box = layout.box()
                box.label(text="! LETS GET STARTED !")
                box = layout.box()
                box.label(text="Please select an option")
                layout.prop(mytool, "my_newbase", expand=True)

                if mytool.my_newbase == "IMPORT":
                    box = layout.box()
                    box.label(text="Import a previously saved plate")
                    box = layout.box()
                    box.operator("object.import_stl_custom", text="Import a Saved Plate", icon='FILE_NEW')

                if mytool.my_newbase == "NEW":
                    box = layout.box()
                    box.label(text="Create a Brand New plate!", icon='FILE_NEW')
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

# -------------------------------------------------------------------
# Help window
# -------------------------------------------------------------------

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

# -------------------------------------------------------------------
# Increase/Decrease text voxel
# -------------------------------------------------------------------

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

# -------------------------------------------------------------------
# Draw operator (rebuild plate)
# -------------------------------------------------------------------

class DRAW_OT_my_op(Operator):
    bl_label = "Draw"
    bl_idname = "draw.myop_operator"

    def execute(self, context):
        drawPlateTrue(self, context)
        return {'FINISHED'}

# -------------------------------------------------------------------
# Clear scene operator
# -------------------------------------------------------------------

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

# -------------------------------------------------------------------
# Set/Mirror/Flip/Change/Add/Delete Nurnies
# (Mostly kept as your original behaviour; just mode/context hardening)
# -------------------------------------------------------------------

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
        _ensure_object_mode()

        base = bpy.data.objects.get("BASE")
        if not base:
            return {'CANCELLED'}

        base_type = base.data.name[:1]
        base_size_x = int(base.data.name[1:4])
        base_size_y = int(base.data.name[4:7])

        _safe_remove_object('NURNIE_RIGHT')
        _safe_remove_object('NUR_RIGHT')

        src = bpy.data.objects.get('NURNIE_LEFT')
        if not src:
            return {'CANCELLED'}

        nurnie_x = -src.location.x
        nurnie_y = src.location.y
        nurnie_z = src.location.z
        nurnie_s = src.instance_faces_scale

        unhidenurnieleft(self)

        ob = bpy.context.scene.objects.get("NUR_LEFT")
        if not ob:
            return {'CANCELLED'}

        _deselect_all()
        _set_active(ob)
        ob.select_set(True)
        bpy.ops.object.duplicate()
        bpy.ops.object.parent_clear(type='CLEAR')
        bpy.context.active_object.name = 'NUR_RIGHT'

        circle_curve = int(bpy.context.scene.my_tool.angles) * .01
        if circle_curve == .41:
            circle_curve = .415

        if base_type == "S":
            bpy.ops.mesh.primitive_plane_add(enter_editmode=False, align='WORLD', location=((base_size_x - 2, -base_size_y * .5 - .5, 2)))
        else:
            bpy.ops.mesh.primitive_plane_add(
                enter_editmode=False, align='WORLD',
                location=(((base_size_x * PI) * .25) + ((base_size_x * PI) * circle_curve * .5) - (float(bpy.context.scene.my_tool.end_length) * .5), -1.5, int(bpy.context.scene.my_tool.my_user_z) * .5)
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

        if "NUR_LEFT" in bpy.data.objects:
            bpy.data.objects["NUR_LEFT"].hide_set(True)
        if "NUR_RIGHT" in bpy.data.objects:
            bpy.data.objects["NUR_RIGHT"].hide_set(True)

        ob = bpy.context.scene.objects.get("NURNIE_LEFT")
        if ob:
            _deselect_all()
            _set_active(ob)
            ob.select_set(True)

        return {'FINISHED'}

class MIRRORNURNIERIGHT_OT_my_op(Operator):
    bl_label = "Mirror Nurnie Right"
    bl_idname = "mirrornurnieright.myop_operator"

    def execute(self, context):
        _ensure_object_mode()

        base = bpy.data.objects.get("BASE")
        if not base:
            return {'CANCELLED'}

        base_type = base.data.name[:1]
        base_size_x = int(base.data.name[1:4])
        base_size_y = int(base.data.name[4:7])

        _safe_remove_object('NURNIE_LEFT')
        _safe_remove_object('NUR_LEFT')

        src = bpy.data.objects.get('NURNIE_RIGHT')
        if not src:
            return {'CANCELLED'}

        nurnie_x = src.location.x
        nurnie_y = src.location.y
        nurnie_z = src.location.z
        nurnie_s = src.instance_faces_scale

        unhidenurnieright(self)

        ob = bpy.context.scene.objects.get("NUR_RIGHT")
        if not ob:
            return {'CANCELLED'}

        _deselect_all()
        _set_active(ob)
        ob.select_set(True)
        bpy.ops.object.duplicate()
        bpy.ops.object.parent_clear(type='CLEAR')
        bpy.context.active_object.name = 'NUR_LEFT'

        circle_curve = int(bpy.context.scene.my_tool.angles) * .01
        if circle_curve == .41:
            circle_curve = .415

        if base_type == "S":
            bpy.ops.mesh.primitive_plane_add(enter_editmode=False, align='WORLD', location=(2, -base_size_y * .5 - .5, 2))
        else:
            bpy.ops.mesh.primitive_plane_add(
                enter_editmode=False, align='WORLD',
                location=(((base_size_x * PI) * .25) - ((base_size_x * PI) * circle_curve * .5) + (float(bpy.context.scene.my_tool.end_length) * .5), -1.5, int(bpy.context.scene.my_tool.my_user_z) * .5)
            )

        bpy.ops.transform.resize(value=(0.1, 0.1, 0.1), orient_type='GLOBAL')
        bpy.ops.object.transform_apply(location=True, rotation=False, scale=True)
        bpy.context.active_object.name = 'NURNIE_LEFT'
        bpy.context.object.location[0] = -nurnie_x
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

        if "NUR_LEFT" in bpy.data.objects:
            bpy.data.objects["NUR_LEFT"].hide_set(True)
        if "NUR_RIGHT" in bpy.data.objects:
            bpy.data.objects["NUR_RIGHT"].hide_set(True)

        ob = bpy.context.scene.objects.get("NURNIE_RIGHT")
        if ob:
            _deselect_all()
            _set_active(ob)
            ob.select_set(True)

        return {'FINISHED'}

class DELETENURNIELEFT_OT_my_op(Operator):
    bl_label = "Delete Nurnie"
    bl_idname = "deletenurnieleft.myop_operator"

    def execute(self, context):
        _safe_remove_object('NURNIE_LEFT')
        _safe_remove_object('NUR_LEFT')
        return {'FINISHED'}

class DELETENURNIERIGHT_OT_my_op(Operator):
    bl_label = "Delete Nurnie"
    bl_idname = "deletenurnieright.myop_operator"

    def execute(self, context):
        _safe_remove_object('NURNIE_RIGHT')
        _safe_remove_object('NUR_RIGHT')
        return {'FINISHED'}

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

        nurnie_x = anchor.location.x
        nurnie_y = anchor.location.y
        nurnie_z = anchor.location.z
        nurnie_s = anchor.instance_faces_scale

        wm = context.window_manager
        import_dir = wm.my_previews_dir
        import_file = bpy.data.window_managers["WinMan"].my_previews[:-4]

        bpy.ops.wm.stl_import(filepath=os.path.join(import_dir, import_file + ".stl"))

        _safe_remove_object('NURNIE_LEFT')
        _safe_remove_object('NUR_LEFT')
        bpy.context.active_object.name = 'NUR_LEFT'

        circle_curve = int(bpy.context.scene.my_tool.angles) * .01
        if circle_curve == .41:
            circle_curve = .415

        if base_type == "S":
            bpy.ops.mesh.primitive_plane_add(enter_editmode=False, align='WORLD', location=(2, -base_size_y * .5 - .5, 2))
        else:
            bpy.ops.mesh.primitive_plane_add(
                enter_editmode=False, align='WORLD',
                location=(((base_size_x * PI) * .25) - ((base_size_x * PI) * circle_curve * .5) + (float(bpy.context.scene.my_tool.end_length) * .5), -1.5, int(bpy.context.scene.my_tool.my_user_z) * .5)
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

        nurnie_x = anchor.location.x
        nurnie_y = anchor.location.y
        nurnie_z = anchor.location.z
        nurnie_s = anchor.instance_faces_scale

        wm = context.window_manager
        import_dir = wm.my_previews_dir
        import_file = bpy.data.window_managers["WinMan"].my_previews[:-4]

        bpy.ops.wm.stl_import(filepath=os.path.join(import_dir, import_file + ".stl"))

        _safe_remove_object('NURNIE_RIGHT')
        _safe_remove_object('NUR_RIGHT')
        bpy.context.active_object.name = 'NUR_RIGHT'

        circle_curve = int(bpy.context.scene.my_tool.angles) * .01
        if circle_curve == .41:
            circle_curve = .415

        if base_type == "S":
            bpy.ops.mesh.primitive_plane_add(enter_editmode=False, align='WORLD', location=((base_size_x - 2, -base_size_y * .5 - .5, 2)))
        else:
            bpy.ops.mesh.primitive_plane_add(
                enter_editmode=False, align='WORLD',
                location=(((base_size_x * PI) * .25) + ((base_size_x * PI) * circle_curve * .5) - (float(bpy.context.scene.my_tool.end_length) * .5), -1.5, int(bpy.context.scene.my_tool.my_user_z) * .5)
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

        circle_curve = int(bpy.context.scene.my_tool.angles) * .01
        if circle_curve == .41:
            circle_curve = .415

        if base_type == "S":
            bpy.ops.mesh.primitive_plane_add(enter_editmode=False, align='WORLD', location=(2, -base_size_y * .5 - .5, 2))
        else:
            bpy.ops.mesh.primitive_plane_add(
                enter_editmode=False, align='WORLD',
                location=(((base_size_x * PI) * .25) - ((base_size_x * PI) * circle_curve * .5) + (float(bpy.context.scene.my_tool.end_length) * .5), -1.5, int(bpy.context.scene.my_tool.my_user_z) * .5)
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

        circle_curve = int(bpy.context.scene.my_tool.angles) * .01
        if circle_curve == .41:
            circle_curve = .415

        if base_type == "S":
            bpy.ops.mesh.primitive_plane_add(enter_editmode=False, align='WORLD', location=((base_size_x - 2, -base_size_y * .5 - .5, 2)))
        else:
            bpy.ops.mesh.primitive_plane_add(
                enter_editmode=False, align='WORLD',
                location=(((base_size_x * PI) * .25) + ((base_size_x * PI) * circle_curve * .5) - (float(bpy.context.scene.my_tool.end_length) * .5), -1.5, int(bpy.context.scene.my_tool.my_user_z) * .5)
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

        if "NUR_RIGHT" in bpy.data.objects:
            bpy.data.objects["NUR_RIGHT"].hide_set(True)

        return {'FINISHED'}

class FLIPNURNIELEFT_OT_my_op(Operator):
    bl_label = "Flip Nurnie Left"
    bl_idname = "flipnurnieleft.myop_operator"

    def execute(self, context):
        _ensure_object_mode()
        unhidenurnieleft(self)

        ob = bpy.context.scene.objects.get("NUR_LEFT")
        if not ob:
            return {'CANCELLED'}

        _deselect_all()
        _set_active(ob)
        ob.select_set(True)

        ob.rotation_euler[2] = PI
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

        parent = bpy.context.scene.objects.get("NURNIE_LEFT")
        if parent:
            _deselect_all()
            _set_active(parent)
            parent.select_set(True)

        if "NUR_LEFT" in bpy.data.objects:
            bpy.data.objects["NUR_LEFT"].hide_set(True)

        return {'FINISHED'}

class FLIPNURNIERIGHT_OT_my_op(Operator):
    bl_label = "Flip Nurnie"
    bl_idname = "flipnurnieright.myop_operator"

    def execute(self, context):
        _ensure_object_mode()
        unhidenurnieright(self)

        ob = bpy.context.scene.objects.get("NUR_RIGHT")
        if not ob:
            return {'CANCELLED'}

        _deselect_all()
        _set_active(ob)
        ob.select_set(True)

        ob.rotation_euler[2] = PI
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

        parent = bpy.context.scene.objects.get("NURNIE_RIGHT")
        if parent:
            _deselect_all()
            _set_active(parent)
            parent.select_set(True)

        if "NUR_RIGHT" in bpy.data.objects:
            bpy.data.objects["NUR_RIGHT"].hide_set(True)

        return {'FINISHED'}

# -------------------------------------------------------------------
# Getready operator (axis + text)
# -------------------------------------------------------------------

class Getready_OT_my_op(Operator):
    bl_label = "Get it Ready"
    bl_idname = "getready.myop_operator"

    def execute(self, context):
        _ensure_object_mode()

        # Remove default scene objects if present
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

        # Main text
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
            bpy.context.object.data.offset_x = (base_size_x * PI) * .25
            bpy.ops.object.modifier_add(type='CURVE')
            bpy.context.object.modifiers["Curve"].object = bpy.data.objects.get("PATH")
            bpy.context.object.data.offset_y = 2.1

        bpy.ops.object.modifier_add(type='REMESH')
        bpy.context.object.modifiers["Remesh"].voxel_size = 0.04
        bpy.context.object.modifiers["Remesh"].use_remove_disconnected = False
        bpy.context.object.modifiers["Remesh"].use_smooth_shade = True

        # Upper text
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
            bpy.context.object.data.offset_x = (base_size_x * PI) * .25
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

# -------------------------------------------------------------------
# Additional properties on Object type
# -------------------------------------------------------------------

bpy.types.Object.myZFloat = FloatProperty(
    name="<< Down / Up >>", description="Set the location on local Z axis",
    min=-100, max=100, soft_min=-10, soft_max=10, step=1, subtype='DISTANCE',
    get=get_locationZ, set=set_locationZ
)
bpy.types.Object.myYFloat = FloatProperty(
    name="<< Back / Forwards >>", description="Set the location on local Y axis",
    min=-100, max=100, soft_min=-10, soft_max=10, step=1, subtype='DISTANCE',
    get=get_locationY, set=set_locationY
)
bpy.types.Object.myNurnZFloat = FloatProperty(
    name="<< Back / Forwards >>", description="Set the location on local Z axis",
    min=-100, max=100, soft_min=-10, soft_max=10, step=1, subtype='DISTANCE',
    get=get_locationZ, set=set_locationZ
)
bpy.types.Object.myNurnYFloat = FloatProperty(
    name="<< Down / Up >>", description="Set the location on local Y axis",
    min=-100, max=100, soft_min=-10, soft_max=10, step=1, subtype='DISTANCE',
    get=get_locationY, set=set_locationY
)

# -------------------------------------------------------------------
# Register / Unregister
# -------------------------------------------------------------------

classes = [
    MyProperties,
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
    OBJECT_PT_NamePlate,
    Import_STL_Custom,
    Export_STL_Custom,
]

def register():
    from bpy.types import WindowManager
    from bpy.props import StringProperty, EnumProperty, BoolProperty

    # WM toggle belongs on WindowManager, not defined inside PropertyGroup
    if not hasattr(WindowManager, "my_operator_toggle"):
        WindowManager.my_operator_toggle = BoolProperty(name="", default=False, update=drawPlate)

    WindowManager.my_previews_dir = StringProperty(name="", subtype='DIR_PATH', default="")
    WindowManager.my_previews = EnumProperty(items=enum_previews_from_directory_items)

    # Initialize previews (optional; won't crash addon if unavailable)
    try:
        import bpy.utils.previews
        pcoll = bpy.utils.previews.new()
        pcoll.my_previews_dir = ""
        pcoll.my_previews = ()
        preview_collections["main"] = pcoll
    except Exception:
        preview_collections.clear()

    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.my_tool = bpy.props.PointerProperty(type=MyProperties)

def unregister():
    from bpy.types import WindowManager

    if hasattr(bpy.types.Scene, "my_tool"):
        del bpy.types.Scene.my_tool

    # Remove WM properties
    if hasattr(WindowManager, "my_previews"):
        del WindowManager.my_previews
    if hasattr(WindowManager, "my_previews_dir"):
        del WindowManager.my_previews_dir
    if hasattr(WindowManager, "my_operator_toggle"):
        del WindowManager.my_operator_toggle

    # Dispose previews
    try:
        import bpy.utils.previews
        for pcoll in preview_collections.values():
            bpy.utils.previews.remove(pcoll)
    except Exception:
        pass
    preview_collections.clear()

    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass

if __name__ == "__main__":
    register()
