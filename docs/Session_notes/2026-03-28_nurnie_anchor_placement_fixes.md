## Nurnie Anchor Placement Fixes

### Summary
- Fixed several placement bugs in the nurnie anchor logic after the helper-based refactor work.
- Unified add/change/mirror to use shared base-type-aware anchor placement where appropriate.
- Corrected mirror so it uses stored baked anchor-plane data plus current live anchor state, instead of recomputing from a fresh suggested target.
- Corrected square-base suggested add height after identifying a square-only Z mismatch.

### Files touched
- `src/nameplate_addon/helpers.py`
- `src/nameplate_addon/operators.py`
- `docs/Session_notes/2026-03-28_nurnie_anchor_placement_fixes.md`

### Problems fixed
- Oval add placement was still using the old non-square circle formula in the add operators.
- Oval mirror placement was still using the old direct square-or-not plane formula in `_mirror_nurnie(side)`.
- Mirror after plate resize could place the target nurnie at a fresh suggested target plus the source movement, instead of mirroring from the source anchor’s own stored basis.
- Square-base add placement had a Z offset mismatch and was landing one plate height too high.

### Changes made
- Added/used `_get_nurnie_anchor_location(...)` for explicit base-type-aware suggested anchor placement.
- Added a real `base_type == "L"` branch so oval long-edge bases use `_get_base_curve_data(..., o_angles)` rather than the circle arc-length formula.
- Switched add and change plane creation sites to use the shared helper.
- Switched mirror plane creation sites to use shared base-type-aware placement where needed.
- Extended stored nurnie anchor state to include:
  - `nurnie_plane_x`
  - `nurnie_plane_y`
  - `nurnie_plane_z`
- Added `_mirror_nurnie_plane_location(...)` so mirror derives the target anchor from the source anchor’s baked plane basis rather than recomputing from a new suggested target.
- Adjusted square-base suggested anchor Z so the add position matches expected square behavior again.

### Behaviour note
- Intended behavior change: none.
- These edits were bug fixes to restore expected placement behavior across circle, oval, special, and square bases.

### Verification
- `python -m py_compile src/nameplate_addon/helpers.py src/nameplate_addon/operators.py` passed during the fix cycle.
- User confirmed in-thread that the current placement behavior now tracks correctly.
