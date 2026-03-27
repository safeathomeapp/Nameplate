# NAMEPLATE GENERATOR — SAFE REFACTOR PLAN (LEGACY → MODULAR)

## Objective

Refactor the existing **working legacy add-on** into a **multi-file Blender add-on package**  
without breaking functionality.

This is a **structural refactor only**.

---

## Critical Rule

> **DO NOT CHANGE BEHAVIOUR**

- Geometry must remain identical
- Operators must behave the same
- UI must behave the same
- Modifier stack must remain unchanged

This refactor is ONLY about:
- file structure
- maintainability
- safety

---

## Why This Refactor Is Required

Single-file add-ons become unmaintainable as complexity grows.

Multi-file Blender add-ons are standard practice:
- Blender treats add-ons as Python packages with `__init__.py`
- Splitting logic improves maintainability, debugging, and scalability

---

## Target Folder Structure

```text
nameplate_addon/
│
├── __init__.py          ← entry point (REQUIRED)
├── constants.py         ← global constants
├── helpers.py           ← shared utility functions
├── properties.py        ← PropertyGroup
├── operators.py         ← operators (draw, reset, export, etc)
├── plate.py             ← drawPlateTrue (UNCHANGED LOGIC)
├── base.py              ← drawCBase, drawOBase, etc
└── ui.py                ← UI panel
```

---

## File Responsibilities (STRICT)

### `plate.py`
Contains:
- `drawPlateTrue(...)`

Rules:
- DO NOT rewrite
- DO NOT optimise
- DO NOT change bpy.ops usage
- MOVE ONLY

This is the **core behaviour system**.

---

### `base.py`
Move:
- `drawCBase(...)`
- `drawOBase(...)`
- `drawSBase(...)`
- `drawZBase(...)`

No logic changes.

---

### `helpers.py`
Move:

- `italicText`
- `unhidenurnieleft/right`
- `get_locationZ`, `set_locationZ`
- `get_locationY`, `set_locationY`
- `selectItem`

Add (new safe helpers):

```python
def mm(val):
    return val * 0.1

def set_active(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

def get_managed_objects():
    return [o for o in bpy.data.objects if o.get("nameplate_managed")]

def delete_managed_objects():
    for o in get_managed_objects():
        bpy.data.objects.remove(o, do_unlink=True)
```

---

### `properties.py`
Move:
- `MyProperties`

No modifications.

---

### `operators.py`
Move:

- `DRAW_OT_my_op`
- `CLEARSCENE_OT_my_op`
- Import/export operators
- Nurnie operators

Update imports to use new module paths.

---

### `ui.py`
Move:
- `OBJECT_PT_NamePlate`

No UI redesign.

---

### `constants.py`
Create new file.

Move:
```python
pi = 3.14159
```

Future use:
- enums
- defaults
- magic numbers (later)

---

## `__init__.py` (MANDATORY STRUCTURE)

Must contain:

- `bl_info`
- `register()`
- `unregister()`
- module imports

Example:

```python
bl_info = {
    "name": "NamePlate Generator",
    "author": "Kev Thomas",
    "version": (2, 0, 0),
    "blender": (5, 0, 0),
    "category": "3D View",
}

from . import properties
from . import operators
from . import ui

def register():
    properties.register()
    operators.register()
    ui.register()

def unregister():
    ui.unregister()
    operators.unregister()
    properties.unregister()
```

---

## Import Rules (IMPORTANT)

Use **relative imports**:

```python
from .plate import drawPlateTrue
from .base import drawCBase
from .helpers import mm
```

Blender requires this structure for multi-file add-ons.

---

## Managed Object System (ADD — NO BEHAVIOUR CHANGE)

When creating objects:

```python
obj["nameplate_managed"] = True
obj["nameplate_role"] = "PLATE"
```

Apply to:
- PLATE
- NameplateBase
- NameplateTop
- NameplateBottom
- END_LEFT / END_RIGHT
- TopBit

Replace manual deletion blocks with:

```python
delete_managed_objects()
```

---

## What MUST NOT Change

Do NOT:

- rewrite `drawPlateTrue`
- change modifier order
- change bend logic
- change numeric values
- change UI layout
- change naming of objects
- replace bpy.ops usage (yet)

---

## What This Refactor Achieves

After completion:

- Codebase becomes modular
- Debugging becomes possible
- Codex can safely modify isolated systems
- Future rewrite becomes controlled instead of chaotic

---

## What This Refactor DOES NOT Do

- Does NOT fix geometry
- Does NOT modernise bpy usage
- Does NOT change behaviour
- Does NOT improve performance

---

## Acceptance Criteria

Refactor is complete only if:

1. Add-on installs successfully
2. UI appears unchanged
3. Plate generation is identical to legacy
4. All operators work
5. Export still works
6. No console errors
7. No missing imports
8. No behavioural regressions

---

## Testing Instructions

1. Install add-on from folder (zip)
2. Enable add-on
3. Create:
   - Circle base
   - Oval base
   - Square base
4. Build plate
5. Compare visually to legacy output
6. Test:
   - rebuild
   - reset
   - export STL
   - text engraving
   - nurnies

---

## Final Rule

> If anything changes visually or behaviourally, the refactor is wrong.

Rollback immediately.

---

## Summary

You are not rewriting the system.

You are:

> **Extracting a stable architecture from a working but fragile codebase**

---

## Next Step (After This Refactor)

Only after this is stable:

1. Introduce safe geometry improvements
2. Replace bend system (if needed)
3. Improve coordinate system
4. Then resume structured rewrite

---

END OF DOCUMENT
