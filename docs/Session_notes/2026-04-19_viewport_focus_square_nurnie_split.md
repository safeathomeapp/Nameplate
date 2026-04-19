# 2026-04-19 Viewport Focus Square Nurnie Split

## Files changed

- `src/nameplate_addon/helpers.py`
- `docs/Session_notes/2026-04-19_viewport_focus_square_nurnie_split.md`

## What changed

- Split nurnie viewport behavior by base type.
- Curved-style bases keep the angled nurnie view.
- Square bases now use a flatter front-style nurnie view.

## Behavior

- `PLATE`, `MAINTEXT`, `UPPERTEXT`
  - front view
  - slight top-down tilt
  - perspective
  - pivot-aware distance formula
- `NURNIE_LEFT`, `NURNIE_RIGHT` on circle / oval / special style bases
  - front-based perspective
  - slight top-down tilt
  - mirrored side turn
  - orbit centered on `0,0,0`
  - distance based on base span plus nurnie size/offset
- `NURNIE_LEFT`, `NURNIE_RIGHT` on square bases
  - front-based perspective
  - slight top-down tilt
  - no mirrored side turn
  - no forced orbit-center recentering
  - same distance formula as other nurnie views

## Why

- On square bases, the nurnies sit on the same plane as the plate/text.
- The curved-base angled nurnie presentation skews that layout visually.
- A flatter front-style view better matches the square-base arrangement.

## Verification

1. Reload the add-on in Blender.
2. Test `Left Nurnie` and `Right Nurnie` on a curved base.
3. Confirm the angled mirrored view still applies.
4. Test `Left Nurnie` and `Right Nurnie` on a square base.
5. Confirm the viewport uses the flatter front-style view instead of the curved-base orbit angle.
6. Confirm plate/text focus behavior remains unchanged.

## Assumptions

- `BASE.data.name[:1] == "S"` remains the correct discriminator for square-base behavior.
