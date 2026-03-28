# Nameplate Generator

Blender add-on for generating curved nameplates with configurable base styles, engraved text, top plates, and decorative nurnies.

This repository contains:

- the active modular Blender package in `src/nameplate_addon/`
- the original Blender 2.91 legacy reference in `legacy/`
- supporting project and migration notes in `docs/`

## Status

This project is being maintained as a legacy-preserving refactor.

- behavior preservation is the primary rule
- geometry changes are only made when fixing confirmed bugs
- the modular package structure is now the active add-on codebase

## Supported Blender Version

- Current target: Blender 5.x
- Legacy reference: Blender 2.91

## Features

- circle, square, oval, and special base types
- multiple end-cap styles
- top plate generation
- engraved text workflow
- nurnie add, change, flip, and mirror operations
- procedural geometry generation from the Blender UI

## Installation

Install the packaged add-on from the modular package directory or a zipped package built from it.

For Blender:

1. Open `Edit -> Preferences -> Add-ons`
2. Click `Install...`
3. Select the add-on package zip, or package the contents of `src/nameplate_addon/` as a Blender add-on first
4. Enable the add-on after installation

If you are working from source, the active package entry point is:

- `src/nameplate_addon/__init__.py`

## Repository Structure

- `src/nameplate_addon/`: active Blender add-on package
- `legacy/`: original legacy implementation kept for behavior reference
- `docs/`: session notes, porting notes, known issues, and refactor contracts
- `assets/`: icons and supporting assets
- `screenshots/`: UI and output reference images
- `extras/`: non-core project extras

## Development Rules

- preserve object naming
- preserve modifier order
- preserve geometry behavior unless fixing a confirmed bug
- do not casually rewrite `drawPlateTrue`
- prefer small, testable changes
- verify behavior in Blender for geometry-sensitive work

## Known Limitations

- the codebase still contains legacy `bpy.ops` flows that are intentionally preserved where behavior depends on them
- some project documentation is developer-oriented because the refactor is still in progress
- public release packaging should use the package structure under `src/nameplate_addon/`

## Manual Verification Areas

Before release, verify in Blender:

- square, circle, oval, and special base generation
- top plate generation
- nurnie add/change/flip/mirror behavior
- mirror behavior after plate size changes
- plate grouping/join behavior
- add-on install flow from package/zip

## License

TBD
