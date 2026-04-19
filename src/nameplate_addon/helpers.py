import os

import bmesh
import bpy
from mathutils import Euler, Vector

from .constants import (
    BASE_OBJECT,
    LEFT_NUR_OBJECT,
    LEFT_NURNIE_OBJECT,
    MAIN_TEXT_OBJECT,
    PLATE_OBJECT,
    RIGHT_NUR_OBJECT,
    RIGHT_NURNIE_OBJECT,
    UPPER_TEXT_OBJECT,
)


preview_collections = {}
_IS_PROGRAMMATIC_EDIT_TARGET_FOCUS = False

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


def mm(val):
    return val * 0.1


def set_active(obj):
    # Selection-reset helper: use this only when deselecting everything first is required.
    # This is NOT interchangeable with _set_active(); swapping them has already broken join flows.
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def get_managed_objects():
    return [o for o in bpy.data.objects if o.get("nameplate_managed")]


def delete_managed_objects():
    for o in get_managed_objects():
        bpy.data.objects.remove(o, do_unlink=True)


def _deselect_all():
    try:
        bpy.ops.object.select_all(action='DESELECT')
    except Exception:
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
        except Exception:
            pass


def _set_active(obj):
    # Legacy active-object helper: intentionally does not change the current selection set.
    # Multi-object operators such as join rely on this preserving already-selected objects.
    if obj is None:
        return
    try:
        bpy.context.view_layer.objects.active = obj
    except Exception:
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


def _find_top_face_index(obj):
    if not obj or obj.type != 'MESH' or not obj.data.polygons:
        return None
    return max(
        range(len(obj.data.polygons)),
        key=lambda i: sum(obj.data.vertices[v].co.z for v in obj.data.polygons[i].vertices) / len(obj.data.polygons[i].vertices)
    )


def _inset_top_face(obj, scale_x, scale_y):
    if not obj or obj.type != 'MESH':
        return False

    try:
        _set_active(obj)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_mode(type='FACE')
        bpy.ops.object.mode_set(mode='OBJECT')

        top_index = _find_top_face_index(obj)
        if top_index is None:
            return False

        obj.data.polygons[top_index].select = True

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.transform.resize(value=(scale_x, scale_y, 1), orient_type='GLOBAL')
        bpy.ops.object.mode_set(mode='OBJECT')
        return True
    except Exception:
        _ensure_object_mode()
        return False


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


def _apply_bevel_to_bmesh_edges(bm, edges, style):
    settings = _get_style_bevel_settings(style)
    if not settings:
        return False

    valid_edges = [edge for edge in edges if edge is not None]
    if not valid_edges:
        return False

    bmesh.ops.bevel(
        bm,
        geom=valid_edges,
        affect='EDGES',
        offset=settings["offset"],
        offset_type='OFFSET',
        segments=settings["segments"],
        profile=settings["profile"],
        clamp_overlap=True,
    )
    return True


def _bevel_mesh_edges_by_index(obj, edge_indices, style):
    if not obj or obj.type != 'MESH':
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

        if not _apply_bevel_to_bmesh_edges(bm, edges, style):
            return False

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
    if not obj or obj.type != 'MESH':
        return False

    mesh = obj.data
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        bm.faces.ensure_lookup_table()
        bm.edges.ensure_lookup_table()

        target_face = _find_outer_face_by_x(bm, sign)
        profile_edges = _get_end_cap_profile_edges(target_face)
        if not _apply_bevel_to_bmesh_edges(bm, profile_edges, style):
            return False

        bm.to_mesh(mesh)
        mesh.update()
        return True
    finally:
        bm.free()


def _world_co(obj, vert):
    return obj.matrix_world @ vert.co


def _find_outer_face_by_x_world(obj, bm, sign):
    if not bm.faces:
        return None

    def _face_center_x_world(face):
        coords = [_world_co(obj, vert) for vert in face.verts]
        return sum(co.x for co in coords) / len(coords)

    return max(bm.faces, key=_face_center_x_world) if sign > 0 else min(bm.faces, key=_face_center_x_world)


def _get_top_face_profile_edge(obj, face):
    if face is None:
        return None

    face_world = [_world_co(obj, vert) for vert in face.verts]
    if not face_world:
        return None

    top_z = max(co.z for co in face_world)
    z_tol = max(obj.dimensions.z, 1.0) * 1e-5

    candidate_edges = []
    for edge in face.edges:
        v0 = _world_co(obj, edge.verts[0])
        v1 = _world_co(obj, edge.verts[1])
        delta = v1 - v0
        abs_x = abs(delta.x)
        abs_y = abs(delta.y)
        abs_z = abs(delta.z)

        if not (abs_y > abs_z and abs_y >= abs_x):
            continue

        edge_top_z = max(v0.z, v1.z)
        both_top = abs(v0.z - top_z) <= z_tol and abs(v1.z - top_z) <= z_tol
        edge_mid_z = (v0.z + v1.z) * 0.5
        candidate_edges.append((both_top, edge_top_z, edge_mid_z, edge))

    if not candidate_edges:
        return None

    candidate_edges.sort(key=lambda item: (item[0], item[1], item[2]), reverse=True)
    return candidate_edges[0][3]


