# Nameplate Generator (Blender Add-on)

A procedural nameplate generator originally built for Blender 2.91, now being actively ported and maintained for Blender 5.x.

This add-on creates curved nameplates with configurable bases, engraved text, and decorative “nurnies”.

---

## Features

- Multiple base types:
  - Circle
  - Square
  - Oval
  - Special
- End cap styles:
  - Plain
  - Bevel
  - Chamfer
  - Slant
- Top plate support
- Text engraving
- Decorative nurnie placement and mirroring
- Procedural geometry generation

---

## Project Status

This project is currently in **active migration and refactor**.

- Original Blender 2.91 script preserved
- Blender 5.x version functional and improving
- Incremental refactoring in progress
- Behaviour preservation is a priority

---

## Repository Structure
src/ → Active Blender 5.x add-on
legacy/ → Original Blender 2.91 version (unchanged)
docs/ → Migration notes, issues, dev logs
assets/ → STL files, icons
screenshots/ → UI and output examples

---

## Installation (Blender 5.x)

1. Download `src/nameplate_generator.py`
2. In Blender:
   - Edit → Preferences → Add-ons
   - Click "Install"
   - Select the `.py` file
3. Enable the add-on

---

## Development Approach

- Incremental refactor (no full rewrite)
- Preserve original visual output unless fixing bugs
- Reduce duplication and fragile logic over time
- Prefer clarity over cleverness

---

## Contributing

This project is currently maintained as a structured refactor of legacy code.

Contributions should:
- Be small and focused
- Avoid breaking geometry behaviour
- Be tested in Blender before submission

---

## License

TBD