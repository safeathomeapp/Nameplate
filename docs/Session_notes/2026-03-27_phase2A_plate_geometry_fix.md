# Phase 2A Session Note: Plate Geometry Fix

Date: 2026-03-27

## 1. Problem with previous geometry (why it was wrong)

The previous curved `PLATE` geometry was generated as a swept filled form based on a centerline band.

That produced the wrong visual/model category for curved plates:
- it read like a wedge / filled curved slab
- it did not express a clean ring-segment plate with a true inner gap

For a proper curved nameplate base, the mesh needed:
- an outer curved boundary
- an inner curved boundary
- explicit side caps
- a real band profile instead of a filled sector-like mass

## 2. New geometric model (ring segment)

Curved `PLATE` is now generated as a ring segment.

Construction method:
- sample angles across the selected arc span
- generate outer arc vertices with polar coordinates
- generate inner arc vertices with polar coordinates
- build bottom and top loops
- connect loops with quads for:
  - outer wall
  - inner wall
  - top face
  - bottom face
  - start cap
  - end cap

Straight families remain unchanged and still use a rectangular band.

## 3. Parameters used (outer radius, inner radius, arc angle, height)

Current curved plate parameters:

- outer radius:
  - circle/special: `max(width, depth) / 2`
  - oval: concentric outer X/Y radii from the preset footprint
- inner radius:
  - outer radius minus band depth
  - clamped to avoid collapse
- arc angle:
  - currently derived from preset size bands
  - circle/special use stepped values from the existing angle set
  - oval uses stepped values from the oval angle set
- height:
  - plate starts at the top of `BASE`
  - plate height uses the centralized Phase scale helper and current `PLATE_THICKNESS_MM`

## 4. How taper is handled (if implemented)

Taper is not implemented in this phase.

Current walls are vertical and concentric.
This keeps the fix narrow and easy to validate.

## 5. Relationship to PATH (if any)

`PATH` is not mutated and is still treated as reference-only.

Relationship:
- curved `PLATE` is generated directly with polar coordinates rather than by deforming around `PATH`
- Phase 2A does not change existing `PATH` creation logic

So `PATH` remains part of the curved architecture, but the mesh no longer depends on a wedge-like centerline sweep.

## 6. Testing instructions

Required beta testing:

1. Reload or reinstall the add-on in Blender 5.x.
2. Test curved families: `CIRCLE`, `OVAL`, and `SPECIAL`.
3. Click `Build References`.
4. Confirm `PLATE` is visibly a band with an inner gap, not a solid curved wedge.
5. Confirm outer and inner curves are concentric.
6. Confirm the start and end caps close the ring segment cleanly.
7. Confirm `PLATE` still sits consistently above `BASE`.
8. Confirm `PATH` still appears only for curved families.
9. Confirm `SQUARE` still builds the straight rectangular plate.
10. Rebuild several times and confirm no duplicate managed objects remain.
11. Click `Start Over` and confirm `PLATE` is removed cleanly.
12. Confirm no extra objects, text, or nurnies are created.
13. Confirm no console errors occur.

## 7. Known limitations

- taper is not implemented yet
- curved plate proportions are still generic
- curved plate arc selection is preset-banded and not user-configurable yet
- `PATH` still uses its prior Phase 2 behavior and is not yet fully harmonized with curved plate arc selection
- oval curved output uses concentric elliptical radii but is still intentionally simple
- no beveling, engraving, or decorative shaping exists yet
