# Phase 2B Session Note: Bent Strip Plate

Date: 2026-03-27

## 1. Phase summary

Phase 2B replaces the curved `PLATE` geometry model with the legacy-correct behavioural contract:

- build a straight strip body
- bend that strip around `EMPTY`

This replaces the prior curved plate approach that generated curved geometry directly.

Current result:
- straight families still use direct straight plate generation
- curved families now use straight strip generation plus explicit bend configuration

## 2. Legacy behavioural contract being implemented

The legacy curved plate is not fundamentally a ring sector.

The behavioural contract extracted from the legacy add-on is:
- derive a usable straight strip length from preset/base logic
- build a straight plate body
- bend the straight body around a canonical anchor
- keep `PATH` separate from the primary plate curvature mechanism

That is what Phase 2B now implements.

## 3. Straight plate construction model

The current straight strip body is intentionally simple:
- one rectangular strip body
- deterministic width/length/height
- no decorative layering yet

For straight families:
- plate width uses the existing straight plate ratio logic
- plate depth uses the centralized band-depth helper
- plate sits on top of `BASE`

For curved families before bend:
- the pre-bend plate is also just a straight rectangular strip
- its strip length is derived from:
  - preset-driven bend angle
  - reference radius derived from preset/base dimensions

## 4. Bend model and anchor rule

Curved plate bending is explicit and deterministic.

Current bend rule:
- `EMPTY` is the bend anchor
- curved `PLATE` gets a `SimpleDeform` bend modifier
- modifier origin is explicitly set to `EMPTY`
- bend axis is explicitly set to `Z`
- bend angle is derived from preset-banded curved angle logic

Important coordinate rule:
- the pre-bend strip is built centered in local space
- `EMPTY` remains at the anchor location
- no cursor-based origin tricks are used
- no post-hoc rotation hacks are used

## 5. Relationship between `EMPTY`, `BASE`, `PLATE`, and `PATH`

`EMPTY`
- canonical bend anchor
- parent anchor for generated managed objects

`BASE`
- footprint/reference object
- plate sits above its top surface

`PLATE`
- straight rectangular strip for straight families
- straight rectangular strip plus bend modifier for curved families

`PATH`
- still exists for curved workflows
- is not the primary curvature source for `PLATE`
- remains available for later systems such as text/attachments

## 6. What legacy patterns were intentionally NOT copied

Intentionally discarded:
- `bpy.ops`-heavy geometry choreography
- cursor-dependent origin setting
- active-object / selection assumptions
- rotate-to-fix placement logic
- scattered magic offsets
- implicit plate behaviour caused by context state

## 7. Testing instructions

Required beta testing guidelines:

1. Re-zip and reload the add-on in Blender 5.x.
2. Test curved families: `CIRCLE`, `OVAL`, and `SPECIAL`.
3. Click `Build References`.
4. Confirm curved `PLATE` is no longer wedge/ring-sector geometry.
5. Confirm curved `PLATE` reads as a bent strip body.
6. Confirm `PLATE` has a `SimpleDeform` bend modifier.
7. Confirm the bend modifier origin is `EMPTY`.
8. Confirm `PATH` still exists for curved families but is not required for the plate shape itself.
9. Test `SQUARE` and confirm straight plate generation still works.
10. Rebuild multiple times and confirm there are no duplicate managed objects.
11. Click `Start Over` and confirm `PLATE` is removed cleanly.
12. Confirm no top plate, text, or nurnie objects are created.
13. Confirm no console errors occur.

## 8. Known limitations / future risks

- curved plate is currently a single bent strip body, not yet layered like the full legacy plate
- no end-cap styling yet
- no top-plate layering yet
- bend-angle logic is still preset-banded and intentionally simple
- oval/special curvature currently uses a simplified reference-radius model
- later phases will still need to decide how much of the legacy layered silhouette to preserve before text and ornament systems are added
