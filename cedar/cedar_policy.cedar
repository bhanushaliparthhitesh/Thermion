// Cedar policies for the cooling-action safety layer.
//
// Cedar's native numeric type is a 64-bit integer (no built-in float).
// Rather than use the `decimal` extension, every continuous metric is
// scaled by 100 before it reaches Cedar (see cedar_check.py's _SCALE),
// so 6.0 degrees becomes 600, 0.85 efficiency becomes 85, etc.
//
// Forbid always overrides permit, regardless of order — so the pattern
// is: permit everything, then forbid the specific unsafe conditions.
// This is the same shape as safety_filter.py's bounds checks, just
// expressed declaratively instead of in Python.

// Baseline: allow any cooling action unless a forbid rule below fires.
permit(
    principal,
    action,
    resource
);

// Deny if temperature deviation exceeds safety_filter.py's
// TEMP_DEVIATION_LIMIT = 6.0 (scaled: 600).
forbid(
    principal,
    action,
    resource
) when {
    context.temperature_deviation_scaled > 600
};

// Deny if water usage is out of bounds.
// TODO: replace 0 / 10000 with safety_filter.py's actual bounds, scaled by 100.
forbid(
    principal,
    action,
    resource
) when {
    context.water_usage_scaled < 0 || context.water_usage_scaled > 10000
};

// Deny if cooling efficiency is out of bounds (expects 0.0–1.0 -> 0–100 scaled).
// TODO: replace 0 / 100 with safety_filter.py's actual bounds, scaled by 100.
forbid(
    principal,
    action,
    resource
) when {
    context.cooling_efficiency_scaled < 0 || context.cooling_efficiency_scaled > 100
};

// Optional third rule from the guide (rapid oscillation) — skipped for now,
// same as Step 4 recommends. Add it here once steady-state is working.
