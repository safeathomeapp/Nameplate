# Session Note: Boolean Solver Manifold Pass

Date: 2026-03-30
Branch: `refactor/legacy-to-modular-v1`

## Summary

This pass changed the export boolean solver from Blender 5-compatible `EXACT` to `MANIFOLD` for:

- FOV subtraction
- main text engraving
- upper text engraving

The reason for the experiment was performance:

- legacy `FAST` is no longer available in Blender 5
- `EXACT` restored correct export behavior but was noticeably slow
- `MANIFOLD` was tested as the next best modern solver option

## Files Created

- `docs/Session_notes/2026-03-30_boolean_solver_manifold_pass.md`

## Files Updated

- `src/nameplate_addon/operators.py`

## Changes Made

Updated the export boolean solver from:

- `EXACT`

to:

- `MANIFOLD`

in the three export boolean applications:

- plate minus `FOV`
- plate minus `MAINTEXTBOOL`
- plate minus `UPPERTEXTBOOL`

## Behavior Change

Intended behavior change:

- export booleans should remain clean
- export speed should improve compared with `EXACT`

## Validation

- `python -m py_compile src/nameplate_addon/operators.py`
- Blender beta test passed:
  - `MANIFOLD` produced clean booleans for this task
  - export speed improved substantially versus `EXACT`
  - user-reported performance gain was approximately 100%

## Exact Beta-Test Result

Observed outcome from Blender testing:

1. `FOV` boolean remained clean.
2. Main text engraving remained clean.
3. Upper text engraving remained clean.
4. Export speed increased significantly compared with `EXACT`.

## Conclusion

For the current nameplate export geometry, `MANIFOLD` is the preferred Blender 5 solver choice over `EXACT`.

## Next Recommended Step

Next tidy/hardening pass should focus on the remaining one-off export realization path around `SETNURNIERIGHT_OT_my_op` and related temporary-object cleanup comments/helpers.
