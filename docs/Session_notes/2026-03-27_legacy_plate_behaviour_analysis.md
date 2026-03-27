# Legacy Plate Behaviour Analysis

Date: 2026-03-27

## 1. Legacy files inspected

Inspected:
- `src/nameplate_generator.py`
- `legacy/blender_2_91/nameplate_generator_2_91.py`

Primary sections inspected:
- `drawPlateTrue(...)`
- `drawCBase(...)`
- `drawOBase(...)`
- `drawSBase(...)`
- `drawZBase(...)`
- setup/operator code that creates `EMPTY` before calling `drawPlateTrue(...)`
- helper `_get_base_curve_data(...)` in the newer legacy-derived script

## 2. Legacy functions/classes involved in plate generation

Core plate-generation functions:
- `drawPlateTrue(...)`

Reference/base setup functions that affect plate behaviour:
- `drawCBase(...)`
- `drawOBase(...)`
- `drawSBase(...)`
- `drawZBase(...)`

Support helpers affecting plate shape:
- `_get_base_curve_data(...)`
- `_bevel_end_cap_profile(...)`
- `_bevel_top_plate_profile(...)`

Anchor/setup logic affecting bend origin:
- operator code that creates `EMPTY` before plate build

## 3. Which function appears to be the true source of curved plate geometry

The true source of curved plate geometry is `drawPlateTrue(...)`.

Important finding:
- the curved plate is not directly modeled as a ring segment
- it is first built as a straight assembly of cubes
- then the joined mesh is bent with a `SimpleDeform` bend modifier

So the real legacy geometric contract is:
- build straight strip components
- join them
- tilt them
- bend them around `EMPTY`

That bend step, not `PATH`, is what actually creates the curved plate shape.

## 4. Exact behavioural findings

### Object orientation

Legacy plate orientation is not purely geometric; it is partly procedural and partly hacky.

Observed behaviour:
- plate components are created as world-aligned cubes
- after joining, the resulting `PLATE` is tilted on X
- in the 2.91 file this is done with a rotate operator
- in the newer derived script this is forced directly through Euler assignment to approximately `-15` degrees on X

Meaning:
- the plate is intentionally not left flat in world axes
- the tilt is part of the display/working orientation before or during bend usage

### Origin point / anchor logic

The bend origin is `EMPTY`.

Observed behaviour:
- `EMPTY` is created before `drawPlateTrue(...)`
- for most base types it is placed at `(0, -base_size_y * 0.5, 0)`
- for special `Z` bases it uses `(0, -base_size_x * 0.5, 0)`
- `SimpleDeform.origin` is assigned to `EMPTY`
- scene cursor is also moved to `(0, -base_size_y * 0.5, 0)` before origin-set on `PLATE`

Meaning:
- the bend anchor is intentionally offset backward in Y
- the plate is not centered on world origin for its bend model
- `EMPTY` is the canonical curved plate anchor in the legacy system

### Footprint definition

The plate footprint is defined from a straight strip length called `user_x`, not from direct ring radii.

Observed behaviour:
- `user_x` is calculated from arc-length-style logic for curved families
- then reduced by `end_length * 2`
- the main body is created as `NameplateBase`, a cube scaled to `(user_x, user_y, user_z)`
- top and bottom border strips are separate cubes
- left and right end caps are separate cubes added at the ends of the strip

Meaning:
- the legacy plate is fundamentally a straight segmented strip before deformation
- the “footprint” is straight-first, bend-later

### Outer vs inner boundary logic

There is no explicit inner-vs-outer ring boundary model in the legacy plate builder.

Observed behaviour:
- the plate is a solid joined strip of cuboids
- curvature comes from bending that whole strip mesh
- inner and outer curved boundaries are emergent results of the bend modifier, not explicitly authored concentric curves

Meaning:
- if the rewrite wants behavioural fidelity, the main thing to preserve is the final band-like bent strip look
- direct ring construction is a rewrite choice, not a legacy construction method

### Taper / sidewall logic

No true tapered wall profile was found in the core curved plate generation.

Observed behaviour:
- main body uses simple cubes
- borders use simple cubes
- end caps may be beveled/chamfered/slanted at selected profile edges
- no evidence of a global radial wall taper in `drawPlateTrue(...)`

Meaning:
- sidewall taper is not a core legacy curved-plate rule
- end-profile styling exists, but global tapered ring walls do not appear to be the defining geometry

### Top face logic

The top face is layered, not monolithic.

Observed behaviour:
- `NameplateTop` and `NameplateBottom` are thin border strips
- optional `TopBit` sits on or partially into the main plate depending on the toggle
- `TopBit` uses its own length fraction (`top_panel_curve`) and end-style treatment

Meaning:
- the final plate silhouette is built from stacked strip components
- the “top face” footprint is partially governed by additional layered pieces, not just the main body volume

### Arc-angle logic

Arc control is converted into straight strip length and bend angle.

Observed behaviour:
- circle/special:
  - `angles` becomes `circle_curve = enum * 0.01`
  - arc length = circumference * curve fraction
  - bend angle = arc_length / radius
- oval/lobed:
  - pre-authored curve metadata tables provide both usable strip length and bend angle
- square:
  - bend angle is zero

Meaning:
- the legacy system thinks in terms of:
  - usable straight length
  - then bend that length into the target arc
- this is the main curved-plate contract

### Any dependency on PATH or text objects

`PATH` is not the primary curved plate generator.

Observed behaviour:
- plate bending uses `SimpleDeform` around `EMPTY`
- `PATH` is used heavily by text and nurnie systems
- curved text uses curve modifiers against `PATH`
- plate generation itself does not depend on `PATH` to create the curved mesh

Meaning:
- `PATH` is important to the overall add-on architecture
- but `PLATE` curvature comes from bend deformation, not path deformation

## 5. Legacy hacks or unstable patterns that must NOT be copied

Patterns that should not be copied into the rewrite:
- heavy reliance on `bpy.ops` for every geometry step
- context-sensitive selection and active-object choreography
- `eval(...)` for base curve lookup
- magic numeric offsets like `-0.15`, `+0.2`, `-1.5`, and fixed border offsets without centralized meaning
- rotating the plate procedurally after join as a positional fix
- cursor-dependent origin setting as a geometry contract
- implicit behavior emerging from modifier order instead of explicit geometry rules

## 6. Clean rewrite recommendations

### What behaviour must be preserved

Preserve:
- curved plate is conceptually a straight plate band wrapped around a stable bend anchor
- bend anchor is a deliberate canonical reference object
- arc span comes from preset-driven bend logic
- straight and curved workflows are structurally distinct
- layered composition matters more than direct solid-sector construction

### What implementation patterns must be discarded

Discard:
- context-driven operator pipelines
- post-hoc transform hacks
- hidden cursor/origin assumptions
- geometry rules encoded in magic offsets
- duplication of curved logic across unrelated systems

## 7. A concise geometric contract for the rewrite plate

Recommended rewrite contract:

- `PLATE` represents a band-like plate body, not a filled disc sector
- curved families should be modeled as a plate band spanning a preset-driven arc
- the plate should have a stable anchor equivalent to legacy `EMPTY`
- the plate’s usable length is conceptually derived before curvature is applied
- the final curved result must preserve the visual meaning of:
  - main body strip
  - border layering
  - optional top section
  - styled ends
- `PATH` should remain a reference system for text/attachments, not the primary source of curved plate shape

## Concise Conclusion

The legacy curved plate is supposed to be a **bent layered strip assembly built from straight parts and wrapped around an anchor**, not a solid wedge and not primarily a path-extruded shape.
