from __future__ import annotations

import math
from typing import Optional

import bpy
from mathutils import Vector

from .constants import (
    BASE_PRESETS,
    BASE_REFERENCE_HEIGHT_MM,
    CURVED_BASE_FAMILIES,
    DEFAULT_SETTINGS,
    MANAGED_TAG,
    MM_TO_SCENE_UNITS,
    OBJECT_NAMES,
    PLATE_BEND_MODIFIER_NAME,
    PLATE_DEPTH_RATIO,
    PLATE_LENGTH_RATIO,
    PLATE_THICKNESS_MM,
    REFERENCE_ROLES,
    ROLE_TAG,
)


def get_settings(context: bpy.types.Context) -> "bpy.types.PropertyGroup":
    return context.scene.nameplate_settings


def get_active_object_name(context: bpy.types.Context) -> str:
    obj = context.active_object
    return obj.name if obj else ""


def scene_object(context: bpy.types.Context, key: str) -> Optional[bpy.types.Object]:
    object_name = OBJECT_NAMES[key]
    return context.scene.objects.get(object_name)


def selected_base_preset(settings: bpy.types.PropertyGroup) -> str:
    family = settings.base_family
    return getattr(settings, f"base_preset_{family.lower()}")


def parse_base_preset_mm(settings: bpy.types.PropertyGroup) -> tuple[float, float]:
    preset_id = selected_base_preset(settings)

    if "x" in preset_id:
        width_text, depth_text = preset_id.split("x", 1)
        return float(width_text), float(depth_text.split("_", 1)[0])

    value = float(preset_id.split("_", 1)[0])
    return value, value


def base_preset_label(settings: bpy.types.PropertyGroup) -> str:
    preset_id = selected_base_preset(settings)
    for item_id, label, _description in BASE_PRESETS[settings.base_family]:
        if item_id == preset_id:
            return label
    return preset_id


def mm_to_scene_units(value_mm: float) -> float:
    # Project convention: preset values are authored in millimeters, but the
    # rewrite uses a 1:1 numeric mapping into Blender scene units for reference geometry.
    return value_mm * MM_TO_SCENE_UNITS


def base_dimensions_m(settings: bpy.types.PropertyGroup) -> tuple[float, float]:
    width_mm, depth_mm = parse_base_preset_mm(settings)
    return mm_to_scene_units(width_mm), mm_to_scene_units(depth_mm)


def path_required(settings: bpy.types.PropertyGroup) -> bool:
    return settings.base_family in CURVED_BASE_FAMILIES


def is_managed_nameplate_object(obj: bpy.types.Object) -> bool:
    return bool(obj.get(MANAGED_TAG))


def object_role(obj: bpy.types.Object) -> str:
    return str(obj.get(ROLE_TAG, ""))


def managed_object_by_role(
    context: bpy.types.Context, role: str
) -> Optional[bpy.types.Object]:
    canonical_name = next(
        (name for name in OBJECT_NAMES.values() if name == role),
        role,
    )
    obj = context.scene.objects.get(canonical_name)
    if obj and is_managed_nameplate_object(obj):
        return obj

    for candidate in context.scene.objects:
        if is_managed_nameplate_object(candidate) and object_role(candidate) == role:
            return candidate
    return None


def list_managed_objects(context: bpy.types.Context) -> list[bpy.types.Object]:
    managed = []
    canonical_names = set(OBJECT_NAMES.values())
    for obj in context.scene.objects:
        if is_managed_nameplate_object(obj):
            managed.append(obj)
            continue
        if obj.name in canonical_names and object_role(obj) in REFERENCE_ROLES:
            managed.append(obj)
    return managed


def remove_object_data_if_unused(data) -> None:
    if data is None or data.users > 0:
        return

    if isinstance(data, bpy.types.Mesh):
        bpy.data.meshes.remove(data)
    elif isinstance(data, bpy.types.Curve):
        bpy.data.curves.remove(data)


def delete_managed_objects(context: bpy.types.Context) -> list[str]:
    removed_names = []
    managed_objects = list_managed_objects(context)
    for obj in managed_objects:
        removed_names.append(obj.name)
        data = obj.data
        bpy.data.objects.remove(obj, do_unlink=True)
        remove_object_data_if_unused(data)
    return removed_names


def ensure_collection_link(
    context: bpy.types.Context, obj: bpy.types.Object
) -> bpy.types.Object:
    if context.scene.collection.objects.get(obj.name) is None:
        context.scene.collection.objects.link(obj)
    return obj


def tag_managed_object(obj: bpy.types.Object, role: str) -> bpy.types.Object:
    obj.name = role
    obj[MANAGED_TAG] = True
    obj[ROLE_TAG] = role
    return obj


