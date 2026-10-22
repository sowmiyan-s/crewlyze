import os
import sys
import re
import json
import uuid
import time
import shutil
import asyncio
from pathlib import Path
from typing import Optional
import pandas as pd
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import StreamingResponse
from tools.dataset_tools import read_csv_robust

from api.dependencies import (
    SESSIONS_DIR,
    OUTPUTS_DIR,
    get_safe_session_dir,
    get_safe_output_dir,
    get_project_metadata,
    save_project_metadata,
    is_safe_id,
    clean_log_message,
    log_stream_states,
    optimize_goal_grammar,
    load_crew_modules,
    MAX_CONCURRENT_ANALYSES,
    active_analyses,
    active_analyses_lock,
    save_upload_file_safely,
)
from api.notifications import run_automation_pipeline

router = APIRouter()

# ---------------------------------------------------------------------------
# Background Task Pipeline
# ---------------------------------------------------------------------------

def run_crew_in_background(
    session_id: str,
    csv_path: str,
    provider: str,
    model: str,
    api_key: str,
    env_key_name: str,
    cooldown: int,
    selected_tasks: list[str],
    deep_analysis: bool,
    report_title: str,
):
    """
    Orchestrates the CrewAI pipeline in a background thread, writing all
    stdout progress to a tail-able stdout.log file and serializing results.
    """
    global active_analyses
    try:
        if not is_safe_id(session_id):
            raise ValueError("Invalid session ID.")
        session_dir = (SESSIONS_DIR / session_id).resolve()
        resolved_csv = Path(csv_path).resolve()
        try:
            resolved_csv.relative_to(session_dir)
        except ValueError:
            raise ValueError("Path traversal detected in CSV path.")

        from config.context import (
            current_session_id,
            current_session_csv,
            current_session_output_dir,
            current_llm_provider,
            current_llm_model,
            current_llm_api_key,
            current_llm_env_key_name,
            current_cooldown,
            current_deep_analysis,
        )
        current_session_id.set(session_id)
        current_session_csv.set(str(resolved_csv).replace("\\", "/"))
        current_session_output_dir.set(str((OUTPUTS_DIR / session_id).resolve()).replace("\\", "/"))
        current_llm_provider.set(provider)
        current_llm_model.set(model)
        current_llm_api_key.set(api_key or "")
        current_llm_env_key_name.set(env_key_name or "")
        current_cooldown.set(cooldown)
        current_deep_analysis.set(deep_analysis)

        try:
            meta = get_project_metadata(session_id)
            if report_title:
                meta["report_title"] = report_title.strip()
            
            user_goal = meta.get("goal", "")
            if user_goal.strip():
                print("Optimizing goal grammar...")
                opt_goal = optimize_goal_grammar(user_goal, provider, model, api_key, env_key_name)
                meta["optimized_goal"] = opt_goal
                print(f"Optimized goal: {opt_goal}")
            else:
                meta["optimized_goal"] = ""
                
            save_project_metadata(session_id, meta)
        except Exception as e:
            print(f"Error handling metadata goal/title: {e}")

        session_dir = SESSIONS_DIR / session_id
        log_path = session_dir / "stdout.log"
        done_path = session_dir / "done.txt"
        results_path = session_dir / "results.json"

        done_path.unlink(missing_ok=True)
        results_path.unlink(missing_ok=True)

        try:
            meta = get_project_metadata(session_id)
            meta["status"] = "running"
            save_project_metadata(session_id, meta)
        except Exception:
            pass

        with open(log_path, "w", encoding="utf-8", errors="replace", buffering=1) as log_file:
            import contextlib
            with contextlib.redirect_stdout(log_file):
                try:
                    print("Initializing multi-agent workflows...", flush=True)
                    print("[Coordinator] Ingesting Dataset & Initializing 25 Agentic Intelligence System...", flush=True)
                    modules = load_crew_modules()
                    _run_crew = modules["run_crew"]
                    result = _run_crew(
                        csv_path,
                        session_id=session_id,
                        selected_tasks=selected_tasks or None,
                        deep_analysis=deep_analysis,
                    )
                    
                    plotly_serializable = []
                    for chart in result.get("plotly_charts", []):
                        try:
                            if "fig_json" in chart and isinstance(chart["fig_json"], dict):
                                plotly_serializable.append({
                                    "title": chart.get("title", "Interactive Visual"),
                                    "fig_json": chart["fig_json"],
                                    "insight": chart.get("insight", "")
                                })
                            elif "fig" in chart:
                                fig_obj = chart["fig"]
                                f_json = json.loads(fig_obj.to_json()) if hasattr(fig_obj, "to_json") else fig_obj
                                plotly_serializable.append({
                                    "title": chart.get("title", "Interactive Visual"),
                                    "fig_json": f_json,
                                    "insight": chart.get("insight", "")
                                })
                        except Exception as p_err:
                            print(f"[Chart Warning] Failed to serialize chart '{chart.get('title')}': {p_err}")

                    png_charts_list = [f.name for f in Path(result["output_dir"]).glob("*.png")]

                    serializable_result = {
                        "cleaning_steps":  result.get("cleaning_steps", ""),
                        "relations":       result.get("relations", ""),
                        "insights":        result.get("insights", ""),
                        "insights_json":   result.get("insights_json"),
                        "detected_domain": result.get("detected_domain", ""),
                        "predictive":      result.get("predictive", ""),
                        "anomaly":         result.get("anomaly", ""),
                        "trend":           result.get("trend", ""),
                        "code":            result.get("code", ""),
                        "output_dir":      result.get("output_dir", ""),
                        "plotly_charts":   plotly_serializable,
                        "png_charts":      png_charts_list,
                        "rows_count":      int(result["dataframe"].shape[0]),
                        "cols_count":      int(result["dataframe"].shape[1]),
                        "numeric_count":   int(len(result["dataframe"].select_dtypes(include=["number"]).columns)),
                        "cat_count":       int(result["dataframe"].shape[1]) - int(len(result["dataframe"].select_dtypes(include=["number"]).columns)),
                        "categories":      result.get("categories", {}),
                        "executive_narrative": result.get("executive_narrative", ""),
                        "executive_findings":  result.get("executive_findings", []),
                    }

                    preview_data = result["dataframe"].head(100).replace([float('inf'), float('-inf')], float('nan')).fillna("").to_dict(orient="records")
                    serializable_result["preview"] = preview_data

                    with open(results_path, "w", encoding="utf-8") as f:
                        json.dump(serializable_result, f, indent=2)
                    
                    print("\nAnalysis complete! Ready to render dashboard.")

                    try:
                        meta = get_project_metadata(session_id)
                        meta["status"] = "completed"
                        if png_charts_list:
                            import urllib.parse
                            meta["thumbnail"] = f"/api/charts/{session_id}/{urllib.parse.quote(png_charts_list[0])}"
                        save_project_metadata(session_id, meta)
                    except Exception:
                        pass

                    try:
                        run_automation_pipeline(session_id, serializable_result)
                    except Exception as aut_err:
                        print(f"[Automation Error] Outbound automations failed: {aut_err}")

                except Exception as e:
                    import traceback
                    print(f"\nPipeline failed: {e}", file=sys.stderr)
                    traceback.print_exc(file=log_file)

                    modules = load_crew_modules()
                    _run_auto_relation_fallback = modules["run_auto_relation_fallback"]
                    _run_auto_insights_fallback = modules["run_auto_insights_fallback"]
                    _run_auto_predictive_fallback = modules["run_auto_predictive_fallback"]
                    _run_auto_anomaly_fallback = modules["run_auto_anomaly_fallback"]
                    _run_auto_trend_fallback = modules["run_auto_trend_fallback"]

                    try:
                        failed_df = read_csv_robust(str(session_dir / "cleaned.csv")) if (session_dir / "cleaned.csv").exists() else None
                    except Exception:
                        failed_df = None

                    error_result = {
                        "cleaning_steps": "Automated cleaning was applied to the dataset.",
                        "relations": _run_auto_relation_fallback(failed_df) if (_run_auto_relation_fallback and failed_df is not None) else "No relationship map could be generated.",
                        "insights": _run_auto_insights_fallback(failed_df, "", error_reason=f"Pipeline degraded: {e}") if (_run_auto_insights_fallback and failed_df is not None) else "No insights available.",
                        "predictive": _run_auto_predictive_fallback(failed_df) if (_run_auto_predictive_fallback and failed_df is not None) else "Predictive modeling was unavailable for this run.",
                        "anomaly": _run_auto_anomaly_fallback(failed_df) if (_run_auto_anomaly_fallback and failed_df is not None) else "Anomaly audit unavailable.",
                        "trend": _run_auto_trend_fallback(failed_df) if (_run_auto_trend_fallback and failed_df is not None) else "Trend analysis unavailable.",
                        "code": "Visualizations could not be generated for this run.",
                        "output_dir": str(OUTPUTS_DIR / session_id),
                        "plotly_charts": [],
                        "png_charts": [],
                        "rows_count": int(failed_df.shape[0]) if failed_df is not None else 0,
                        "cols_count": int(failed_df.shape[1]) if failed_df is not None else 0,
                        "numeric_count": int(len(failed_df.select_dtypes(include=["number"]).columns)) if failed_df is not None else 0,
                        "cat_count": int(len(failed_df.select_dtypes(include=["object"]).columns)) if failed_df is not None else 0,
                        "degraded": True,
                        "warning": f"Analysis completed with reduced results due to an internal error: {e}"
                    }
                    with open(results_path, "w", encoding="utf-8") as f:
                        json.dump(error_result, f, indent=2)

                    try:
                        meta = get_project_metadata(session_id)
                        meta["status"] = "completed"
                        meta["degraded"] = True
                        save_project_metadata(session_id, meta)
                    except Exception:
                        pass
                finally:
                    with open(done_path, "w", encoding="utf-8") as f:
                        f.write("done")
    finally:
        with active_analyses_lock:
            active_analyses = max(0, active_analyses - 1)

