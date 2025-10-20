# PURPOSE: Utility to neatly round portfolio allocations to fixed decimal places.
# CONTEXT: Used to ensure equities + bonds + cash always sum cleanly to 1.0 after rounding.
# CREDITS: Original work — no external code reuse.

from decimal import Decimal, ROUND_HALF_UP, getcontext

# Set the global precision for Decimal calculations (10 digits total).
# This prevents rounding errors from compounding during repeated operations.
getcontext().prec = 10

def round_allocation(a, places=3):
    """
    Round each asset weight (equities, bonds, cash) to a fixed number of decimal places.

    parameters:
    - a: dict – allocation dictionary, e.g. {"equities": 0.547, "bonds": 0.398, "cash": 0.055}.
    - places: int – number of decimal places to round to (default = 3).

    returns:
    - dict – new allocation where all components are rounded floats that sum to 1.0.

    notes:
    - Uses Decimal for exact rounding behaviour and consistency across platforms.
    - 'cash' is derived as the residual (1 - equities - bonds) to maintain total = 1.0.
    - ROUND_HALF_UP ensures typical “banker’s rounding” (e.g., 0.1235 → 0.124).
    """
    eq = Decimal(a["equities"]).quantize(Decimal(f'1e-{places}'), ROUND_HALF_UP)
    bo = Decimal(a["bonds"]).quantize(Decimal(f'1e-{places}'), ROUND_HALF_UP)

    # Cash is inferred to guarantee sum of weights = 1.0 exactly after rounding.
    ca = Decimal(1) - eq - bo

    # Convert Decimals back to floats for downstream compatibility.
    return {"equities": float(eq), "bonds": float(bo), "cash": float(ca)}
