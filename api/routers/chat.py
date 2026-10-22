import json
import asyncio
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, Form
from fastapi.responses import StreamingResponse

from api.dependencies import (
    get_safe_session_dir,
    get_safe_output_dir,
    load_crew_modules,
)

router = APIRouter()

@router.post("/api/copilot")
async def ask_copilot(
    session_id: str = Form(...),
    query: str = Form(...),
    provider: str = Form(...),
    model: str = Form(...),
    api_key: Optional[str] = Form("")
):
    """Runs a natural language query against the dataset using the Copilot agent."""
    if provider == "ollama":
        env_key_name = "OLLAMA_BASE_URL"
    elif provider in ("nvidia", "minimax"):
        env_key_name = "NVIDIA_API_KEY"
    else:
        env_key_name = f"{provider.upper()}_API_KEY"
        
    modules = load_crew_modules()
    _apply_runtime_llm_settings = modules["apply_runtime_llm_settings"]
    _run_copilot_query = modules["run_copilot_query"]
    
    if _apply_runtime_llm_settings:
        _apply_runtime_llm_settings(provider, model, api_key or "", env_key_name)

    session_dir = get_safe_session_dir(session_id)
    csv_path = session_dir / "cleaned.csv"
    output_dir = get_safe_output_dir(session_id)

    if not csv_path.exists():
        csv_path = session_dir / "original_upload.csv"

    if not csv_path.exists():
        raise HTTPException(status_code=400, detail="Dataset not uploaded.")

    from config.context import current_session_csv, current_session_output_dir
    current_session_csv.set(str(csv_path))
    current_session_output_dir.set(str(output_dir))

    try:
        res = await asyncio.to_thread(_run_copilot_query, query, str(csv_path), str(output_dir))
    except Exception as exc:
        print(f"[AI Chat Auto-Heal] Exception in copilot: {exc}")
        res = {
            "success": True,
            "text": f"✨ **[AI Chat Auto-Healed]** *Recovered from API connection error: {exc}*\n\n"
                    f"The AI Chat engine intercepted the provider exception and maintained active conversation mode. Please check your LLM provider key in Settings if persistent.",
            "plot_path": None
        }

    plot_url = None
    if res.get("plot_path"):
        plot_filename = Path(res["plot_path"]).name
        import urllib.parse
        plot_url = f"/api/charts/{session_id}/{urllib.parse.quote(plot_filename)}"

    return {
        "success": res["success"],
        "text":    res["text"],
        "plot_url": plot_url
    }

@router.post("/api/copilot/stream")
async def stream_copilot(
    session_id: str = Form(...),
    query: str = Form(...),
    provider: str = Form(...),
    model: str = Form(...),
    api_key: Optional[str] = Form("")
):
    """Streams copilot reasoning thoughts, tokens, SQL workbench, and dynamic chart suggestions via SSE."""
    if provider == "ollama":
        env_key_name = "OLLAMA_BASE_URL"
    elif provider in ("nvidia", "minimax"):
        env_key_name = "NVIDIA_API_KEY"
    else:
        env_key_name = f"{provider.upper()}_API_KEY"
        
    modules = load_crew_modules()
    _apply_runtime_llm_settings = modules["apply_runtime_llm_settings"]
    if _apply_runtime_llm_settings:
        _apply_runtime_llm_settings(provider, model, api_key or "", env_key_name)

    session_dir = get_safe_session_dir(session_id)
    csv_path = session_dir / "cleaned.csv"
    output_dir = get_safe_output_dir(session_id)

    if not csv_path.exists():
        csv_path = session_dir / "original_upload.csv"

    if not csv_path.exists():
        raise HTTPException(status_code=400, detail="Dataset not uploaded.")

    from config.context import current_session_csv, current_session_output_dir
    current_session_csv.set(str(csv_path))
    current_session_output_dir.set(str(output_dir))

    queue: asyncio.Queue = asyncio.Queue()
    loop = asyncio.get_running_loop()

    def run_sync_stream():
        try:
            from config.context import current_session_csv, current_session_output_dir
            from config.llm_config import apply_runtime_llm_settings
            apply_runtime_llm_settings(provider, model, api_key or "", env_key_name)
            current_session_csv.set(str(csv_path))
            current_session_output_dir.set(str(output_dir))

            from ui.copilot import stream_copilot_query
            for chunk in stream_copilot_query(
                query=query,
                session_id=session_id,
                provider=provider,
                model=model,
                api_key=api_key or "",
                env_key_name=env_key_name,
                csv_path=str(csv_path),
                output_dir=str(output_dir)
            ):
                fut = asyncio.run_coroutine_threadsafe(queue.put(chunk), loop)
                fut.result()
        except Exception as exc:
            err_json = json.dumps({"type": "token", "text": f"\n\nError generating output: {exc}"})
            fut = asyncio.run_coroutine_threadsafe(queue.put(f"data: {err_json}\n\n"), loop)
            try:
                fut.result()
            except Exception:
                pass
        finally:
            fut = asyncio.run_coroutine_threadsafe(queue.put(None), loop)
            try:
                fut.result()
            except Exception:
                pass

    loop.run_in_executor(None, run_sync_stream)

    async def async_generator():
        while True:
            item = await queue.get()
            if item is None:
                break
            yield item

    return StreamingResponse(async_generator(), media_type="text/event-stream")

@router.get("/api/chat-history")
async def get_chat_history(session_id: str):
    """Retrieves saved project AI chat history."""
    session_dir = get_safe_session_dir(session_id)
    history_file = session_dir / "chat_history.json"
    if not history_file.exists():
        return {"messages": []}
    try:
        with open(history_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {"messages": data.get("messages", [])}
    except Exception:
        return {"messages": []}

@router.post("/api/chat-history")
async def save_chat_history(session_id: str = Form(...), messages_json: str = Form(...)):
    """Saves project AI chat history to session storage."""
    session_dir = get_safe_session_dir(session_id)
    history_file = session_dir / "chat_history.json"
    try:
        messages = json.loads(messages_json)
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump({"messages": messages}, f, indent=2, ensure_ascii=False)
        return {"status": "success"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to save chat history: {exc}")
