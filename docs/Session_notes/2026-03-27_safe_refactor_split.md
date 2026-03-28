## Safe Refactor Split

### Files created
- `src/nameplate_addon/base.py`
- `src/nameplate_addon/plate.py`
- `docs/Session_notes/2026-03-27_safe_refactor_split.md`

### Functions/classes moved
- Moved `drawPlateTrue(...)` into `src/nameplate_addon/plate.py`.
- Moved `drawCBase(...)`, `drawOBase(...)`, `drawSBase(...)`, and `drawZBase(...)` into `src/nameplate_addon/base.py`.
- Moved `italicText`, `unhidenurnieleft`, `unhidenurnieright`, `get_locationZ`, `set_locationZ`, `get_locationY`, `set_locationY`, and `selectItem` into `src/nameplate_addon/helpers.py`.
- Kept supporting shared utility functions in `src/nameplate_addon/helpers.py` so the moved legacy logic still resolves without rewriting operator or geometry behaviour.
- Moved `MyProperties` into `src/nameplate_addon/properties.py`.
- Moved operator logic into `src/nameplate_addon/operators.py`, including import/export operators, nurnie operators, draw/reset/help operators, and preview registration.
- Moved `OBJECT_PT_NamePlate` into `src/nameplate_addon/ui.py`.
- Moved the global `pi` constant into `src/nameplate_addon/constants.py`.

### Imports updated
- Added package-relative imports across the add-on modules.
- `__init__.py` now imports `operators`, `properties`, and `ui`, and delegates registration through those modules.
- `properties.py` now imports update callbacks from `base.py`, `plate.py`, `helpers.py`, and `operators.py`.
- `operators.py` now imports shared helpers from `helpers.py`, `pi` from `constants.py`, and `drawPlateTrue` from `plate.py`.
- `plate.py` now imports `pi` from `constants.py` and shared helper utilities from `helpers.py`.

### Managed object helper scaffolding
- Added `mm`, `set_active`, `get_managed_objects`, and `delete_managed_objects` to `src/nameplate_addon/helpers.py`.
- Added managed-object tags to `PLATE`, `NameplateBase`, `NameplateTop`, `NameplateBottom`, `END_LEFT`, `END_RIGHT`, and `TopBit`.
- Replaced the legacy plate-piece cleanup block in `drawPlateTrue(...)` with `delete_managed_objects()`.

### Whether any behaviour changed
- No behaviour changes were intended.
- `drawPlateTrue(...)` was moved, not rewritten.
- Geometry logic, modifier order, UI layout, object names, and operator IDs were kept aligned with the legacy package split target.
- Blender runtime behaviour was not verified in-app during this session; only a Python syntax compile pass was run.

### Assumptions made
- The current working legacy source of truth is `src/nameplate_generator.py`, and the task was to split that implementation into the package structure from `docs/codex/SAFE_REFACTOR_PLAN.md`.
- The managed-object scaffolding requirement applied to the generated plate-piece objects listed in the refactor plan, not to every scene object created by the add-on.
- Replacing the legacy plate-piece cleanup block with `delete_managed_objects()` was the required structural cleanup change and not a behavioural redesign.

### Exact Blender test steps
1. In Blender, remove any previously installed copy of the add-on.
2. Zip the `src/nameplate_addon` folder or install that folder as the add-on package if using a development install path.
3. Open `Edit > Preferences > Add-ons`, click `Install...`, select the package, and enable `NamePlate Generator`.
4. In the 3D View sidebar, open the `Name Plate` tab.
5. Create a circle base and confirm the UI appears unchanged.
6. Create an oval base and confirm the UI appears unchanged.
7. Create a square base and confirm the UI appears unchanged.
8. Run `Confirm Base Choice` and then build the plate.
9. Verify the generated `PLATE` matches the legacy output visually.
10. Verify object names remain exactly `BASE`, `PATH`, `EMPTY`, `PLATE`, `NameplateBase`, `NameplateTop`, `NameplateBottom`, `END_LEFT`, `END_RIGHT`, and `TopBit` when present.
11. Rebuild the plate and confirm no console errors appear.
12. Test `Start Over`.
13. Test STL export with `Save Your STL`.
14. Test main text and upper text creation and export engraving options.
15. Test left and right nurnie import, mirror, flip, change, and delete flows.
16. Compare modifier order on the generated plate against the legacy add-on and confirm it is unchanged.
