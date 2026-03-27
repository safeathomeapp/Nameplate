# Nameplate Generator — Project Understanding & Functional Specification

## Purpose

This document explains the current **Nameplate Generator** project as a functional system, based on the working Blender 5.x script and the behaviour discussed during development.

The goal of this document is not to describe the code line-by-line. The goal is to describe:

- what the add-on does
- what objects it creates
- what each UI control means
- how those controls affect the generated nameplate
- which behaviours are global vs per-object
- which parts of the current script are stable
- which parts are fragile or legacy-driven
- what a clean ground-up rewrite would need to reproduce

This is intended to be used as a **functional brief** for recreating the add-on from scratch in Codex or another engineering workflow.

---

## High-Level Summary

This add-on creates a tabletop miniature **nameplate** in Blender.

The output is a curved or straight plate that can include:

- a main base plate
- optional decorative end caps
- an optional top plate
- a main text line
- an upper text line
- optional decorative attachments called **nurnies**
- an optional FOV cut-out
- STL export for 3D printing or modelling use

The system is procedural, meaning the plate is rebuilt from properties and helper objects rather than edited manually.

At a practical level, the add-on works by creating and managing a set of named scene objects such as:

- `BASE`
- `PATH`
- `EMPTY`
- `PLATE`
- `MAINTEXT`
- `UPPERTEXT`
- `NURNIE_LEFT`
- `NURNIE_RIGHT`
- `NUR_LEFT`
- `NUR_RIGHT`

The object naming is important because much of the UI and logic depends on these names.

---

## Core Scene Objects and Their Roles

## `BASE`
This is the underlying base reference mesh for the selected base type and size.

Its role is to define:
- base type
- size class
- plate curvature assumptions
- dimensions used later when drawing the final plate

It is **not** the final printable plate. It is the reference geometry used to derive the final plate.

---

## `PATH`
This is the curve object used by curved text and some nurnie behaviour.

Its role is to define the curved deformation path.

For circular and oval bases, text and some decorative objects are attached to this path with Curve modifiers.

This is one of the most sensitive parts of the project because:
- text placement depends on it
- nurnie placement and mirroring depend on it
- rotating or scaling it changes downstream behaviour

---

## `EMPTY`
This is the deformation origin used by the final plate bend operation.

Its role is to act as a datum / bend origin for the plate.

This object is important because the final `PLATE` bends around it using a `SIMPLE_DEFORM` bend modifier.

In a clean rewrite, `EMPTY` should remain the canonical bend/basis object.

---

## `PLATE`
This is the final joined nameplate mesh.

It is built from multiple components such as:
- base body
- top border
- bottom border
- left end cap
- right end cap
- optional top plate section

It is then:
- joined
- remeshed
- bent around `EMPTY`

This is the main deliverable object for export.

---

## `MAINTEXT`
Main engraved or raised text on the lower/main band of the plate.

It is a Blender text object with:
- size
- extrusion
- font
- spacing
- curve deformation on curved bases
- remesh for printability / robustness

---

## `UPPERTEXT`
Upper text line, usually used on the optional top plate or upper band.

Functionally similar to `MAINTEXT`, but intended for the upper region.

---

## `NURNIE_LEFT` / `NURNIE_RIGHT`
These are support plane objects used as anchors for decorative geometry.

They are not the decorative STL itself. They are the support/instancer objects that define:
- where the nurnie sits
- how it follows the plate/path
- its local movement and scale

---

## `NUR_LEFT` / `NUR_RIGHT`
These are the actual imported decorative STL meshes.

They are parented to the nurnie support planes and then instanced.

---

# Functional Model of the Add-on

## 1. Base Selection
The user selects a base family and a base size.

The supported base families are:

- Circle
- Oval
- Square
- Special

Each family has predefined size options.

Selecting a base creates:
- `BASE`
- sometimes `PATH`
- supporting deformation references

---

## 2. Plate Construction
Once the base is confirmed, the plate is built procedurally.

The main construction variables are:
- plate height / thickness
- end cap style
- end cap width
- curvature amount
- whether the base plate is engravable/plain
- whether a top plate exists
- top plate height and coverage
- top plate end styling

The build function creates separate primitive mesh components, names them, then joins them into `PLATE`.

---

## 3. Text Placement
The main and upper text are separate text objects.

