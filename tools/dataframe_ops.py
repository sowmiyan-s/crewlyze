import pandas as pd
import json

def apply_cleaning(df, cleaning_json):
    rules = json.loads(cleaning_json)

    for rule in rules:
        if rule["action"] == "drop_nulls":
            df = df.dropna()
        if rule["action"] == "fill_null":
            df[rule["column"]] = df[rule["column"]].fillna(rule["value"])
        if rule["action"] == "rename":
            df = df.rename(columns={rule["old"]: rule["new"]})

    return df