# ---------------------------------------------------------------------------
# Upload & Pre-analysis data exploration
# ---------------------------------------------------------------------------

@router.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Uploads the dataset and registers a unique user session ID."""
    session_id = uuid.uuid4().hex[:12]
    session_dir = get_safe_session_dir(session_id)
    session_dir.mkdir(parents=True, exist_ok=True)

    filename_lower = file.filename.lower()
    is_excel = filename_lower.endswith((".xlsx", ".xls"))
    is_sqlite = filename_lower.endswith((".db", ".sqlite", ".sqlite3"))

    if is_excel:
        file_path = session_dir / "uploaded_file.xlsx"
    elif is_sqlite:
        file_path = session_dir / "uploaded_file.db"
    else:
        file_path = session_dir / "original_upload.csv"

    await save_upload_file_safely(file, file_path)

    log_path = session_dir / "stdout.log"
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("Dataset uploaded successfully.\n")

    proj_name = file.filename.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ').title()
    status = "idle"
    sheets = []
    tables = []

    if is_excel:
        try:
            xl = pd.ExcelFile(file_path)
            sheets = xl.sheet_names
            status = "awaiting_sheet"
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to read Excel workbook: {e}")
    elif is_sqlite:
        try:
            import sqlite3
            conn = sqlite3.connect(str(file_path))
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            conn.close()
            status = "awaiting_table"
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to read SQLite tables: {e}")
    rows_count = 0
    cols_count = 0
    num_count = 0
    cat_count = 0

    if not is_excel and not is_sqlite:
        try:
            df = read_csv_robust(file_path)
            rows_count, cols_count = df.shape
            num_count = int(len(df.select_dtypes(include=["number"]).columns))
            cat_count = int(len(df.select_dtypes(include=["object"]).columns))
            df.to_csv(file_path, index=False)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to read CSV: {e}")

    try:
        meta = {
            "id": session_id,
            "name": proj_name,
            "filename": file.filename,
            "size": file_path.stat().st_size,
            "created_at": time.time() * 1000,
            "status": status,
            "rows_count": rows_count,
            "cols_count": cols_count,
            "numeric_count": num_count,
            "cat_count": cat_count
        }
        save_project_metadata(session_id, meta)
    except Exception:
        pass

    return {
        "session_id": session_id,
        "filename": file.filename,
        "size": file_path.stat().st_size,
        "type": "excel" if is_excel else "sqlite" if is_sqlite else "csv",
        "sheets": sheets,
        "tables": tables,
        "rows_count": rows_count,
        "cols_count": cols_count,
        "numeric_count": num_count,
        "cat_count": cat_count
    }

@router.post("/api/upload/select-sheet")
async def select_excel_sheet(session_id: str = Form(...), sheet_name: str = Form(...)):
    session_dir = get_safe_session_dir(session_id)
    xlsx_path = session_dir / "uploaded_file.xlsx"
    if not xlsx_path.exists():
        raise HTTPException(status_code=400, detail="Excel upload not found.")
    try:
        def _parse_sheet():
            df = pd.read_excel(xlsx_path, sheet_name=sheet_name)
            csv_path = session_dir / "original_upload.csv"
            df.to_csv(csv_path, index=False)
            return csv_path.stat().st_size

        csv_size = await asyncio.to_thread(_parse_sheet)
        
        meta = get_project_metadata(session_id)
        meta["status"] = "idle"
        meta["filename"] = f"{meta['filename']} [{sheet_name}]"
        meta["size"] = csv_size
        save_project_metadata(session_id, meta)
        
        return {"status": "success", "session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load sheet: {e}")

@router.post("/api/upload/select-table")
async def select_sqlite_table(session_id: str = Form(...), table_name: str = Form(...)):
    session_dir = get_safe_session_dir(session_id)
    db_path = session_dir / "uploaded_file.db"
    if not db_path.exists():
        raise HTTPException(status_code=400, detail="Database upload not found.")
    try:
        def _parse_table():
            import sqlite3
            safe_table = table_name.replace("`", "``")
            conn = sqlite3.connect(str(db_path))
            df = pd.read_sql_query(f"SELECT * FROM `{safe_table}`", conn)
            conn.close()
            csv_path = session_dir / "original_upload.csv"
            df.to_csv(csv_path, index=False)
            return csv_path.stat().st_size

        csv_size = await asyncio.to_thread(_parse_table)
        
        meta = get_project_metadata(session_id)
        meta["status"] = "idle"
        meta["filename"] = f"{meta['filename']} [{table_name}]"
        meta["size"] = csv_size
        save_project_metadata(session_id, meta)
        
        return {"status": "success", "session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load table: {e}")

@router.post("/api/query-sql")
async def query_sql_dataset(session_id: str = Form(...), sql_query: str = Form(...)):
    session_dir = get_safe_session_dir(session_id)
    csv_path = session_dir / "cleaned.csv"
    if not csv_path.exists():
        csv_path = session_dir / "original_upload.csv"
    if not csv_path.exists():
        raise HTTPException(status_code=400, detail="Dataset not found.")

    clean_query = sql_query.strip()
    if not clean_query:
        return {"success": False, "error": "Query cannot be empty."}

    first_word = clean_query.split()[0].upper() if clean_query.split() else ""
    if first_word not in ("SELECT", "EXPLAIN", "WITH"):
        return {"success": False, "error": "Security Error: Only read-only queries (SELECT) are permitted."}

    forbidden = ["ATTACH", "DETACH", "PRAGMA", "CREATE", "DROP", "ALTER", "INSERT", "UPDATE", "DELETE", "VACUUM", "REINDEX", "TRANSACTION", "COMMIT", "ROLLBACK"]
    if any(re.search(rf"\b{kw}\b", clean_query, re.IGNORECASE) for kw in forbidden):
        return {"success": False, "error": "Security Error: Mutating or administrative SQL statements are blocked."}

    try:
        def _execute_sql():
            import sqlite3
            df = read_csv_robust(csv_path)
            conn = sqlite3.connect(":memory:")
            df.to_sql("dataset", conn, index=False)

            step_counter = [0]
            def interrupt_handler():
                step_counter[0] += 1
                if step_counter[0] > 50000:  # 50M VM steps guard
                    return 1
                return 0

            conn.set_progress_handler(interrupt_handler, 1000)
            res_df = pd.read_sql_query(clean_query, conn)
            conn.close()
            return res_df

        res_df = await asyncio.to_thread(_execute_sql)

        res_df = res_df.replace([float('inf'), float('-inf')], float('nan')).fillna("")
        results = res_df.head(100).to_dict(orient="records")
        columns = list(res_df.columns)

        return {
            "success": True,
            "columns": columns,
            "results": results,
            "total_count": len(res_df)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/api/query-relational-sql")
async def query_relational_sql(session_id: str = Form(...), sql_query: str = Form(...)):
    """Executes multi-table relational SQL JOINs across all dataset CSVs loaded in session."""
    session_dir = get_safe_session_dir(session_id)
    tables = {}
    for csv_file in session_dir.glob("*.csv"):
        tbl_name = csv_file.stem
        try:
            tables[tbl_name] = read_csv_robust(csv_file)
        except Exception:
            pass

    if not tables:
        raise HTTPException(status_code=400, detail="No CSV datasets found in session directory.")

    from tools.db_tools import execute_relational_sql_query
    return execute_relational_sql_query(tables, sql_query)

@router.post("/api/clean/preview")
async def preview_data_cleaning(session_id: str = Form(...)):
    """Previews data hygiene issues (missing values, duplicates, type conversions) before applying rules."""
    session_dir = get_safe_session_dir(session_id)
    csv_path = session_dir / "original_upload.csv"
    if not csv_path.exists():
        csv_path = session_dir / "cleaned.csv"
    if not csv_path.exists():
        raise HTTPException(status_code=400, detail="Dataset not found for session.")

    try:
        df = read_csv_robust(csv_path)
        null_counts = {col: int(cnt) for col, cnt in df.isnull().sum().items() if cnt > 0}
        dup_count = int(df.duplicated().sum())

        type_conversions = []
        for col in df.select_dtypes(include=["object"]).columns:
            sample_str = df[col].dropna().astype(str).str.strip()
            if sample_str.str.replace(r'[\$,%]', '', regex=True).str.replace('.', '', regex=1).str.isdigit().mean() > 0.8:
                type_conversions.append(col)

        actions = []
        if dup_count > 0:
            actions.append({"action": "drop_duplicates", "description": f"Remove {dup_count} duplicate row(s)"})
        if null_counts:
            actions.append({"action": "impute_missing", "description": f"Impute missing values in {len(null_counts)} column(s)"})
        if type_conversions:
            actions.append({"action": "convert_types", "description": f"Convert numeric text formatting in column(s): {', '.join(type_conversions)}"})

        return {
            "success": True,
            "rows": len(df),
            "columns": len(df.columns),
            "duplicate_rows": dup_count,
            "null_counts": null_counts,
            "type_conversion_candidates": type_conversions,
            "recommended_actions": actions
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/api/clean/apply")
async def apply_data_cleaning(
    session_id: str = Form(...),
    drop_duplicates: bool = Form(True),
    impute_missing: bool = Form(True),
    convert_numeric: bool = Form(True)
):
    """Applies user-approved cleaning rules to dataset and saves cleaned.csv."""
    session_dir = get_safe_session_dir(session_id)
    csv_path = session_dir / "original_upload.csv"
    if not csv_path.exists():
        csv_path = session_dir / "cleaned.csv"
    if not csv_path.exists():
        raise HTTPException(status_code=400, detail="Dataset not found for session.")

    try:
        df = read_csv_robust(csv_path)
        applied = []

        if drop_duplicates:
            before_len = len(df)
            df = df.drop_duplicates()
            applied.append(f"Dropped {before_len - len(df)} duplicate rows")

        if convert_numeric:
            for col in df.select_dtypes(include=["object"]).columns:
                cleaned_series = df[col].astype(str).str.replace(r'[\$,%]', '', regex=True).str.strip()
                converted = pd.to_numeric(cleaned_series, errors="coerce")
                if converted.notnull().sum() > 0.7 * len(df):
                    df[col] = converted
                    applied.append(f"Converted column '{col}' to numeric dtype")

        if impute_missing:
            num_cols = df.select_dtypes(include=["number"]).columns
            for col in num_cols:
                if df[col].isnull().sum() > 0:
                    df[col] = df[col].fillna(df[col].median())
                    applied.append(f"Imputed missing values in '{col}' with median")
            
            cat_cols = df.select_dtypes(exclude=["number"]).columns
            for col in cat_cols:
                if df[col].isnull().sum() > 0:
                    df[col] = df[col].fillna("Unknown")
                    applied.append(f"Filled missing values in '{col}' with 'Unknown'")

        cleaned_path = session_dir / "cleaned.csv"
        df.to_csv(cleaned_path, index=False)

        return {
            "success": True,
            "new_shape": list(df.shape),
            "applied_actions": applied
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/api/dataset-diff")
async def get_dataset_diff(session_id: str):
    session_dir = get_safe_session_dir(session_id)
    orig_path = session_dir / "original_upload.csv"
    clean_path = session_dir / "cleaned.csv"
    
    if not orig_path.exists():
        raise HTTPException(status_code=400, detail="Original dataset upload not found.")
        
    orig_df = read_csv_robust(orig_path)
    
    if not clean_path.exists():
        return {
            "cleaned": False,
            "original_rows": len(orig_df),
            "original_cols": len(orig_df.columns),
            "original_columns": list(orig_df.columns)
        }
        
    clean_df = read_csv_robust(clean_path)
    rows_dropped = len(orig_df) - len(clean_df)
    cols_changed = []
    
    for col in orig_df.columns:
        if col not in clean_df.columns:
            cols_changed.append({"column": col, "type": "dropped"})
            
    for col in clean_df.columns:
        if col not in orig_df.columns:
            cols_changed.append({"column": col, "type": "added"})
        elif orig_df[col].dtype != clean_df[col].dtype:
            cols_changed.append({
                "column": col, 
                "type": "type_changed", 
                "from": str(orig_df[col].dtype), 
                "to": str(clean_df[col].dtype)
            })
            
    return {
        "cleaned": True,
        "original_rows": len(orig_df),
        "original_cols": len(orig_df.columns),
        "cleaned_rows": len(clean_df),
        "cleaned_cols": len(clean_df.columns),
        "rows_dropped": rows_dropped,
        "changes": cols_changed
    }

# ---------------------------------------------------------------------------
# Analysis Trigger & Streaming
# ---------------------------------------------------------------------------

@router.post("/api/analyze")
async def trigger_analysis(
    background_tasks: BackgroundTasks,
    session_id: str = Form(...),
    provider: str = Form(...),
    model: str = Form(...),
    api_key: Optional[str] = Form(""),
    cooldown: int = Form(5),
    selected_tasks: str = Form(""),
    deep_analysis: str = Form("false"),
    report_title: str = Form(""),
    goal: Optional[str] = Form(""),
    clean_rules: Optional[str] = Form("")
):
    """Launches the CrewAI analysis process in the background."""
    session_dir = get_safe_session_dir(session_id)
    csv_path = session_dir / "original_upload.csv"

    if not csv_path.exists():
        raise HTTPException(status_code=400, detail="Session upload not found.")

    if provider == "ollama":
        env_key_name = "OLLAMA_BASE_URL"
    elif provider in ("nvidia", "minimax"):
        env_key_name = "NVIDIA_API_KEY"
    else:
        env_key_name = f"{provider.upper()}_API_KEY"

    task_list = [
        task.strip()
        for task in selected_tasks.split(",")
        if task.strip()
    ]
    if not task_list:
        task_list = ["relations", "insights", "visualization"]

    deep = deep_analysis.strip().lower() in {"true", "1", "yes", "on"}

    try:
        meta = get_project_metadata(session_id)
        if report_title.strip():
            meta["report_title"] = report_title.strip()
        if goal and goal.strip():
            meta["goal"] = goal.strip()
            meta["optimized_goal"] = goal.strip()
        meta["clean_rules"] = clean_rules.strip() if clean_rules else ""
        save_project_metadata(session_id, meta)
    except Exception:
        pass

    global active_analyses
    with active_analyses_lock:
        if active_analyses >= MAX_CONCURRENT_ANALYSES:
            raise HTTPException(
                status_code=429,
                detail="Server is busy. Maximum concurrent analyses limit reached. Please try again later."
            )
        active_analyses += 1

    try:
        background_tasks.add_task(
            run_crew_in_background,
            session_id=session_id,
            csv_path=str(csv_path),
            provider=provider,
            model=model,
            api_key=api_key,
            env_key_name=env_key_name,
            cooldown=cooldown,
            selected_tasks=task_list,
            deep_analysis=deep,
            report_title=report_title.strip(),
        )
    except Exception as e:
        with active_analyses_lock:
            active_analyses = max(0, active_analyses - 1)
        raise e

    return {"status": "started", "session_id": session_id}

@router.post("/api/analyze/stop")
async def stop_analysis(session_id: str = Form(...)):
    """Stops/cancels an active background analysis task."""
    session_dir = get_safe_session_dir(session_id)
    done_path = session_dir / "done.txt"
    results_path = session_dir / "results.json"

    try:
        with open(done_path, "w", encoding="utf-8") as f:
            f.write("done")
    except Exception:
        pass

    if not results_path.exists():
        try:
            with open(results_path, "w", encoding="utf-8") as f:
                json.dump({"error": "Analysis cancelled by user.", "status": "cancelled"}, f, indent=2)
        except Exception:
            pass

    try:
        meta = get_project_metadata(session_id)
        meta["status"] = "failed"
        save_project_metadata(session_id, meta)
    except Exception:
        pass

    global active_analyses
    with active_analyses_lock:
        active_analyses = max(0, active_analyses - 1)

    return {"status": "stopped", "session_id": session_id}

@router.get("/api/analyze/stream")
async def stream_analysis_logs(session_id: str):
    """Streams running stdout log lines using Server-Sent Events (SSE)."""
    session_dir = get_safe_session_dir(session_id)
    log_path = session_dir / "stdout.log"

    if session_id in log_stream_states:
        log_stream_states[session_id] = {"in_prompt": False}

    async def log_generator():
        for _ in range(50):
            if log_path.exists():
                break
            await asyncio.sleep(0.1)

        if not log_path.exists():
            yield "data: [Initializing Master Multi-Agent Orchestration...]\n\n"
        
        yield "data: [Stage 1/8] Ingesting raw dataset & initializing agent squad...\n\n"

        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            while True:
                line = f.readline()
                if line:
                    cleaned = clean_log_message(line, session_id=session_id)
                    if cleaned is not None:
                        yield f"data: {cleaned}\n\n"
                else:
                    done_path = session_dir / "done.txt"
                    if done_path.exists():
                        for trail_line in f.readlines():
                            cleaned_trail = clean_log_message(trail_line, session_id=session_id)
                            if cleaned_trail is not None:
                                yield f"data: {cleaned_trail}\n\n"
                        yield "data: [EOF]\n\n"
                        break
                    await asyncio.sleep(0.1)

    return StreamingResponse(log_generator(), media_type="text/event-stream")

@router.get("/api/results")
async def get_results(session_id: str):
    """Retrieves cached JSON results containing stats, insights, and charts."""
    session_dir = get_safe_session_dir(session_id)
    results_path = session_dir / "results.json"
    if not results_path.exists():
        return {"ready": False, "status": "pending"}

    with open(results_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        if "error" in data:
            return data
        data["ready"] = True
        return data
