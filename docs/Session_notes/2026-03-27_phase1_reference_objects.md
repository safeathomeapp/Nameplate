# Phase 1 Session Note: Reference Object Creation

Date: 2026-03-27

## Scope Completed

Phase 1 implemented the deterministic reference-object layer only.

Created by build:
- `BASE`
- `EMPTY`
- `PATH` when the selected base family requires a curved workflow

Not implemented in this phase:
- final plate mesh
- top plate mesh
- text objects
- nurnies
- mirror logic
- export logic

## Add-on State

The new add-on package is installed as `nameplate_addon`.

Phase 1 uses a managed-object contract:
- `object["nameplate_managed"] = True`
- `object["nameplate_role"] = "BASE" | "EMPTY" | "PATH"`

Build behaviour:
- rebuilds managed reference objects deterministically
- does not depend on selection
- always creates `BASE`
- always creates `EMPTY`
- only creates `PATH` for curved workflows

Reset behaviour:
- removes only managed add-on objects
- leaves unrelated scene objects untouched
- resets Phase 1 settings back to defaults

## Current PATH Rule

`PATH` is created when `base_family` is:
- `CIRCLE`
- `OVAL`
- `SPECIAL`

`PATH` is not created when `base_family` is:
- `SQUARE`

## Beta Testing Steps

1. Open Blender 5.x and enable the `nameplate_addon` add-on.
2. Confirm the `Name Plate` tab appears in the 3D View sidebar.
3. In a clean scene, click `Build References`.
4. Confirm the Outliner contains `BASE` and `EMPTY`.
5. Confirm `PATH` appears for `CIRCLE`, `OVAL`, and `SPECIAL`.
6. Switch to `SQUARE`, click `Build References`, and confirm `PATH` is not created.
7. Re-run `Build References` several times for different presets and confirm there are no duplicate managed objects left behind.
8. Select several different presets within each family and confirm `BASE` changes size in a readable deterministic way.
9. Confirm `EMPTY` is always recreated at a stable location and keeps the canonical name `EMPTY`.
10. Confirm `PATH` keeps the canonical name `PATH` and is not arbitrarily rotated or scaled by the build.
11. Add unrelated objects to the scene such as a Cube or Empty, then click `Start Over`.
12. Confirm only managed nameplate objects are removed and unrelated objects remain.
13. Confirm no `PLATE`, `MAINTEXT`, `UPPERTEXT`, nurnie objects, or export objects are created during any Phase 1 test.
14. Confirm Blender reports no console errors during normal build and reset use.

## Notes For Next Phase

Next recommended phase:
- build deterministic reference geometry workflows further if needed
- or start plate-construction logic on top of `BASE`, `EMPTY`, and conditional `PATH`

The main Phase 1 acceptance point is that the reference-object layer is now isolated, inspectable, and safe to reset.
