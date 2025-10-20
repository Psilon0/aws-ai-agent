SEVERITY = {
    "vol_spike": [
        {"cond": "vol_z < 1.5", "sev": "low"},
        {"cond": "1.5 <= vol_z < 2.5", "sev": "medium"},
        {"cond": "vol_z >= 2.5", "sev": "high"}
    ],
    "sentiment_flip": [{"cond": "flip_any", "sev": "medium"}],
    "exposure_mismatch": [{"cond": "out_of_band", "sev": "high"}]
}
