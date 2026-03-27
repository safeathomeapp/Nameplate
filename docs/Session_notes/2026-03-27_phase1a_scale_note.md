# Phase 1A Session Note: Scale Convention Clarification

Date: 2026-03-27

## Context

After Phase 1 reference-object testing, it was observed that the generated reference objects appeared at the wrong size.

An initial follow-up change was prepared around a `10x` working-scale assumption so that preset values authored as millimeters would build at a larger centimeter-style working size.

## Clarification

Project direction is now clarified as:

- preset source dimensions are in millimeters
- conversion should be standard `mm -> m`
- the add-on should not use a `mm -> cm` or `10x` scale convention

In other words:

- `32mm` should convert to `0.032` meters
- `105x70mm` should convert to `0.105 x 0.070` meters

## Impact

This means the temporary Phase 1A scaling assumption was incorrect.

The correct long-term rule for the rewrite is:
- centralize one explicit `mm -> m` conversion helper
- apply that same rule consistently to both `BASE` and `PATH`
- avoid hidden per-object scale multipliers

## Implementation Note

At this point, the important architectural parts from Phase 1 remain valid:

- canonical object names
- managed-object tagging
- deterministic rebuild behaviour
- conditional `PATH`
- reset that removes only managed objects

Only the scale convention needs to be treated as corrected project guidance.

## Next Action

Next code follow-up should:

1. restore a single explicit `mm -> m` conversion rule
2. apply it consistently across reference object creation
3. keep build/reset/object lifecycle unchanged
