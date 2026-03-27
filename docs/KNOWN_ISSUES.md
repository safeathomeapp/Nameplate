# Known Issues

## Mirror Behaviour (Curved Bases)

Mirroring nurnies on curved plates is not fully reliable.

Symptoms:
- Mirrored nurnie may appear on incorrect side of the path
- Behaviour may break after changing arc (`angles`)
- Placement is not consistently symmetrical

Status:
- Under active investigation
- Root cause likely tied to path-relative positioning vs object transforms

---

## UI State After Deletion

After deleting a nurnie:
- The UI panel may not immediately revert to the “Add Nurnie” state
- Requires re-selecting the nurnie tool to refresh

Status:
- Known side-effect of recent UI condition changes
- Will be addressed during full UI refactor

---

## Context Sensitivity (`bpy.ops`)

Some operations depend on:
- active object
- selection state
- mode (OBJECT / EDIT)

This can lead to:
- inconsistent behaviour
- hard-to-trace bugs

Status:
- Gradual migration to safer patterns planned

---

## Legacy Naming / Structure

- Inconsistent naming conventions
- Mixed responsibilities in functions
- Historical duplication of logic

Status:
- Being refactored incrementally
- Not yet fully standardized

---

## General Note

This project is under active refactor.

Issues are expected during transition from Blender 2.91 → 5.x.