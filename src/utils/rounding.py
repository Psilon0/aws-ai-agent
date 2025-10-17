from decimal import Decimal, ROUND_HALF_UP, getcontext
getcontext().prec = 10

def round_allocation(a, places=3):
    eq = Decimal(a["equities"]).quantize(Decimal(f'1e-{places}'), ROUND_HALF_UP)
    bo = Decimal(a["bonds"]).quantize(Decimal(f'1e-{places}'), ROUND_HALF_UP)
    ca = Decimal(1) - eq - bo
    return {"equities": float(eq), "bonds": float(bo), "cash": float(ca)}
