# 2026-04-21 Plate Contact Origin Tilt

## Files Changed

- `src/nameplate_addon/plate.py`
- `docs/Session_notes/2026-04-21_plate_contact_origin_tilt.md`

## Summary

- Left base and `PATH` generation unchanged.
- Changed plate construction so the plate's inner/contact face is built on the path datum at `y = -base_size_y * 0.5`.
- Set the joined `PLATE` origin to the contact point before applying the fixed X tilt.
- Removed the post-build Z nudges that previously repositioned the plate after tilt.

## Geometry Contract

- The path is the source of truth for base shape, size, and position.
- The plate is built in its intended world position.
- The centre of the plate face/edge nearest world `0,0` sits on the path datum.
- The plate origin is set to that contact point.
- Tilt is applied from that contact origin.

## Notes

- This replaces the old correction flow:
  - rotate first
  - temporarily move to `z = -0.15`
  - set origin
  - move again to `z = user_z * 0.5 + 0.2`
- The new flow is:
  - build plate geometry against the path datum
  - set origin at the contact datum
  - tilt from that origin

## Suggested Blender Checks

1. Build circle, oval, square, and special bases.
2. Confirm the generated `PATH` is unchanged.
3. Build 3mm, 4mm, 5mm, and 6mm plates.
4. Confirm the inner/contact face stays on the path datum for each height.
5. Confirm the visible tilt pivots from the contact edge rather than lifting/sliding the whole plate.
6. Check text and nurnie placement after the plate geometry change, because they may have inherited assumptions from the old post-build offsets.
