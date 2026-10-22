import os
import re
import json
import uuid
import time
import shutil
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Optional
import pandas as pd
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, StreamingResponse
from tools.dataset_tools import read_csv_robust

from api.dependencies import (
    SESSIONS_DIR,
    DATA_DIR,
    get_safe_session_dir,
    get_safe_output_dir,
    get_project_metadata,
    save_project_metadata,
    is_safe_id,
    is_safe_filename,
    save_upload_file_safely,
)

router = APIRouter()

def BytesIO_iterator(data_bytes: bytes):
    """Simple generator to stream raw bytes back to the response."""
    yield data_bytes

@router.get("/api/projects")
async def list_projects():
    """Lists all available data analysis projects/sessions."""
    projects = []
    if SESSIONS_DIR.exists():
        for p in SESSIONS_DIR.iterdir():
            if p.is_dir():
                try:
                    meta = get_project_metadata(p.name)
                    if meta:
                        projects.append(meta)
                except Exception:
                    pass
    projects.sort(key=lambda x: x.get("created_at", 0), reverse=True)
    return projects

@router.post("/api/projects")
async def create_project(
    name: str = Form(...),
    report_title: str = Form(""),
    goal: str = Form(""),
    file: UploadFile = File(...)
):
    """Creates a new project context and uploads the dataset (CSV, Excel, or SQLite)."""
    project_id = uuid.uuid4().hex[:12]
    session_dir = get_safe_session_dir(project_id)
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
        f.write("Project created. Dataset uploaded successfully.\n")

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

    meta = {
        "id": project_id,
        "name": name.strip(),
        "report_title": report_title.strip() or f"{name.strip()} Executive Analysis",
        "goal": goal.strip(),
        "optimized_goal": "",
        "filename": file.filename,
        "size": file_path.stat().st_size,
        "created_at": time.time() * 1000,
        "status": status,
        "rows_count": rows_count,
        "cols_count": cols_count,
        "numeric_count": num_count,
        "cat_count": cat_count
    }
    save_project_metadata(project_id, meta)

    return {
        "id": project_id,
        "name": meta["name"],
        "report_title": meta["report_title"],
        "goal": meta["goal"],
        "filename": meta["filename"],
        "size": meta["size"],
        "status": meta["status"],
        "type": "excel" if is_excel else "sqlite" if is_sqlite else "csv",
        "sheets": sheets,
        "tables": tables,
        "rows_count": rows_count,
        "cols_count": cols_count,
        "numeric_count": num_count,
        "cat_count": cat_count
    }

@router.post("/api/projects/{project_id}/rename")
async def rename_project(project_id: str, name: str = Form(...)):
    """Renames an existing project context."""
    session_dir = get_safe_session_dir(project_id)
    if not session_dir.exists():
        raise HTTPException(status_code=404, detail="Project not found")

    meta = get_project_metadata(project_id)
    meta["name"] = name.strip()
    save_project_metadata(project_id, meta)

    return meta

@router.post("/api/projects/{project_id}/tweak-relations")
async def tweak_relations(project_id: str, relations_text: str = Form(...)):
    """Saves tweaked relationships back to the results cache."""
    session_dir = get_safe_session_dir(project_id)
    if not session_dir.exists():
        raise HTTPException(status_code=404, detail="Project not found")

    results_path = session_dir / "results.json"
    res_data = {}
    if results_path.exists():
        try:
            with open(results_path, "r", encoding="utf-8") as f:
                res_data = json.load(f)
        except Exception:
            pass
            
    res_data["relations"] = relations_text.strip()
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(res_data, f, indent=2)
        
    return {"status": "success", "relations": res_data["relations"]}

@router.delete("/api/projects/{project_id}")
async def delete_project(project_id: str):
    """Deletes all session files, artifacts, and outputs of a project."""
    session_dir = get_safe_session_dir(project_id)
    output_dir = get_safe_output_dir(project_id)

    if not session_dir.exists():
        raise HTTPException(status_code=404, detail="Project not found")

    shutil.rmtree(session_dir, ignore_errors=True)
    if output_dir.exists():
        shutil.rmtree(output_dir, ignore_errors=True)

    return {"status": "deleted", "id": project_id}

