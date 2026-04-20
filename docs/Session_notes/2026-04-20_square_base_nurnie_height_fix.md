# 2026-04-20 Square Base Nurnie Height Fix

## Files changed

- `src/nameplate_addon/operators.py`
- `docs/Session_notes/2026-04-20_square_base_nurnie_height_fix.md`

## What changed

- Fixed square-base nurnie start height so it tracks plate height correctly.
- Fixed square-base anchor-plane creation so the square seed location is not baked into plane mesh data before the anchor is rotated.

## Scope

- This change is limited to square bases only.
- Circle, oval, and special-base nurnie behavior is intentionally unchanged.

## Root cause

- The square branch was seeding `z` with the wrong sign.
- Square anchor planes were also applying object location during setup, which baked the seed offset into the plane mesh and then rotated that baked offset around object origin.
- That caused visible height drift as square base size changed.

## Behavior

- Square-base nurnies now seed with:
  - `z = plate_height * 0.5`
  - positive half-height
- Square-base anchor planes now keep their seeded object-space location during creation.

## Verification

1. Reload the add-on in Blender.
2. Test square bases at `25mm`, `32mm`, `40mm`, and `50mm`.
3. Add a nurnie on each and confirm height no longer drifts with square base size.
4. Confirm a `4mm` plate seeds square nurnies at `+2mm` height.
5. Add nurnies on circle, oval, and special bases and confirm those flows are unchanged.

## Assumptions

- Square-base height should depend on plate height, not square base size.
- Existing curved-base behavior is already correct and should remain untouched.