Their final position is influenced by:
- base type
- path deformation
- text spacing
- text size
- local movement offsets
- whether text is italic
- whether engraving is enabled on export

On curved bases, text is positioned partly through text-data offsets and partly through world/object location.

On square bases, text behaves more like ordinary placement.

---

## 4. Nurnie Placement
A nurnie is a decorative imported STL, usually attached left or right.

The current system works like this:
- import STL
- create a small support plane
- parent the imported STL to the plane
- apply a Curve modifier / instancing behaviour
- allow local movement, scale, flipping, mirroring, replacement, and deletion

This system works, but is one of the least cleanly abstracted parts of the project.

---

## 5. Export / Import
The add-on supports:
- export of the finished STL
- import of an existing STL plate for alignment/edit support

The export can also make duplicate instances real in some workflows so the result is printable/exportable.

---

# UI Structure

The panel is in:

- `3D View`
- Sidebar
- Tab: **Name Plate**

The panel is state-driven. The UI shown depends on:
- whether the user is starting new or importing
- whether `PLATE` exists
- which object is currently selected
- which edit mode is chosen in the add-on UI

This means the same panel can show:
- setup controls
- plate controls
- text controls
- nurnie controls
- import controls

---

# Complete UI Option Breakdown

## Start State

### `my_newbase`
Options:
- `NEW`
- `IMPORT`

Effect:
- `NEW` starts a new procedural plate workflow
- `IMPORT` allows importing an existing STL plate and aligning it to a selected base reference

---

## Base Family Selection

### `my_baselist`
Options:
- `Circle Bases`
- `Oval Bases`
- `Square Bases`
- `Special Bases`

Effect:
Chooses which base-family enum becomes active and which base-drawing function is used:
- `drawCBase`
- `drawOBase`
- `drawSBase`
- `drawZBase`

This selection determines:
- base reference geometry
- whether the plate is straight or curved
- whether `PATH` is used
- what arc options are shown later

---

## Base Size Selection

### `my_BCIRCLE`
Circle size presets such as:
- 25mm
- 32mm
- 40mm
- 50mm
- 60mm
- 80mm
- 100mm
- 130mm
- 160mm

Effect:
Creates a circular base reference and matching curve behaviour.

---

### `my_BOVAL`
Oval presets such as:
- 60x35
- 75x42
- 90x52
- 105x70
- 120x92
- 150x95
- 170x105

Effect:
Creates an oval base and oval path.

---

### `my_BSQUARE`
Square presets such as:
- 25mm
- 32mm
- 40mm
- 50mm
- 60mm
- 80mm
- 100mm
- 130mm
- 160mm

Effect:
Creates a straight/square base workflow.

---

### `my_BSPECIAL`
Special presets:
- 70x25 40K Bike
- 95x40 40K Bike

Effect:
Uses special predefined geometry logic.

---

## Confirm Base

### `Confirm Base Choice`
Operator:
- `getready.myop_operator`

Effect:
Moves the workflow from base setup toward editable plate-building state.

---

# Edit Mode Selector

Once `PLATE` exists, the UI offers:

### `my_item`
Options:
- `Nameplate`
- `Upper Text`
- `Main Text`
- `Left Nurnie`
- `Right Nurnie`

Effect:
This decides what the panel edits and which scene object is selected.

This is a key workflow control:
- `PLATE` edits shape/options
- `MAINTEXT` edits main text
- `UPPERTEXT` edits top text
- `NURNIE_LEFT` / `NURNIE_RIGHT` edit decorative side attachments

---

# Global Workflow Buttons

### `Save Your STL`
Operator:
- `object.export_stl_custom`

Effect:
Exports the finished model.

---

### `Start Over`
Operator:
- `clear_scene.myop_operator`

Effect:
Removes the procedural setup and resets the workflow.

---

### `Clear Any Engraves`
Operator:
- `draw.myop_operator`

Effect:
Rebuilds/redraws the plate, effectively clearing text engraving changes from the current mesh build.

---

# Nameplate Editing Options

These appear when `PLATE` is selected.

## `autodraw`
Boolean toggle.

Effect:
- When `True`, changing properties redraws the plate automatically
- When `False`, the user must press `Create Plate`

This controls rebuild strategy.

---

## `Create Plate`
Operator:
- `draw.myop_operator`

Effect:
Manually triggers plate generation if autodraw is off.

---

## `basic_options`
Boolean expander.

