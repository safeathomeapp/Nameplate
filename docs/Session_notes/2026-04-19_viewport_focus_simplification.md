# 2026-04-19 Viewport Focus Simplification

## Files changed

- `src/nameplate_addon/helpers.py`
- `src/nameplate_addon/properties.py`
- `src/nameplate_addon/ui.py`
- `docs/Session_notes/2026-04-19_viewport_focus_simplification.md`

## What changed

- Removed the viewport tuning properties and the extra `Viewport` panel section.
- Kept a minimal automatic viewport behavior on edit-target selection.

## Viewport behavior

- Selecting `PLATE`, `MAINTEXT`, or `UPPERTEXT`:
  - focuses the main `PLATE`
  - switches the 3D view to Blender front view
  - frames the selected object
- Selecting `NURNIE_LEFT` or `NURNIE_RIGHT`:
  - focuses the relevant nurnie object
  - frames the selected object
  - does not force a front view

## Why this version

- It keeps the helpful viewport behavior without adding UI clutter.
- It avoids storing view state or exposing tuning controls.
- It is easier to maintain and easier to remove later if needed.

## Exact Blender test steps

1. Reload the add-on in Blender.
2. Build a plate so the edit-target buttons are available.
3. Click `Nameplate`, `Main Text`, and `Upper Text`.
4. Confirm the viewport snaps to front view and frames the main plate.
5. Click `Left Nurnie` and `Right Nurnie`.
6. Confirm the viewport frames the selected nurnie without forcing front view.
7. Confirm the panel contains no extra viewport controls.

## Assumptions made

- The desired compromise is fixed automatic behavior with no user-facing viewport settings.
