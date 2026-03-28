## Nurnie Anchor State Helpers

### Summary
- Added explicit helper functions to store and read left/right nurnie anchor state.
- Updated add, change, and mirror flows to use stored anchor coordinates instead of relying only on live object transforms as the reference source.
- Kept the legacy nurnie placement flow intact and only introduced explicit state capture around it.

### Files touched
- `.gitignore`
- `src/nameplate_addon/helpers.py`
- `src/nameplate_addon/operators.py`
- `docs/Session_notes/2026-03-28_nurnie_anchor_state_helpers.md`

### Helpers added
- `store_nurnie_anchor_state(obj)`
- `get_nurnie_anchor_state(obj)`

### Stored fields
- `nurnie_anchor_x`
- `nurnie_anchor_y`
- `nurnie_anchor_z`
- `nurnie_scale`

### Integration points
- `ADDNURNIELEFT_OT_my_op`
- `ADDNURNIERIGHT_OT_my_op`
- `CHANGENURNIELEFT_OT_my_op`
- `CHANGENURNIERIGHT_OT_my_op`
- `_mirror_nurnie(side)`

### Behaviour note
- Intended behavior change: none.
- The purpose was to make mirror/reference logic easier to reason about and less dependent on ad hoc coordinate reconstruction.
- Mirror still follows the legacy placement flow; the source coordinates now come from stored anchor state.

### Verification
- `python -m py_compile` passed for the updated helper and operator modules.
- User-reported in-thread verification: current behavior appears to work correctly.

### Follow-on cleanup opportunity
- Move repeated nurnie anchor setup code into one or two narrowly scoped helper functions without changing operator ids, object names, or placement rules.
