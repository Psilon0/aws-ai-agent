# Runbook

## KPIs Methodology
- **exp_return_1y**: Weighted mean of expected returns (stub formula now, GBM later).
- **exp_vol_1y**: Weighted stdev proxy.
- **max_drawdown**: -0.8 × vol.

## Alert Severity Matrix
| Rule | Condition | Severity |
|------|------------|-----------|
| vol_spike | vol_z < 1.5 | low |
| vol_spike | 1.5 ≤ vol_z < 2.5 | medium |
| vol_spike | vol_z ≥ 2.5 | high |
| sentiment_flip | any flip | medium |
| exposure_mismatch | out_of_band | high |
