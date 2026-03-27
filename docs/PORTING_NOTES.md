# Porting Notes — Blender 2.91 → Blender 5.x

## Objective

Modernize the original add-on for Blender 5.x while preserving:
- Visual output
- User workflow
- Core behaviour

This is **not a rewrite**. It is a controlled refactor.

---

## Key Changes So Far

### Compatibility
- Updated code to work with Blender 4.x / 5.x API changes
- Removed deprecated constructs where required

### Geometry Stability
- Replaced fragile edge-index selection with geometric detection
- Ensured bevel operations only affect intended edges
- Preserved plate thickness and depth behaviour

### Base Generation Fixes
- Fixed square, oval, and special base types:
  - Correct depth restored
  - Correct bevel/inset behaviour restored
  - Removed flat-plane bug

### Top Plate
- Rebuilt top plate drop logic
- Removed broken legacy positioning code
- Introduced controlled offset logic

### Nurnie System
- Refactored duplicated logic:
  - Flip
  - Delete
  - Mirror
- Introduced shared helper functions
- Added `NURNIE_CONFIG` for side-based behaviour

---

## Design Rules

These rules guide all changes:

1. **No Behaviour Drift**
   - Do not change how the plate looks unless fixing a bug

2. **Incremental Changes Only**
   - One function at a time
   - Each change must be testable in Blender

3. **Avoid Over-Engineering**
   - Do not rewrite working systems unnecessarily

4. **Reduce Duplication**
   - Extract shared logic when safe

5. **Geometry > Code Cleanliness**
   - Correct output is more important than “clean” code

---

## Known Fragile Areas

- Curve/path-based positioning
- Mirror logic on curved bases
- Context-sensitive `bpy.ops` usage
- Legacy naming and structure

---

## Future Work

- Stabilize mirror behaviour on curved plates
- Continue removing duplicated left/right logic
- Improve naming consistency
- Gradually replace `bpy.ops` with safer data-level operations
- Full UI cleanup and redesign

---

## Notes

This codebase is intentionally being improved step-by-step.

Large rewrites are avoided to prevent regressions.