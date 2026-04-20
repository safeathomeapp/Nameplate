# 2026-04-19 Next Session Follow-Ups

## Items to review next session

1. Square-base nurnie vertical placement
   - When adding nurnies to square bases, they appear too high.
   - Expected behavior: start centered to the height of the plate.

2. User-configurable saved directories
   - Add a user config or preferences flow so font and STL directories persist.
   - Goal: avoid re-entering or manually editing these paths every session.

3. UI cleanup pass
   - Review excessive headers and boxes.
   - Remove or simplify hidden frames that are no longer needed.
   - Show items such as `Text Extras` inline by default for `Upper Text` and `Main Text` where appropriate.

4. Rebuild Plate button behavior
   - Verify what `Rebuild Plate` currently does in practice.
   - If it is redundant, broken, or unclear, either fix it or relabel/remove it.
   - Document the intended behavior clearly.

5. Export / save-plate UX
   - Review the current Blender-native export flow.
   - Identify ways to make exporting/saving the plate more user-friendly and less sloppy.
   - Possible areas: naming defaults, destination handling, save/export wording, and workflow clarity.

6. Re-center text when plate height changes
   - When `Plate Height` changes, re-center the text on the Z axis based on the current plate height.
   - The text should stay visually centered relative to the plate depth instead of keeping a stale height offset.

7. Support multiple nurnies per plate
   - Review replacing fixed `Left Nurnie` / `Right Nurnie` slots with a more general `Add Nurnie` flow.
   - Goal: allow multiple nurnies on one plate, such as 3 or 4, rather than only one per side.

## Notes

- Current viewport work is in a usable state; next session should focus on geometry placement and UX polish rather than more viewport tuning unless regressions appear.
