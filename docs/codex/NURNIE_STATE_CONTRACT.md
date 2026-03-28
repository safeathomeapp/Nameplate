# Nurnie State Contract

This note documents the stored anchor state that mirror and rebuild operations rely on.

## Stored Fields

`store_nurnie_anchor_state(obj)` writes the following custom properties to `NURNIE_LEFT` / `NURNIE_RIGHT`:

- `nurnie_anchor_x`
- `nurnie_anchor_y`
- `nurnie_anchor_z`
- `nurnie_scale`
- `nurnie_plane_x`
- `nurnie_plane_y`
- `nurnie_plane_z`

## Meaning

- `nurnie_anchor_*` is the anchor object's current live location after user edits
- `nurnie_scale` is the current `instance_faces_scale`
- `nurnie_plane_*` is the baked local center of the anchor plane mesh and is used as the mirror basis

## Behavioral Rules

- Add and change operations use base-type-aware suggested anchor placement
- Mirror must not recompute from a fresh suggested target endcap position
- Mirror uses the source anchor's stored plane basis, then applies mirrored live offset and current scale
- This preserves expected behavior after a plate resize followed by manual nurnie repositioning

## Refactor Guardrails

- Do not remove these stored properties unless mirror behavior is replaced with an equivalent tested source of truth
- Do not swap mirror back to direct endcap math for `L` bases
- Do not collapse square and curved-base Z logic into one formula without Blender verification
