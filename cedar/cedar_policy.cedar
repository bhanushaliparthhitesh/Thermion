// Cedar policies for the cooling-action safety layer.
//
// Cedar's native numeric type is a 64-bit integer (no built-in float).
// Every continuous metric is scaled by 100 before reaching Cedar (see _SCALE in cedar_check.py),
// so 6.0 degrees becomes 600, 0.85 efficiency becomes 85, etc.
//
// Forbid always overrides permit, regardless of order.
// Pattern: permit approved actions, then forbid unsafe conditions based on
// safety_filter.py thresholds.

// Permit ONLY actions from the approved cooling action set
permit(
    principal,
    action,
    resource
) when {
    action in [
        Action::"apply_AIR",
        Action::"apply_LIQUID",
        Action::"apply_HYBRID"
    ]
};

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
// WATER_USAGE_MIN = 0.0 from safety_filter.py (scaled: 0).
forbid(
    principal,
    action,
    resource
) when {
    context.water_usage_scaled < 0
};

// Deny if cooling efficiency is out of bounds.
// COOLING_EFFICIENCY_MIN = 0.0, max = 1.0 from safety_filter.py (scaled: 0–100).
forbid(
    principal,
    action,
    resource
) when {
    context.cooling_efficiency_scaled < 0 || context.cooling_efficiency_scaled > 100
};

// Deny if liquid outlet temperature is out of bounds.
// LIQUID_OUTLET_TEMP_MIN = 0.0, LIQUID_OUTLET_TEMP_MAX = 80.0 from safety_filter.py (scaled: 0–8000).
forbid(
    principal,
    action,
    resource
) when {
    context.liquid_outlet_temp_scaled < 0 || context.liquid_outlet_temp_scaled > 8000
};
