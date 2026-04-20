# 2026-04-20 Persistence Enable Fix

## Files changed

- `src/nameplate_addon/operators.py`
- `docs/Session_notes/2026-04-20_persistence_enable_fix.md`

## What changed

- Fixed an add-on enable/install error introduced during the directory persistence pass.

## Why

- `register()` and `unregister()` used `import bpy.utils.previews` inside function scope.
- In Python that makes `bpy` a local name in the function, which then breaks earlier `bpy...` references with:
  - `cannot access local variable 'bpy' where it is not associated with a value`

## Fix

- Replaced the function-local dotted import with:
  - `from bpy.utils import previews`
- Updated preview collection creation/removal to use `previews.new()` and `previews.remove(...)`.

## Verification

1. Reload or reinstall the add-on in Blender.
2. Confirm the add-on enables without the `local variable 'bpy'` error.
3. Re-test the saved directory persistence flow.

## Assumptions

- No other function-local dotted `bpy...` imports remain in this path.