@router.get("/api/projects/{project_id}/export-zip")
async def export_project_zip(project_id: str):
    """Exports the entire project (metadata, data files, results, and generated charts) as a ZIP file."""
    session_dir = get_safe_session_dir(project_id)
    output_dir = get_safe_output_dir(project_id)
    if not session_dir.exists():
        raise HTTPException(status_code=404, detail="Project not found")

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for root, dirs, files in os.walk(session_dir):
            for file in files:
                file_path = Path(root) / file
                arcname = Path("session") / file_path.relative_to(session_dir)
                zip_file.write(file_path, arcname=arcname)
        if output_dir.exists():
            for root, dirs, files in os.walk(output_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = Path("outputs") / file_path.relative_to(output_dir)
                    zip_file.write(file_path, arcname=arcname)

    zip_buffer.seek(0)
    meta = get_project_metadata(project_id)
    safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", meta.get("name", "project").lower())
    filename = f"{safe_name}_{project_id}.zip"
    return StreamingResponse(
        BytesIO_iterator(zip_buffer.getvalue()),
        media_type="application/x-zip-compressed",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.post("/api/projects/import-zip")
async def import_project_zip(file: UploadFile = File(...)):
    """Imports a project from a ZIP file and registers it in the system."""
    zip_contents = await file.read()
    zip_buffer = BytesIO(zip_contents)
    
    project_id = uuid.uuid4().hex[:12]
    temp_dir = DATA_DIR / "temp_import" / project_id
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    target_project_id = project_id
    session_dir = None
    output_dir = None
    try:
        with zipfile.ZipFile(zip_buffer, "r") as zip_file:
            for member in zip_file.infolist():
                if ".." in member.filename or member.filename.startswith("/") or member.filename.startswith("\\"):
                    raise HTTPException(status_code=400, detail=f"Invalid zip entry: {member.filename}")
                target_path = (temp_dir / member.filename).resolve()
                try:
                    target_path.relative_to(temp_dir.resolve())
                except ValueError:
                    raise HTTPException(status_code=400, detail=f"Zip Slip detected: {member.filename}")
            zip_file.extractall(temp_dir)
            
        meta_file = temp_dir / "session" / "metadata.json"
        if not meta_file.exists():
            raise HTTPException(status_code=400, detail="Invalid zip format: missing metadata.json")
            
        with open(meta_file, "r", encoding="utf-8") as f:
            meta = json.load(f)
            
        orig_project_id = meta.get("id")
        if orig_project_id:
            if not is_safe_id(orig_project_id):
                raise HTTPException(status_code=400, detail="Invalid project ID in metadata.")
            target_project_id = orig_project_id
            
        session_dir = get_safe_session_dir(target_project_id)
        if session_dir.exists():
            target_project_id = uuid.uuid4().hex[:12]
            session_dir = get_safe_session_dir(target_project_id)
            meta["id"] = target_project_id
            meta["name"] = f"{meta.get('name', 'Imported')} (Copy)"
            
        output_dir = get_safe_output_dir(target_project_id)
        session_dir.mkdir(parents=True, exist_ok=True)
        
        for item in (temp_dir / "session").iterdir():
            if item.is_file():
                if not is_safe_filename(item.name):
                    continue
                shutil.copy2(item, session_dir / item.name)
                
        if (temp_dir / "outputs").exists():
            output_dir.mkdir(parents=True, exist_ok=True)
            for item in (temp_dir / "outputs").iterdir():
                if item.is_file():
                    if not is_safe_filename(item.name):
                        continue
                    shutil.copy2(item, output_dir / item.name)
                    
        meta["id"] = target_project_id
        if meta.get("thumbnail"):
            thumb_parts = meta["thumbnail"].split("/")
            if len(thumb_parts) >= 5:
                thumb_parts[3] = target_project_id
                meta["thumbnail"] = "/".join(thumb_parts)
                
        with open(session_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
            
        return meta
    except Exception as e:
        if session_dir and session_dir.exists():
            shutil.rmtree(session_dir, ignore_errors=True)
        if output_dir and output_dir.exists():
            shutil.rmtree(output_dir, ignore_errors=True)
        raise HTTPException(status_code=400, detail=f"Import failed: {str(e)}")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

@router.get("/api/projects/{project_id}/preview")
async def get_dynamic_preview(project_id: str):
    """Dynamically reads the latest state of the CSV and returns a 100-row preview, column names, shapes, and types."""
    session_dir = get_safe_session_dir(project_id)
    if not session_dir.exists():
        raise HTTPException(status_code=404, detail="Project not found")

    cleaned_csv = session_dir / "cleaned.csv"
    original_csv = session_dir / "original_upload.csv"
    csv_path = cleaned_csv if cleaned_csv.exists() else original_csv

    if not csv_path.exists():
        raise HTTPException(status_code=404, detail="CSV not found.")

    try:
        df = read_csv_robust(str(csv_path))
        rows_count, cols_count = df.shape
        num_count = int(len(df.select_dtypes(include=["number"]).columns))
        cat_count = cols_count - num_count
        preview = df.head(100).fillna("").to_dict(orient="records")
        col_types = {col: str(dtype) for col, dtype in df.dtypes.items()}
        columns = list(df.columns)

        results_path = session_dir / "results.json"
        if results_path.exists():
            try:
                with open(results_path, "r", encoding="utf-8") as f:
                    res_data = json.load(f)
                res_data["preview"] = preview
                res_data["rows_count"] = rows_count
                res_data["cols_count"] = cols_count
                with open(results_path, "w", encoding="utf-8") as f:
                    json.dump(res_data, f, indent=2)
            except Exception:
                pass

        return {
            "columns": columns,
            "col_types": col_types,
            "rows_count": rows_count,
            "cols_count": cols_count,
            "numeric_count": num_count,
            "cat_count": cat_count,
            "preview": preview
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load preview: {str(e)}")

@router.get("/api/projects/{project_id}/download-csv")
async def download_project_csv(project_id: str):
    """Downloads the cleaned dataset CSV for the specified project."""
    session_dir = get_safe_session_dir(project_id)
    if not session_dir.exists():
        raise HTTPException(status_code=404, detail="Project not found")

    cleaned_csv = session_dir / "cleaned.csv"
    original_csv = session_dir / "original_upload.csv"
    csv_path = cleaned_csv if cleaned_csv.exists() else original_csv

    if not csv_path.exists():
        raise HTTPException(status_code=404, detail="CSV not found.")

    try:
        meta = get_project_metadata(project_id)
        orig_name = meta.get("filename", "dataset.csv")
    except Exception:
        orig_name = "dataset.csv"

    base_name = orig_name.rsplit(".", 1)[0] if "." in orig_name else orig_name
    download_filename = f"{base_name}_cleaned.csv"

    return FileResponse(csv_path, media_type="text/csv", filename=download_filename)

@router.get("/api/charts/{session_id}/{filename}")
async def serve_chart(session_id: str, filename: str):
    """Serves the generated PNG visual charts."""
    if not is_safe_filename(filename):
        raise HTTPException(status_code=400, detail="Invalid filename.")
    output_dir = get_safe_output_dir(session_id)
    chart_path = (output_dir / filename).resolve()
    try:
        chart_path.relative_to(output_dir)
    except ValueError:
        raise HTTPException(status_code=400, detail="Path traversal detected.")
    if not chart_path.exists():
        raise HTTPException(status_code=404, detail="Chart not found.")
    return FileResponse(chart_path)

@router.get("/api/projects/compare")
async def compare_projects(project_a: str, project_b: str):
    """Returns comparative delta data for two completed projects."""
    def _load_project_summary(pid):
        session_dir = get_safe_session_dir(pid)
        results_path = session_dir / "results.json"
        if not results_path.exists():
            raise HTTPException(status_code=404, detail=f"Results not found for project {pid}")
        with open(results_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        meta = get_project_metadata(pid)
        return {
            "id": pid,
            "name": meta.get("name", pid),
            "rows": data.get("rows_count", 0),
            "cols": data.get("cols_count", 0),
            "numeric": data.get("numeric_count", 0),
            "categorical": data.get("cat_count", 0),
            "charts_count": len(data.get("plotly_charts", [])) + len(data.get("png_charts", [])),
            "cleaning": data.get("cleaning_steps", "")[:500],
            "insights": data.get("insights", "")[:800],
            "relations": data.get("relations", "")[:500],
        }

    a = _load_project_summary(project_a)
    b = _load_project_summary(project_b)

    def _delta(va, vb):
        if va == 0:
            return "+∞%" if vb > 0 else "0%"
        pct = round(((vb - va) / va) * 100, 1)
        return f"+{pct}%" if pct >= 0 else f"{pct}%"

    return {
        "project_a": a,
        "project_b": b,
        "deltas": {
            "rows": _delta(a["rows"], b["rows"]),
            "cols": _delta(a["cols"], b["cols"]),
            "numeric": _delta(a["numeric"], b["numeric"]),
            "categorical": _delta(a["categorical"], b["categorical"]),
            "charts": _delta(a["charts_count"], b["charts_count"]),
        }
    }