def _bevel_top_plate_profile(obj, style, drop_top_halfway=False):
    if not obj or obj.type != 'MESH':
        return False

    mesh = obj.data
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        bm.edges.ensure_lookup_table()

        target_indices = [2, 8]
        if drop_top_halfway:
            target_indices.extend([0, 7])

        target_edges = [
            bm.edges[i] for i in target_indices
            if 0 <= i < len(bm.edges)
        ]

        if not _apply_bevel_to_bmesh_edges(bm, target_edges, style):
            return False

        bm.to_mesh(mesh)
        mesh.update()
        return True
    finally:
        bm.free()


def enum_previews_from_directory_items(self, context):
    enum_items = []
    if context is None:
        return enum_items

    wm = context.window_manager
    directory = getattr(wm, "my_previews_dir", "")

    pcoll = preview_collections.get("main")
    if pcoll is None:
        return enum_items

    if directory == getattr(pcoll, "my_previews_dir", ""):
        return getattr(pcoll, "my_previews", enum_items)

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
                enum_items.append((name, name, "", 'FILE_IMAGE', i))

    pcoll.my_previews = enum_items
    pcoll.my_previews_dir = directory
    return getattr(pcoll, "my_previews", enum_items)


def italicText(self, context):
    obj = bpy.context.object
    if not obj or obj.type != 'FONT':
        return
    try:
        tool = bpy.context.scene.my_tool
        if obj.name == "UPPERTEXT":
            is_italic = bool(tool.it_top_text)
        else:
            is_italic = bool(tool.it_bot_text)

        if is_italic:
            obj.data.shear = 0.2
        else:
            obj.data.shear = 0.0
    except Exception:
        pass


def unhidenurnieleft(_self=None):
    obj = bpy.data.objects.get("NUR_LEFT")
    if obj:
        obj.hide_set(False)


def unhidenurnieright(_self=None):
    obj = bpy.data.objects.get("NUR_RIGHT")
    if obj:
        obj.hide_set(False)


NURNIE_CONFIG = {
    "LEFT": {
        "nur": "NUR_LEFT",
        "nurnie": "NURNIE_LEFT",
        "unhide": unhidenurnieleft,
    },
    "RIGHT": {
        "nur": "NUR_RIGHT",
        "nurnie": "NURNIE_RIGHT",
        "unhide": unhidenurnieright,
    },
}


def store_nurnie_anchor_state(obj):
    if obj is None:
        return
    obj["nurnie_anchor_x"] = obj.location.x
    obj["nurnie_anchor_y"] = obj.location.y
    obj["nurnie_anchor_z"] = obj.location.z
    obj["nurnie_scale"] = getattr(obj, "instance_faces_scale", 0.0)
    if getattr(obj, "type", "") == 'MESH' and getattr(obj, "data", None) and getattr(obj.data, "vertices", None):
        verts = obj.data.vertices
        count = len(verts)
        if count:
            obj["nurnie_plane_x"] = sum(v.co.x for v in verts) / count
            obj["nurnie_plane_y"] = sum(v.co.y for v in verts) / count
            obj["nurnie_plane_z"] = sum(v.co.z for v in verts) / count


def get_nurnie_anchor_state(obj):
    if obj is None:
        return None
    return {
        "x": obj.get("nurnie_anchor_x", obj.location.x),
        "y": obj.get("nurnie_anchor_y", obj.location.y),
        "z": obj.get("nurnie_anchor_z", obj.location.z),
        "scale": obj.get("nurnie_scale", getattr(obj, "instance_faces_scale", 0.0)),
        "plane_x": obj.get("nurnie_plane_x", 0.0),
        "plane_y": obj.get("nurnie_plane_y", 0.0),
        "plane_z": obj.get("nurnie_plane_z", 0.0),
    }


def get_locationZ(self):
    return self.get('locationZ', 0.0)


def set_locationZ(self, value):
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


def _get_view3d_override_context():
    window = getattr(bpy.context, "window", None)
    if window is None:
        return None

    screen = getattr(window, "screen", None)
    if screen is None:
        return None

    for area in screen.areas:
        if area.type != 'VIEW_3D':
            continue
        for region in area.regions:
            if region.type == 'WINDOW':
                return {
                    "window": window,
                    "screen": screen,
                    "area": area,
                    "region": region,
                    "scene": bpy.context.scene,
                    "view_layer": bpy.context.view_layer,
                }
    return None


def _is_plate_view_target(target_name):
    return target_name in {PLATE_OBJECT, MAIN_TEXT_OBJECT, UPPER_TEXT_OBJECT}


def _get_focus_target_object(scene, target_name):
    if _is_plate_view_target(target_name):
        return scene.objects.get(PLATE_OBJECT)
    if target_name == LEFT_NURNIE_OBJECT:
        return scene.objects.get(LEFT_NUR_OBJECT) or scene.objects.get(LEFT_NURNIE_OBJECT)
    if target_name == RIGHT_NURNIE_OBJECT:
        return scene.objects.get(RIGHT_NUR_OBJECT) or scene.objects.get(RIGHT_NURNIE_OBJECT)
    return scene.objects.get(target_name)


