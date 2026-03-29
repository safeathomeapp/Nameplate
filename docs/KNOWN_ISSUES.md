# Known Issues

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