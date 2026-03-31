import bpy

from .constants import BASE_OBJECT, NAMEPLATE_LEGACY_OBJECTS, PATH_OBJECT
from .helpers import (
    _ensure_object_mode,
    _inset_top_face,
    _safe_remove_object,
    _set_active,
    _set_random_viewport_color,
)


def _clear_full_nameplate_scene():
    for name in NAMEPLATE_LEGACY_OBJECTS:
        _safe_remove_object(name)


def drawCBase(self, context):
    _ensure_object_mode()
    _clear_full_nameplate_scene()

    base_size_x = int(bpy.context.scene.my_tool.my_BCIRCLE[1:4])
    base_size_y = int(bpy.context.scene.my_tool.my_BCIRCLE[4:])

    bpy.ops.curve.primitive_bezier_circle_add(radius=base_size_x * 0.5, enter_editmode=False, align='WORLD', location=(0, 0, 0))
    path = bpy.context.active_object
    _set_active(path)
    try:
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.curve.switch_direction()
        bpy.ops.object.mode_set(mode='OBJECT')
    except Exception:
        _ensure_object_mode()
    path.name = PATH_OBJECT

    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=base_size_x * 0.5, depth=4, enter_editmode=False, align='WORLD', location=(0, 0, 2))
    base = bpy.context.active_object
    base.name = BASE_OBJECT
    base.data.name = bpy.context.scene.my_tool.my_BCIRCLE

    try:
        _set_active(base)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_mode(type='FACE')
        bpy.ops.object.mode_set(mode='OBJECT')

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
    _safe_remove_object(PATH_OBJECT)
    _safe_remove_object(BASE_OBJECT)

    base_size_x = int(bpy.context.scene.my_tool.my_BOVAL[1:4])
    base_size_y = int(bpy.context.scene.my_tool.my_BOVAL[4:7])

    bpy.ops.curve.primitive_bezier_circle_add(radius=1, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
    path = bpy.context.active_object
    path.scale[0] = base_size_x * 0.5
    path.scale[1] = base_size_y * 0.5
    _set_active(path)
    try:
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.curve.switch_direction()
        bpy.ops.object.mode_set(mode='OBJECT')
    except Exception:
        _ensure_object_mode()
    path.name = PATH_OBJECT

    bpy.ops.mesh.primitive_cylinder_add(
        vertices=64,
        radius=1.0,
        depth=4.0,
        enter_editmode=False,
        align='WORLD',
        location=(0, 0, 2)
    )
    base = bpy.context.active_object
    base.scale[0] = base_size_x * 0.5
    base.scale[1] = base_size_y * 0.5
    _set_active(base)
    try:
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    except Exception:
        pass

    _inset_top_face(base, (base_size_x - 2) / base_size_x, (base_size_y - 2) / base_size_y)

    base.name = BASE_OBJECT
    base.data.name = bpy.context.scene.my_tool.my_BOVAL

    _set_random_viewport_color()


def drawSBase(self, context):
    _ensure_object_mode()
    _safe_remove_object(PATH_OBJECT)
    _safe_remove_object(BASE_OBJECT)

    base_size_x = int(bpy.context.scene.my_tool.my_BSQUARE[1:4])
    base_size_y = int(bpy.context.scene.my_tool.my_BSQUARE[4:7])

    bpy.ops.curve.primitive_nurbs_path_add(
        radius=base_size_x * 0.25,
        enter_editmode=False,
        align='WORLD',
        location=(0, -base_size_y * 0.5, 0),
        scale=(1, 1, 1)
    )
    bpy.context.active_object.name = PATH_OBJECT

    bpy.ops.mesh.primitive_cube_add(
        enter_editmode=False,
        align='WORLD',
        location=(0, 0, 2),
        scale=(base_size_x * 0.5, base_size_y * 0.5, 2.0)
    )
    base = bpy.context.active_object

    _inset_top_face(base, (base_size_x - 2) / base_size_x, (base_size_y - 2) / base_size_y)

    base.name = BASE_OBJECT
    base.data.name = bpy.context.scene.my_tool.my_BSQUARE

    _set_random_viewport_color()


def drawZBase(self, context):
    _ensure_object_mode()
    _safe_remove_object(PATH_OBJECT)
    _safe_remove_object(BASE_OBJECT)

    base_size_x = int(bpy.context.scene.my_tool.my_BSPECIAL[1:4])
    base_size_y = int(bpy.context.scene.my_tool.my_BSPECIAL[4:7])

    bpy.ops.curve.primitive_bezier_circle_add(radius=base_size_x * 0.5, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
    path = bpy.context.active_object
    _set_active(path)
    try:
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.curve.switch_direction()
        bpy.ops.object.mode_set(mode='OBJECT')
    except Exception:
        _ensure_object_mode()
    path.name = PATH_OBJECT

    bpy.ops.mesh.primitive_cylinder_add(
        vertices=64,
        radius=base_size_x * 0.5,
        depth=4.0,
        enter_editmode=False,
        align='WORLD',
        location=(0, 0, 2)
    )
    base = bpy.context.active_object

    _inset_top_face(base, (base_size_x - 2) / base_size_x, (base_size_x - 2) / base_size_x)

    try:
        _set_active(base)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT')

        for x in range(0, min(16, len(base.data.polygons))):
            base.data.polygons[x].select = True
        for x in range(48, min(62, len(base.data.polygons))):
            base.data.polygons[x].select = True
        for x in range(63, min(65, len(base.data.polygons))):
            base.data.polygons[x].select = True

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.transform.translate(
            value=(0, base_size_y - base_size_x, 0),
            orient_type='GLOBAL',
            constraint_axis=(False, True, False)
        )
        bpy.ops.object.mode_set(mode='OBJECT')
    except Exception:
        _ensure_object_mode()

    base.name = BASE_OBJECT
    base.data.name = bpy.context.scene.my_tool.my_BSPECIAL

    _set_random_viewport_color()