def _get_base_span(scene):
    base_obj = scene.objects.get(BASE_OBJECT)
    if base_obj is None or not getattr(base_obj, "dimensions", None):
        return 0.0
    return max(base_obj.dimensions.x, base_obj.dimensions.y, base_obj.dimensions.z)


def _get_base_type(scene):
    base_obj = scene.objects.get(BASE_OBJECT)
    if base_obj is None or not getattr(base_obj, "data", None):
        return ""
    return str(getattr(base_obj.data, "name", ""))[:1]


def _apply_view_focus(target_name, focus_target):
    override = _get_view3d_override_context()
    if override is None:
        return

    try:
        with bpy.context.temp_override(**override):
            region_3d = override["area"].spaces.active.region_3d

            if _is_plate_view_target(target_name):
                bpy.ops.view3d.view_axis(type='FRONT', align_active=False)
            bpy.ops.view3d.view_selected(use_all_regions=False)

            if _is_plate_view_target(target_name):
                base_rotation = region_3d.view_rotation.copy()
                delta_rotation = Euler((-(0.174533), 0.0, 0.0), 'XYZ').to_quaternion()
                region_3d.view_rotation = base_rotation @ delta_rotation
                region_3d.view_perspective = 'PERSP'
                base_span = _get_base_span(bpy.context.scene)
                half_base_span = base_span * 0.5
                target_span = max(focus_target.dimensions) if focus_target is not None and getattr(focus_target, "dimensions", None) else 0.0
                computed_distance = max(0.1, half_base_span + max(24.0, target_span * 0.18))
                region_3d.view_distance = computed_distance
                print(
                    "[Nameplate] Plate/Text view distance:",
                    f"target={target_name}",
                    f"base_span={base_span:.3f}",
                    f"half_base_span={half_base_span:.3f}",
                    f"target_span={target_span:.3f}",
                    f"view_distance={computed_distance:.3f}",
                )
            elif target_name in {LEFT_NURNIE_OBJECT, RIGHT_NURNIE_OBJECT} and focus_target is not None:
                base_span = _get_base_span(bpy.context.scene)
                base_type = _get_base_type(bpy.context.scene)
                target_distance = focus_target.matrix_world.translation.length
                target_span = max(focus_target.dimensions) if getattr(focus_target, "dimensions", None) else 0.0

                bpy.ops.view3d.view_axis(type='FRONT', align_active=False)
                region_3d.view_perspective = 'PERSP'

                if base_type == "S":
                    base_rotation = region_3d.view_rotation.copy()
                    delta_rotation = Euler((-(0.174533), 0.0, 0.0), 'XYZ').to_quaternion()
                    region_3d.view_rotation = base_rotation @ delta_rotation
                else:
                    side_turn = -1.047198 if target_name == LEFT_NURNIE_OBJECT else 1.047198
                    delta_rotation = Euler((-(0.174533), side_turn, 0.0), 'XYZ').to_quaternion()
                    region_3d.view_rotation = region_3d.view_rotation.copy() @ delta_rotation
                    region_3d.view_location = Vector((0.0, 0.0, 0.0))

                computed_distance = max(0.1, base_span + target_distance + max(20.0, target_span * 4.5))
                region_3d.view_distance = computed_distance
                print(
                    "[Nameplate] Nurnie view distance:",
                    f"base_type={base_type}",
                    f"base_span={base_span:.3f}",
                    f"target_distance={target_distance:.3f}",
                    f"target_span={target_span:.3f}",
                    f"view_distance={computed_distance:.3f}",
                )
    except Exception:
        pass


def _focus_edit_target(context, target_name):
    global _IS_PROGRAMMATIC_EDIT_TARGET_FOCUS

    scene = getattr(context, "scene", None)
    if scene is None or not hasattr(scene, "my_tool"):
        return

    menu = scene.objects.get(target_name)
    if menu is None:
        return

    focus_target = _get_focus_target_object(scene, target_name)
    if focus_target is None:
        return

    _IS_PROGRAMMATIC_EDIT_TARGET_FOCUS = True
    try:
        _deselect_all()
        _set_active(menu)
        menu.select_set(True)

        if _is_plate_view_target(target_name):
            _deselect_all()
            _set_active(focus_target)
            focus_target.select_set(True)
        elif focus_target is not menu:
            focus_target.select_set(True)

        _apply_view_focus(target_name, focus_target)

        if _is_plate_view_target(target_name):
            _deselect_all()
            _set_active(menu)
            menu.select_set(True)
        elif focus_target is not None and focus_target is not menu:
            focus_target.select_set(False)
            _set_active(menu)
    finally:
        _IS_PROGRAMMATIC_EDIT_TARGET_FOCUS = False


def selectItem(self, context):
    name = str(bpy.context.scene.my_tool.my_item)
    _focus_edit_target(bpy.context, name)
    # If the requested target does not exist yet, keep the current selection.
    # This is important for add-state UI such as left/right nurnies, where
    # forcing selection back to BASE makes the panel feel like it needs
    # an extra click before the add controls appear.
