# 2026-04-21 Datum Normalisation TODO

## Current Checkpoint

- The base and `PATH` generation are treated as correct and should stay unchanged.
- The plate now builds from the path/contact datum instead of being shifted after construction.
- The plate origin is set to the path/contact datum before applying the fixed 15 degree tilt.
- The top and bottom border strips are offset from the main plate's outer face rather than directly from the path datum.

## Product-Wide Datum Goal

All generated/editable parts should follow the same pattern:

1. Build or import the geometry in a known, measurable state.
2. Determine the semantic contact datum for that object.
3. Set or compensate the origin against that datum.
4. Apply the 15 degree tilt from the datum.
5. Apply user movement along local axes, not raw global axes.

## Text Normalisation

- Review `MAINTEXT` and `UPPERTEXT` creation in `operators.py`.
- Replace hard-coded world placement where possible with placement relative to the plate datum.
- Define the text contact datum:
  - likely the centre of the text object's plate-facing/back contact plane.
- Account for text bounds after font, size, body, alignment, and extrusion are applied.
- Keep user movement sliders local-axis based.
- Confirm text remains visually consistent when:
  - plate height changes
  - text content changes
  - font changes
  - upper/top plate settings change
  - square/curved/special base type changes

## Nurnie Normalisation

- Review `NURNIE_LEFT`, `NURNIE_RIGHT`, `NUR_LEFT`, and `NUR_RIGHT` setup in `operators.py`.
- Define the nurnie contact datum:
  - likely the centre of the imported STL's plate-facing/back mounting plane.
- Imported STL origins cannot be trusted; use mesh bounds or a deliberate normalisation pass.
- Preserve manual edit state through change/mirror/delete flows.
- Apply or preserve 15 degree tilt from the contact datum.
- Keep user movement sliders local-axis based.
- Confirm nurnie placement remains consistent when:
  - plate height changes
  - nurnie STL shape/size changes
  - nurnie is changed after manual positioning
  - nurnie is mirrored
  - square/curved/special base type changes

## Risks

- Text and nurnies currently rely on legacy hard-coded positions, Curve modifiers, text data offsets, and instancing behavior.
- Fixing datum behavior in one path may expose hidden assumptions in export, mirror, or change flows.
- Changes should be made one workflow at a time and checked in Blender after each step.
