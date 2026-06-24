
import json
from datetime import datetime
import pandas as pd

FIELD_ALIASES = {
    "phi2": ["Phi2", "phi2", "PhiII", "PhiPS2"],
    "phinpq": ["PhiNPQ", "phiNPQ"],
    "phino": ["PhiNO", "phiNO"],
    "npqt": ["NPQt", "npqt", "NPQ"],
    "ql": ["qL", "ql"],
    "lef": ["LEF", "lef"],
    "spad": ["SPAD", "spad", "relative_chlorophyll", "Relative Chlorophyll"],
    "ecst": ["ECSt", "ECS", "ECSt mAU"],
    "vhplus": ["vH+", "vHplus", "vH"],
    "ghplus": ["gH+", "gHplus", "gH"],
    "pmf": ["pmf", "PMF"],
    "p700": ["P700", "DIRK_P700", "P700_DIRK"],
    "ps1_active_centers": ["PS1 Active Centers", "PSI Active Centers"],
    "ps1_open_centers": ["PS1 Open Centers", "PSI Open Centers"],
    "ps1_oxidized_centers": ["PS1 Oxidized Centers", "PSI Oxidized Centers"],
    "ps1_over_reduced_centers": ["PS1 Over Reduced Centers", "PSI Over Reduced Centers"],
    "par": ["PAR", "light_intensity", "previous_light_intensity"],
    "leaf_temperature": ["leaf_temperature", "Leaf Temperature", "contactless_temp"],
    "ambient_temperature": ["temperature", "ambient_temperature", "Ambient Temperature"],
    "humidity": ["humidity", "Humidity"],
    "pressure": ["pressure", "Pressure"],
    "thickness": ["thickness", "leaf_thickness", "Leaf Thickness"],
    "angle": ["angle", "Angle"],
    "direction": ["direction", "cardinal_direction"],
    "timestamp": ["timestamp", "time", "created_at", "date", "Date"],
}

def flatten_json(obj, prefix=""):
    out = {}
    if isinstance(obj, dict):
        for key, value in obj.items():
            new_key = f"{prefix}.{key}" if prefix else str(key)
            out.update(flatten_json(value, new_key))
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            new_key = f"{prefix}.{index}" if prefix else str(index)
            out.update(flatten_json(value, new_key))
    else:
        out[prefix] = obj
    return out

def find_value(flat, aliases):
    keys = list(flat.keys())
    for alias in aliases:
        a = alias.lower()
        for k in keys:
            if k.lower() == a or k.split(".")[-1].lower() == a:
                return flat[k]
    for alias in aliases:
        a = alias.lower()
        for k in keys:
            if a in k.lower():
                return flat[k]
    return None

def coerce_float(value):
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip().replace(",", "."))
        except ValueError:
            return None
    return None

def split_json_records(data):
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ["measurements", "data", "rows", "results", "items"]:
            if isinstance(data.get(key), list):
                return data[key]
        return [data]
    return []

def normalize_measurement(raw, source_file, metadata):
    flat = flatten_json(raw)
    now = datetime.now().isoformat(timespec="seconds")
    row = {
        "imported_at": now,
        "source_file": source_file,
        "experiment": metadata.get("experiment"),
        "treatment": metadata.get("treatment"),
        "sample_id": metadata.get("sample_id"),
        "plant_id": metadata.get("plant_id"),
        "replicate": metadata.get("replicate"),
        "notes": metadata.get("notes"),
        "raw_json": json.dumps(raw, ensure_ascii=False),
    }
    for target, aliases in FIELD_ALIASES.items():
        value = find_value(flat, aliases)
        if target in ["timestamp", "direction"]:
            row[target] = str(value) if value is not None else None
        else:
            row[target] = coerce_float(value)
    if not row.get("timestamp"):
        row["timestamp"] = now
    return row

def parse_uploaded_file(uploaded_file, metadata):
    name = uploaded_file.name.lower()
    if name.endswith(".json") or name.endswith(".txt"):
        data = json.loads(uploaded_file.read().decode("utf-8", errors="replace"))
        return [normalize_measurement(r, uploaded_file.name, metadata) for r in split_json_records(data)]
    if name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
        return [normalize_measurement(series.dropna().to_dict(), uploaded_file.name, metadata) for _, series in df.iterrows()]
    raise ValueError(f"Formato non supportato: {uploaded_file.name}")
