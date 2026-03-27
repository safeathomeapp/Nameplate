# Phase 2 Session Note: Plate Generation

Date: 2026-03-27

## 1. Phase summary (what was implemented)

Phase 2 introduces the first generated production-side geometry object:
- `PLATE`

Build now creates:
- `EMPTY`
- `BASE`
- `PATH` when required by the selected base family
- `PLATE`

`PLATE` is managed with the same lifecycle system as the Phase 1 objects:
- canonical object name
- managed custom-property tag
- managed role tag
- clean rebuild replacement
- clean reset removal

## 2. Plate construction method (how geometry is generated)

`PLATE` is generated entirely through the Blender data API as a mesh object.

Current construction approach:
- straight workflows build an extruded rectangular band
- curved workflows build an extruded curved band from a centerline

Geometry rules in this phase:
- simple deterministic footprint
- simple consistent thickness
- no bevels
- no engraving
- no decorative styling

This is intentionally a clean structural plate, not a polished final plate style.

## 3. Relationship to BASE / EMPTY / PATH

`EMPTY`
- created first
- acts as the stable anchor
- generated objects are parented to it

`BASE`
- remains the preset-derived footprint reference
- plate dimensions are derived from the same preset dimension source

`PATH`
- exists only for curved families
- acts as reference only
- is not mutated during plate generation
- curved plate generation uses the same underlying centerline logic as PATH to preserve deterministic alignment

## 4. Coordinate system decisions (explicit)

The coordinate model for this phase is:

- world origin is the build origin
- `EMPTY` is at `(0, 0, 0)`
- `BASE` is centered on that anchor
- `PLATE` is centered on that anchor
- `BASE` occupies the lower reference volume
- `PLATE` begins at the top of `BASE`

Straight families:
- no `PATH`
- plate is a centered rectangular band

Curved families:
- path centerline is generated in local object space
- plate band is built from centerline tangents and lateral offsets
- no viewport-driven placement
- no random offsets
- no PATH transform hacks

## 5. How scale is handled (confirm reuse of Phase 1 rule)

Phase 2 reuses the same centralized scale helper already used by Phase 1:
- `mm_to_scene_units(...)`

That helper is reused for:
- base dimensions
- path extent
- base reference height
- plate thickness
- plate band depth

This keeps `BASE`, `PATH`, and `PLATE` on the same scale rule.

## 6. What is intentionally NOT implemented yet

Still not implemented in Phase 2:
- top plate
- main text
- upper text
- nurnies
- mirror logic
- export logic
- engraving
- decorative edge styling

## 7. Testing instructions

Required beta testing steps:

1. Install or reload the current add-on package in Blender 5.x.
2. Open the `Name Plate` sidebar panel.
3. Test `CIRCLE`, `OVAL`, `SQUARE`, and `SPECIAL` presets.
4. Click `Build References` for each test case.
5. Confirm `PLATE` is created every time.
6. Confirm `PLATE` is named exactly `PLATE`.
7. Confirm `PLATE` is removed and recreated cleanly on repeated builds.
8. Confirm `PLATE` is removed by `Start Over`.
9. Confirm straight families build without `PATH`.
10. Confirm curved families build with `PATH`.
11. Confirm `PLATE` sits consistently above `BASE`.
12. Confirm switching between straight and curved families does not leave stale managed objects behind.
13. Confirm no text objects, top plate objects, or nurnie objects are created.
14. Confirm no console errors occur during normal use.

## 8. Known limitations / future risks

- curved plate output is still a structural placeholder band, not final art direction
- arc coverage is still fixed in this phase
- plate proportions are generic and not yet tuned for the final nameplate look
- no modifier-based bend workflow has been introduced yet
- later text placement and decorative systems will depend on preserving the current coordinate consistency

Main future risk:
- keeping curved placement stable once text, top plate, and side attachments are introduced
