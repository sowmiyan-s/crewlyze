# Hermes audit-fix verification — real execution, no mocks.
import os, sys, io, contextlib, tempfile
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
import pandas as pd
from tools.dataset_tools import auto_coerce_types, DatasetTools

ok = True
def check(name, cond):
    global ok
    ok = ok and cond
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")

# ── 1. Datatype coercion: int-as-string, currency, %, duplicate rows, mixed years
print("=== 1. auto_coerce_types (real data) ===")
df = pd.DataFrame({
    "int_str": ["1", "2", "3", "4", "5"],
    "int_str_null": ["1", "2", "", "4", "5"],
    "currency": ["$1,000", "$2,500", "$3,200", "$4,100", "$5,000"],
    "pct": ["95%", "88%", "92%", "100%", "76%"],
    "year_only": ["1990", "1991", "1992", "1993", "1994"],
    "real_date": ["2021-01-01", "2021-02-01", "2021-03-01", "2021-04-01", "2021-05-01"],
    "label": ["Yes", "No", "Yes", "No", "Yes"],
    "text": ["apple", "banana", "cherry", "date", "elder"],
})
# inject 2 fully-duplicate rows (the 4th becomes dup of 3rd, etc.)
df = pd.concat([df, df.iloc[[0, 2]]], ignore_index=True)
out, actions = auto_coerce_types(df)
print("  rows in ->", len(df), "| rows out ->", len(out), "(dup removal)")
check("duplicate rows removed (7 -> 5)", len(out) == 5)
check("int-as-string -> int64", str(out["int_str"].dtype) == "int64")
check("int-with-null -> Int64 (nullable)", str(out["int_str_null"].dtype) == "Int64")
check("currency '$1,000' -> int64", str(out["currency"].dtype) == "int64" and out["currency"].iloc[0] == 1000)
check("percent '95%' -> int64 (=95)", str(out["pct"].dtype) == "int64" and out["pct"].iloc[0] == 95)
check("4-digit year stays int (NOT datetime)", str(out["year_only"].dtype).startswith("int"))
check("real date -> datetime64", str(out["real_date"].dtype).startswith("datetime"))
check("binary label -> bool", str(out["label"].dtype) == "bool")
check("text stays object", str(out["text"].dtype) == "object")
check("dedup action reported", any("duplicated" in a.lower() for a in actions))

# ── 2. NO dummy-data fallback in cleaning/visualization tools
print("\n=== 2. no dummy-data fabrication anywhere ===")
import inspect
src_clean = inspect.getsource(DatasetTools.clean_dataset_with_python.func)
src_viz = inspect.getsource(DatasetTools.execute_visualization_code.func)
check("cleaning tool: no feature_a dummy df", "feature_a" not in src_clean)
check("cleaning tool: guard returns 'no active dataset'", "no active dataset is loaded" in src_clean)
check("viz tool: no feature_a dummy df", "feature_a" not in src_viz)
check("viz tool: guard raises when CSV missing", "No active dataset is loaded" in src_viz)
# Whole-repo sanity: no fabrication string left
import subprocess
grep = subprocess.run(["grep", "-rn", "feature_a", "tools/dataset_tools.py", "crew.py", "ui/"],
                      capture_output=True, text=True)
check("repo-wide: feature_a dummy fully removed", grep.returncode != 0)

# When a REAL csv is pointed, the cleaning tool runs real data
tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="")
pd.DataFrame({"a": [1, 2, 3]}).to_csv(tmp.name, index=False)
from config.context import current_session_csv
current_session_csv.set(tmp.name)
os.environ.pop("CURRENT_SESSION_CSV", None)
res2 = DatasetTools.clean_dataset_with_python.func(python_code="print(df.shape)")
print("  with real csv:", repr(res2[:80]))
check("runs real df when csv exists", "Error" not in res2 and "print(df.shape)" not in res2)

# ── 3. Server still imports cleanly
print("\n=== 3. server import ===")
try:
    import main
    check("main imports without error", True)
except Exception as e:
    check(f"main imports without error (got {e})", False)

# ── 4. visualizer fallback uses REAL data, no dummy
print("\n=== 4. visualizer fallback produces real charts from real data ===")
from crew import _run_auto_visualizer_fallback
out_dir = tempfile.mkdtemp()
real_csv = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="")
pd.DataFrame({"sales": [10, 20, 30, 40, 50], "cost": [5, 12, 18, 25, 30], "region": ["A","B","A","B","A"]}).to_csv(real_csv.name, index=False)
msg = _run_auto_visualizer_fallback(real_csv.name, out_dir, relations_text="- X: sales | Y: cost | Type: Scatter Plot | Details: test")
import glob
pngs = glob.glob(os.path.join(out_dir, "*.png"))
print("  charts generated:", len(pngs))
check("real charts generated from real data", len(pngs) >= 1)

print("\nOVERALL:", "PASS — no dummy data, correct dtypes, dedup, server OK"
      if ok else "FAIL")
sys.exit(0 if ok else 1)
