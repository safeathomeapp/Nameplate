## Mirror State Refresh Fix

### Summary
- Fixed the nurnie mirror flow so it mirrors the current live anchor position and scale again.
- The stored anchor-state helper system remained in place, but mirror now refreshes the source anchor snapshot immediately before calculating the mirrored side.

### Files touched
- `src/nameplate_addon/operators.py`
- `docs/Session_notes/2026-03-28_mirror_state_refresh_fix.md`

### Problem
- Mirror was reading cached stored anchor values.
- After manual anchor movement or `instance_faces_scale` changes, the cached values could become stale.
- Result: mirror no longer reflected all axes and scale edits the way the previous behavior did.

### Fix
- In `_mirror_nurnie(side)`, call `store_nurnie_anchor_state(source_anchor)` immediately before reading the source state with `get_nurnie_anchor_state(...)`.
- This preserves the helper-based storage approach while making mirror read the current live anchor state at mirror time.

### Behaviour note
- Intended behavior change: none.
- This was a regression fix so mirror matches expected live behavior again.

### Verification
- `python -m py_compile src/nameplate_addon/operators.py` passed.
- User confirmed in-thread that the updated behavior is good.
