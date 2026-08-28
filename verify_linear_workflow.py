# Hermes verification harness — proves the linear pipeline ordering in crew.py
import os, sys, time, io, contextlib, tempfile
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import pandas as pd

# Build a tiny representative dataset so the run is fast
tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="")
df = pd.DataFrame({
    "date": ["2021-01-01","2021-02-01","2021-03-01","2021-04-01","2021-05-01"],
    "revenue": [100, 120, 90, 140, 160],
    "cost": [60, 70, 55, 80, 90],
    "region": ["A","B","A","B","A"],
})
df.to_csv(tmp.name, index=False)
csv_path = tmp.name

# No API key set -> every LLM stage fails fast (401) and the auto-healing
# pure-Python fallback engines run. This exercises the REAL crew.py path.
os.environ.pop("NVIDIA_API_KEY", None)
os.environ.pop("OPENAI_API_KEY", None)
os.environ["CREWLYZE_DEBUG"] = "false"

from crew import run_crew

def run_and_check(deep, label):
    buf = io.StringIO()
    t0 = time.time()
    with contextlib.redirect_stdout(buf):
        result = run_crew(csv_path, session_id=f"verify_{label}", deep_analysis=deep)
    elapsed = time.time() - t0
    log = buf.getvalue()

    print(f"\n########## MODE: {label} (deep_analysis={deep}) ##########")
    import re
    stage_lines = [l.strip() for l in log.splitlines()
                   if re.search(r"\[Stage \d", l) or
                      l.strip().startswith("Running") or
                      "Building interactive Plotly" in l]
    print("=== STAGE EXECUTION ORDER ===")
    for s in stage_lines:
        print("  " + s)

    idx_clean = log.find("[Stage 1/8] Running Data Cleaner")
    idx_rel   = log.find("[Stage 2/8] Running Relation Analyst")
    idx_viz   = log.find("[Stage 3/8] Running Data Visualizer")
    idx_ins   = log.find("[Stage 4/8] Running BI Analyst")
    idx_pred  = log.find("[Stage 5/8] Running Predictive Auto-ML")
    idx_anom  = log.find("[Stage 6/8] Running Anomaly")
    idx_trend = log.find("[Stage 7/8] Running Time-Series Trend")
    idx_plot  = log.find("[Stage 8/8] Building interactive Plotly")

    checks = []
    ordered = [idx_clean, idx_rel, idx_viz, idx_ins, idx_plot]
    if deep:
        ordered = [idx_clean, idx_rel, idx_viz, idx_ins, idx_pred, idx_anom, idx_trend, idx_plot]
    # All present (deep adds 3 specialized)
    present = [x for x in ordered if x != -1]
    checks.append(("all stages printed in this mode", len(present) == len(ordered)))
    # Strictly increasing = linear ordering
    strictly_linear = all(present[i] < present[i+1] for i in range(len(present)-1))
    checks.append(("stages execute in strictly increasing (linear) order", strictly_linear))
    if deep:
        checks.append(("insights before predictive", idx_ins < idx_pred))
        checks.append(("predictive before anomaly", idx_pred < idx_anom))
        checks.append(("anomaly before trend", idx_anom < idx_trend))
        checks.append(("trend before plotly", idx_trend < idx_plot))

    ok = True
    print("=== ORDER ASSERTIONS ===")
    for name, c in checks:
        print(f"  [{'PASS' if c else 'FAIL'}] {name}")
        ok = ok and c

    required_keys = ["dataframe","cleaning_steps","relations","insights",
                     "predictive","anomaly","trend","code","output_dir","plotly_charts"]
    missing = [k for k in required_keys if k not in result]
    print("=== RESULT CONTRACT ===")
    if missing:
        print("  [FAIL] Missing keys:", missing)
        ok = False
    else:
        print("  [PASS] All required result keys present")
    spec_ok = bool(result["predictive"]) and bool(result["anomaly"]) and bool(result["trend"])
    print(f"  [{'PASS' if spec_ok else 'FAIL'}] specialized outputs populated")
    ok = ok and spec_ok

    print(f"Elapsed: {elapsed:.1f}s")
    return ok

ok1 = run_and_check(False, "standard")
ok2 = run_and_check(True, "deep")
all_ok = ok1 and ok2
print("\nOVERALL:", "PASS — pipeline is strictly linear in all modes and contract intact"
      if all_ok else "FAIL")
sys.exit(0 if all_ok else 1)