Effect:
Shows/hides main plate controls.

---

## `eng_bot`
Labelled as plain/engrave style.

Effect:
Switches the lower/main plate behaviour between engravable/plain variants.

This changes the geometry of the main lower body region.

---

## `angles`
Arc of nameplate for circle/special family.

Options:
- 90°
- 120°
- 150°
- 180°

Effect:
Changes how much of the circle the plate covers.
This changes:
- plate arc length
- final bend angle
- text and nurnie placement assumptions

This is one of the most important curved-plate parameters.

---

## `o_angles`
Arc option for some oval logic.

Options:
- 90°
- 120°
- 135°

Effect:
Determines oval arc coverage where supported.

---

## `my_main_ends`
Main end-cap design.

Options:
- Plain
- Round
- Slanted
- Chamfered

Effect:
Controls the shape treatment applied to the outer end cap profile of the main plate.

Practical meaning:
- `Plain` keeps square ends
- `Round` bevels into a rounded end
- `Slanted` creates a sloped end
- `Chamfered` creates a clipped/bevelled end

This affects only the main plate end caps, not the top plate.

---

## `end_length`
End cap width.

Options:
- 2mm
- 3mm
- 4mm
- 5mm
- 6mm

Effect:
Controls how wide the left and right end-cap blocks are.

This affects:
- how much room the end caps occupy
- effective central plate length
- curved placement formulas that reference end spacing

---

## `my_user_z`
Plate height/thickness.

Options:
- 3mm
- 4mm
- 5mm
- 6mm

Effect:
Controls total main plate height.

This affects:
- base/body thickness
- border/top band relationships
- text embed assumptions
- top plate positioning
- nurnie vertical placement assumptions

This is one of the most globally important dimensions.

---

## `top_options`
Boolean expander.

Effect:
Shows/hides top plate controls.

---

## `add_top`
Boolean.

Effect:
Adds or removes the top plate section (`TopBit`).

---

## `my_top_height`
Top plate height.

Options:
- 1.5mm
- 2mm
- 2.5mm
- 3mm

Effect:
Controls the thickness of the optional top plate.

---

## `top_angles`
Top plate coverage.

Options:
- 1/4 coverage
- 1/2 coverage
- 3/4 coverage
- Full coverage

Effect:
Controls how much of the main plate length the top plate spans.

This changes the horizontal length/coverage of `TopBit`.

---

## `drop_top_halfway`
Boolean toggle.

Effect:
Controls whether the top plate:
- sits fully on top of the main plate
- or drops halfway into it

Practical effect:
This changes the vertical center position of `TopBit`.

---

## `my_top_ends`
Top plate end-cap design.

Options:
- Plain
- Round
- Slanted
- Chamfered

Effect:
Applies a style treatment to the top plate end profile, independent from the main plate end style.

---

## `addit_options`
Boolean expander.

Effect:
Shows/hides advanced options.

---

## `fov_option`
Boolean.

Effect:
Adds an FOV cut-out feature when enabled.

---

# Main Text Controls

These appear when `MAINTEXT` is selected.

## Text body
Property:
- `text.body`

Effect:
Sets the actual displayed main text string.

This is the plate’s primary inscription.

---

## Font selector
Property:
- `text.font`

Effect:
Chooses the font used for the text object.

---

## `eng_bot_text`
Boolean.

Effect:
Controls whether main text should be engraved on export.

Interpretation:
- off = likely raised / surface text workflow
- on = engraved/subtractive intent on export workflow

---

## `it_bot_text`
Boolean.

Effect:
Applies italic style via text shear.

Current implementation changes font shear rather than using a true italic font.

---

## `text.size`
Effect:
Controls overall text size.

---

## `myZFloat`
Custom object property.

Labelled:
- `<< Down / Up >>`

Effect:
Moves the text object along its local vertical-ish axis.

This is not a raw world-Z slider; it uses custom getter/setter logic based on the object’s local orientation.

---

## `myYFloat`
Custom object property.

Labelled:
- `<< Back / Forwards >>`

Effect:
Moves the text object along its local depth axis.

Again, this is local-axis movement, not simple world translation.

---

## `maintext_options`
Boolean expander.

Effect:
Shows extra text controls.

---

## `space_character`
Effect:
Adjusts spacing between characters.

---

## `space_word`
Effect:
Adjusts spacing between words.

---