def create_empty_object(context: bpy.types.Context) -> bpy.types.Object:
    empty = bpy.data.objects.new(OBJECT_NAMES["empty"], None)
    ensure_collection_link(context, empty)
    tag_managed_object(empty, "EMPTY")
    empty.empty_display_type = "PLAIN_AXES"
    empty.empty_display_size = mm_to_scene_units(5.0)
    empty.location = (0.0, 0.0, 0.0)
    return empty


def create_base_object(
    context: bpy.types.Context, settings, parent: Optional[bpy.types.Object] = None
) -> bpy.types.Object:
    mesh = bpy.data.meshes.new("BASE_MESH")
    base = bpy.data.objects.new(OBJECT_NAMES["base"], mesh)
    ensure_collection_link(context, base)
    tag_managed_object(base, "BASE")
    base.location = (0.0, 0.0, 0.0)
    base.parent = parent

    width_m, depth_m = base_dimensions_m(settings)
    verts, faces = build_base_mesh(settings.base_family, width_m, depth_m)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    return base


def create_path_object(
    context: bpy.types.Context, settings, parent: Optional[bpy.types.Object] = None
) -> Optional[bpy.types.Object]:
    if not path_required(settings):
        return None

    curve = bpy.data.curves.new("PATH_CURVE", type="CURVE")
    curve.dimensions = "3D"
    spline = curve.splines.new("NURBS")
    points = build_path_points(settings)
    spline.points.add(len(points) - 1)
    for index, point in enumerate(points):
        spline.points[index].co = (point.x, point.y, point.z, 1.0)
    spline.order_u = min(4, len(spline.points))
    spline.use_endpoint_u = True

    path = bpy.data.objects.new(OBJECT_NAMES["path"], curve)
    ensure_collection_link(context, path)
    tag_managed_object(path, "PATH")
    path.location = (0.0, 0.0, 0.0)
    path.parent = parent
    return path


def create_plate_object(
    context: bpy.types.Context, settings, parent: Optional[bpy.types.Object] = None
) -> bpy.types.Object:
    mesh = bpy.data.meshes.new("PLATE_MESH")
    plate = bpy.data.objects.new(OBJECT_NAMES["plate"], mesh)
    ensure_collection_link(context, plate)
    tag_managed_object(plate, "PLATE")
    plate.location = (0.0, 0.0, 0.0)
    plate.parent = parent

    width_m, depth_m = base_dimensions_m(settings)
    verts, faces = build_plate_mesh(settings, width_m, depth_m)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    if path_required(settings) and parent is not None:
        configure_plate_bend_modifier(plate, parent, curved_plate_bend_angle(settings))
    return plate


def build_base_mesh(
    base_family: str, width_m: float, depth_m: float
) -> tuple[list[tuple[float, float, float]], list[tuple[int, ...]]]:
    height_m = base_reference_height()
    if base_family in {"CIRCLE", "OVAL", "SPECIAL"}:
        return extruded_ellipse_mesh(width_m, depth_m, height_m, segments=48)
    return extruded_rectangle_mesh(width_m, depth_m, height_m)


def extruded_rectangle_mesh(
    width_m: float, depth_m: float, height_m: float, z_offset: float = 0.0
) -> tuple[list[tuple[float, float, float]], list[tuple[int, ...]]]:
    hx = width_m / 2.0
    hy = depth_m / 2.0
    z0 = z_offset
    z1 = z_offset + height_m
    verts = [
        (-hx, -hy, z0),
        (hx, -hy, z0),
        (hx, hy, z0),
        (-hx, hy, z0),
        (-hx, -hy, z1),
        (hx, -hy, z1),
        (hx, hy, z1),
        (-hx, hy, z1),
    ]
    faces = [
        (0, 1, 2, 3),
        (4, 7, 6, 5),
        (0, 4, 5, 1),
        (1, 5, 6, 2),
        (2, 6, 7, 3),
        (3, 7, 4, 0),
    ]
    return verts, faces


def extruded_ellipse_mesh(
    width_m: float, depth_m: float, height_m: float, segments: int
) -> tuple[list[tuple[float, float, float]], list[tuple[int, ...]]]:
    rx = width_m / 2.0
    ry = depth_m / 2.0
    bottom = []
    top = []
    for index in range(segments):
        angle = (math.tau * index) / segments
        x = math.cos(angle) * rx
        y = math.sin(angle) * ry
        bottom.append((x, y, 0.0))
        top.append((x, y, height_m))

    verts = bottom + top
    faces = [tuple(range(segments))]
    faces.append(tuple(range((segments * 2) - 1, segments - 1, -1)))
    for index in range(segments):
        next_index = (index + 1) % segments
        faces.append(
            (
                index,
                next_index,
                segments + next_index,
                segments + index,
            )
        )
    return verts, faces


def base_reference_height() -> float:
    return mm_to_scene_units(BASE_REFERENCE_HEIGHT_MM)


