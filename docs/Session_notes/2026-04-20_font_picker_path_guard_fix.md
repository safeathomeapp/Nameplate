# 2026-04-20 Font Picker Path Guard Fix

## Files changed

- `src/nameplate_addon/operators.py`
- `docs/Session_notes/2026-04-20_font_picker_path_guard_fix.md`

## What changed

- Added a file-path guard to the custom font picker operator.
- Adjusted the saved-directory startup behavior so the browser opens in the remembered folder without treating that folder as the chosen file.

## Why

- The previous font picker could execute with a directory path instead of a specific font file path.
- That produced errors such as Blender trying to work with `C:\WINDOWS\Fonts\` as if it were the selected file.

## Behavior

- The font picker now:
  - opens in the saved directory when available
  - requires a real file to be selected before execution succeeds
  - saves the selected font's parent directory after a successful load

## Verification

1. Reload the add-on in Blender.
2. Open the font picker from a text object.
3. Confirm it opens in the remembered directory.
4. Select an actual font file and confirm it loads successfully.
5. Reopen the font picker and confirm the directory is remembered without the previous directory-path error.

## Assumptions

- The remaining desired behavior is to remember the directory, not to allow accepting the file browser with only a folder selected.