## `Increase Text Clarity`
Operator:
- `increasevoxel.myop_operator`

Effect:
Reduces remesh voxel size to make text sharper / more detailed.

Trade-off:
- more detail
- more geometry
- heavier processing

---

## `Decrease Text Clarity`
Operator:
- `decreasevoxel.myop_operator`

Effect:
Increases remesh voxel size to simplify/smooth text.

Trade-off:
- less detail
- lighter processing

---

# Upper Text Controls

These are functionally almost identical to main text controls.

Differences:
- target object is `UPPERTEXT`
- intended physical location is upper plate/top band
- uses `eng_top_text` and `it_top_text` style toggles

Note:
In the current script, some italic toggle wiring appears shared or slightly inconsistent. A rewrite should cleanly separate main-text and upper-text state.

---

# Nurnie Controls

## Nurnie Directory and Preview
Properties:
- `WindowManager.my_previews_dir`
- `WindowManager.my_previews`

Effect:
Chooses a folder and preview item for STL import/change.

This is the asset selection system for decorative nurnies.

---

## `Add your Left Hand Nurnie`
Operator:
- `addnurnieleft.myop_operator`

Effect:
Imports the selected STL and creates:
- `NUR_LEFT`
- `NURNIE_LEFT`

Then attaches the STL to the support plane and applies the required instancing/curve behaviour.

---

## `Add your Right Hand Nurnie`
Operator:
- `addnurnieright.myop_operator`

Effect:
Same as left, but for the right side.

---

## Nurnie location slider
Property:
- `obj.location`, index 0

Label changes depending on base:
- Square: `<< Left / Right >>`
- Curved: `<< Around Circle >>`

Effect:
Moves the nurnie support anchor along the relevant logical axis.

Meaning differs by base:
- straight left/right on square
- travel around the path/curve on curved bases

---

## `myNurnZFloat`
Custom property.

Effect:
Moves the nurnie on one local axis.

Despite the label text, this is tied to the object’s custom local-axis motion logic, not simple world Z.

---

## `myNurnYFloat`
Custom property.

Effect:
Moves the nurnie on the other local axis.

Again, local-axis driven, not raw world movement.

---

## `instance_faces_scale`
Effect:
Controls decorative nurnie scale.

This is the main per-nurnie scale control.

---

## `Flip Nurnie`
Operators:
- `flipnurnieleft.myop_operator`
- `flipnurnieright.myop_operator`

Effect:
Flips the decorative STL orientation on the chosen side.

---

## `Mirror Nurnie On Plate`
Operators:
- `mirrornurnieleft.myop_operator`
- `mirrornurnieright.myop_operator`

Effect:
Attempts to duplicate/mirror a nurnie to the opposite side.

This is one of the current fragile/legacy areas and is the source of much recent work.

Desired behaviour:
- take an existing side
- create the matching opposite side nurnie
- preserve scale and relative placement
- produce a visually mirrored result

Current state:
- works inconsistently on curved plates
- better candidate for isolated rewrite than for global script changes

---

## `Change Nurnie`
Operators:
- `changenurnieleft.myop_operator`
- `changenurnieright.myop_operator`

Effect:
Replaces the existing STL on the chosen side while keeping the support/placement workflow.

---

## `Remove Nurnie`
Operators:
- `deletenurnieleft.myop_operator`
- `deletenurnieright.myop_operator`

Effect:
Deletes the nurnie on the chosen side and returns that side to an “add” state.

---

# Imported Plate Workflow

When importing an existing STL plate:
- the user is warned that imported plates may not align automatically
- the user must choose a reference base shape and size
- the imported plate can then be positioned relative to the generated base

This workflow is meant for alignment/reference, not full parametric reconstruction from STL.

---

# How Plate Geometry Is Constructed

The final plate build generally works like this:

1. Read `BASE`
2. Determine base family and dimensions
3. Derive:
   - usable plate length
   - bend angle
   - end cap width
   - border thickness
   - top plate placement
4. Create primitive mesh blocks:
   - `NameplateBase`
   - `NameplateTop`
   - `NameplateBottom`
   - `END_LEFT`
   - `END_RIGHT`
   - optional `TopBit`
5. Apply end styling
6. Join all pieces into `PLATE`
7. Apply:
   - remesh
   - bend/simple deform around `EMPTY`
8. Final plate sits in world space ready for text/nurnies/export