def plate_thickness() -> float:
    return mm_to_scene_units(PLATE_THICKNESS_MM)


def plate_band_depth(depth_m: float) -> float:
    return max(mm_to_scene_units(8.0), depth_m * PLATE_DEPTH_RATIO)


def plate_span_length(width_m: float) -> float:
    return width_m * PLATE_LENGTH_RATIO


def build_plate_mesh(
    settings, width_m: float, depth_m: float
) -> tuple[list[tuple[float, float, float]], list[tuple[int, ...]]]:
    if path_required(settings):
        return build_curved_plate_mesh(settings, width_m, depth_m)
    return build_straight_plate_mesh(width_m, depth_m)


def build_straight_plate_mesh(
    width_m: float, depth_m: float
) -> tuple[list[tuple[float, float, float]], list[tuple[int, ...]]]:
    z0 = base_reference_height()
    plate_width = plate_span_length(width_m)
    plate_depth = plate_band_depth(depth_m)
    return extruded_rectangle_mesh(
        plate_width,
        plate_depth,
        plate_thickness(),
        z_offset=z0,
    )


def build_curved_plate_mesh(
    settings, width_m: float, depth_m: float
) -> tuple[list[tuple[float, float, float]], list[tuple[int, ...]]]:
    strip_length = curved_strip_length(settings, width_m, depth_m)
    strip_depth = plate_band_depth(depth_m)
    return extruded_rectangle_mesh(
        strip_length,
        strip_depth,
        plate_thickness(),
        z_offset=base_reference_height(),
    )


def build_path_points(settings) -> list[Vector]:
    width_m, depth_m = base_dimensions_m(settings)

    if settings.base_family in {"CIRCLE", "SPECIAL"}:
        radius = max(width_m, depth_m) / 2.0
        return arc_points(radius_x=radius, radius_y=radius, angle_degrees=120.0)

    return arc_points(
        radius_x=width_m / 2.0,
        radius_y=depth_m / 2.0,
        angle_degrees=120.0,
    )


def arc_points(radius_x: float, radius_y: float, angle_degrees: float) -> list[Vector]:
    segments = 12
    angle_radians = math.radians(angle_degrees)
    start = (math.pi / 2.0) + (angle_radians / 2.0)
    points = []
    for index in range(segments + 1):
        blend = index / segments
        angle = start - (blend * angle_radians)
        points.append(Vector((math.cos(angle) * radius_x, math.sin(angle) * radius_y, 0.0)))
    return points


def curve_tangent(points: list[Vector], index: int) -> Vector:
    if index == 0:
        tangent = points[1] - points[0]
    elif index == len(points) - 1:
        tangent = points[-1] - points[-2]
    else:
        tangent = points[index + 1] - points[index - 1]
    return tangent.normalized() if tangent.length != 0.0 else Vector((1.0, 0.0, 0.0))


def curved_plate_arc_angle(settings) -> float:
    width_mm, _depth_mm = parse_base_preset_mm(settings)
    if settings.base_family == "OVAL":
        if width_mm <= 75.0:
            return 90.0
        if width_mm <= 120.0:
            return 120.0
        return 135.0

    if width_mm <= 40.0:
        return 90.0
    if width_mm <= 80.0:
        return 120.0
    if width_mm <= 130.0:
        return 150.0
    return 180.0


def curved_plate_bend_angle(settings) -> float:
    return math.radians(curved_plate_arc_angle(settings))


def curved_plate_reference_radius(settings, width_m: float, depth_m: float) -> float:
    if settings.base_family == "OVAL":
        return width_m * 0.5
    return max(width_m, depth_m) * 0.5


def curved_strip_length(settings, width_m: float, depth_m: float) -> float:
    radius = curved_plate_reference_radius(settings, width_m, depth_m)
    return radius * curved_plate_bend_angle(settings)


def configure_plate_bend_modifier(
    plate: bpy.types.Object, anchor: bpy.types.Object, bend_angle: float
) -> None:
    bend = plate.modifiers.new(name=PLATE_BEND_MODIFIER_NAME, type="SIMPLE_DEFORM")
    bend.deform_method = "BEND"
    bend.deform_axis = "Z"
    bend.origin = anchor
    bend.angle = bend_angle


def workflow_summary(settings: bpy.types.PropertyGroup) -> str:
    return (
        f"{settings.workflow_mode} | "
        f"{settings.base_family}:{base_preset_label(settings)} | "
        f"path={'yes' if path_required(settings) else 'no'}"
    )


def tag_view_layer_for_update(context: bpy.types.Context) -> None:
    if context.view_layer is not None:
        context.view_layer.update()


def reset_settings(settings: bpy.types.PropertyGroup) -> None:
    for key, value in DEFAULT_SETTINGS.items():
        setattr(settings, key, value)