This means a clean rewrite should not try to sculpt one mesh directly. It should preserve the “assemble simple parts, then deform” philosophy.

---

# Geometry Parameters and Their Meaning

## Plate Thickness
Currently driven by `my_user_z`.

This is one of the most important core dimensions.
It affects:
- final plate body height
- top/bottom border relationships
- text embed assumptions
- top plate vertical placement
- likely nurnie vertical reference logic

---

## End Length
Currently driven by `end_length`.

Controls how much of the total plate length is reserved by the end caps.

This reduces the central usable straight/curved span.

---

## Arc / Coverage
Controlled by `angles`, `o_angles`, and `top_angles`.

This determines:
- how much of the circle/oval is covered
- bend angle
- path span
- text path assumptions
- nurnie placement assumptions

---

## Border Thickness / Depth
Internally the script uses narrow top/bottom bands.

These create the bordered visual look and help define:
- engravable main body
- upper/lower decorative frame
- top plate seating

---

# Known Fragile Areas

These are the parts a ground-up rewrite should handle carefully:

## 1. Nurnie Mirror Logic
This is the most obvious candidate for redesign.

Current problem:
- mirror behaviour is derived from legacy coordinate assumptions
- changes to path or arc ripple through it unpredictably

Rewrite recommendation:
Use a canonical placement representation and build both left/right from that.

---

## 2. Curve/Text/Nurnie Coordinate Interpretation
Text and nurnies on curved bases are affected by:
- world/object location
- text data offsets
- path orientation
- modifier order

A rewrite should document a single consistent coordinate model.

---

## 3. Heavy Dependence on Named Scene Objects
Current script relies on object names heavily.

This works, but is brittle.

A rewrite can still keep named objects for UX clarity, but should centralise them better.

---

## 4. `bpy.ops` Context Sensitivity
Many operations use context-sensitive operators.

This makes the script fragile under:
- wrong active object
- wrong mode
- wrong selection state

A rewrite should prefer data-level operations where practical.

---

## 5. Duplicated Side Logic
Left/right nurnie functions are historically duplicated.

Recent cleanup started extracting helpers, but the subsystem remains more duplicated than ideal.

A rewrite should use side-driven helper logic from the outset.

---

# What a Ground-Up Rewrite Must Preserve

A replacement script should preserve these functional behaviours:

1. Base-family selection with presets
2. Procedural plate generation from primitive parts
3. Main end-cap styles
4. Optional top plate with independent styling
5. Main text and upper text workflows
6. Import/change/flip/delete/mirror nurnie workflows
7. Export to STL
8. Imported-plate alignment workflow
9. The same overall “look” of the generated plate
10. Bend around a stable datum/origin object

If those are preserved, the new script can be considered functionally equivalent even if the internals are cleaner.

---

# Recommended Ground-Up Rewrite Architecture

If this were rebuilt cleanly, the architecture should likely be:

## 1. Configuration Layer
A structured property model containing:
- base family
- base preset
- arc
- thickness
- end style
- top plate settings
- text settings
- nurnie settings

---

## 2. Reference Geometry Layer
Functions that create:
- `BASE`
- `PATH`
- `EMPTY`

These should be deterministic and isolated.

---

## 3. Plate Builder
A pure-ish builder that reads config and produces:
- plate component blocks
- final joined `PLATE`

---

## 4. Text Builder
Separate helper(s) for:
- main text
- upper text

These should share logic but allow different placement rules.

---

## 5. Nurnie Builder
One coherent subsystem for:
- import
- attach
- move
- scale
- flip
- mirror
- replace
- delete

Mirror should be rewritten from first principles.

---

## 6. UI Layer
A cleaner UI should:
- reduce state surprises
- separate setup from edit mode more clearly
- reduce dependence on active-object quirks
- keep the current practical workflow

---

# Final Understanding in One Sentence

This project is a **procedural Blender add-on for building curved or straight miniature nameplates with layered plate geometry, configurable text, optional top plates, and decorative mirrored side attachments, using a mix of reference meshes, curve deformation, and object-based editing workflows**.

---

# Most Important Insight for a Rewrite

The hardest part is **not** building the plate mesh.

The hardest part is building a **clear and stable coordinate system** for:
- curved text
- top text
- nurnie placement
- nurnie mirroring

A successful rewrite must make those systems explicit instead of emergent from legacy offsets and object transforms.

