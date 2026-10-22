import os
import re
import json
import time
from pathlib import Path
from typing import Optional
from tools.dataset_tools import read_csv_robust

from api.dependencies import (
    get_safe_session_dir,
    get_safe_output_dir,
    get_project_metadata,
    get_local_config_path,
    parse_bool,
    is_valid_url,
    load_crew_modules,
)

def send_automated_email(session_id: str, results_data: dict, meta: dict, cfg: dict, subject: Optional[str] = None, send_pdf: bool = True, send_insights: bool = True):
    try:
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.base import MIMEBase
        from email import encoders

        smtp_host = cfg.get("SMTP_HOST")
        smtp_port_val = cfg.get("SMTP_PORT", 587)
        try:
            smtp_port = int(smtp_port_val)
        except Exception:
            smtp_port = 587
            
        smtp_user = cfg.get("SMTP_USER")
        smtp_password = cfg.get("SMTP_PASSWORD")
        smtp_sender = cfg.get("SMTP_SENDER") or smtp_user
        smtp_recipient = cfg.get("SMTP_RECIPIENT")
        smtp_secure = parse_bool(cfg.get("SMTP_SECURE"))

        if not smtp_host or not smtp_user or not smtp_recipient:
            print("[Automation Email] SMTP parameters missing (host, username, or recipient). Skipping email.")
            return

        print(f"[Automation Email] Preparing automated report email to {smtp_recipient}...")

        pdf_bytes = None
        report_dict = {}
        if send_pdf:
            session_dir = get_safe_session_dir(session_id)
            cleaned_csv = session_dir / "cleaned.csv"
            df = read_csv_robust(cleaned_csv)
            
            report_dict = {
                "dataframe":      df,
                "cleaning_steps": results_data.get("cleaning_steps", ""),
                "relations":      results_data.get("relations", ""),
                "insights":       results_data.get("insights", ""),
                "code":           results_data.get("code", ""),
                "output_dir":     str(get_safe_output_dir(session_id)),
                "report_title":   meta.get("report_title", meta.get("name", "Analysis Report")),
                "goal":           meta.get("optimized_goal") or meta.get("goal") or "",
            }
            
            modules = load_crew_modules()
            _export_pdf = modules["export_pdf"]
            if _export_pdf:
                pdf_bytes = _export_pdf(report_dict)

        msg = MIMEMultipart()
        msg['From'] = smtp_sender
        msg['To'] = smtp_recipient
        
        email_title = subject.strip() if subject and subject.strip() else f"📊 Crewlyze Automated Report: {meta.get('name', 'Analysis Report')}"
        msg['Subject'] = email_title

        body = f"Hello,\n\nYour automated data analysis run for project \"{meta.get('name')}\" has completed successfully.\n"
        if send_pdf:
            body += "\nPlease find the executive PDF summary report attached to this email.\n"
            
        if send_insights:
            insights_txt = results_data.get("insights", "").strip() if isinstance(results_data.get("insights"), str) else ""
            if insights_txt:
                body += f"\n--- Key Strategic Insights ---\n\n{insights_txt}\n"
                
        body += "\nBest regards,\nCrewlyze Swarm\n"
        msg.attach(MIMEText(body, 'plain'))

        if send_pdf and pdf_bytes:
            part = MIMEBase('application', "octet-stream")
            part.set_payload(pdf_bytes)
            encoders.encode_base64(part)
            clean_title = report_dict.get('report_title', meta.get('name', 'report'))
            filename = re.sub(r"[^a-zA-Z0-9_-]", "_", clean_title.lower())[:60] or f"report_{session_id}"
            part.add_header('Content-Disposition', f'attachment; filename="{filename}.pdf"')
            msg.attach(part)

        server = None
        if smtp_port == 465 or smtp_secure:
            try:
                server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15)
            except Exception as ssl_err:
                print(f"[Automation Email] SMTP_SSL connection failed, trying standard SMTP: {ssl_err}")
                
        if server is None:
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=15)
            try:
                server.starttls()
            except Exception as tls_err:
                print(f"[Automation Email] STARTTLS failed: {tls_err}")
        
        if smtp_user and smtp_password:
            server.login(smtp_user, smtp_password)
            
        recipients = [r.strip() for r in smtp_recipient.split(",") if r.strip()]
        server.sendmail(smtp_sender, recipients, msg.as_string())
        server.quit()
        print(f"[Automation Email] Automated report email sent successfully to {smtp_recipient}.")
    except Exception as e:
        print(f"[Automation Email] Failed to send automated email: {e}")

def send_automated_slack(session_id: str, results_data: dict, meta: dict, cfg: dict):
    try:
        import urllib.request
        
        webhook_url = (cfg.get("SLACK_WEBHOOK_URL") or "").strip()
        if not is_valid_url(webhook_url):
            print("[Automation Slack] No active Slack webhook URL configured. Skipping.")
            return

        send_summary = parse_bool(cfg.get("SLACK_SEND_SUMMARY", True))
        if not send_summary:
            print("[Automation Slack] Slack summary card disabled. Skipping Slack post.")
            return

        print("[Automation Slack] Posting automated summary to Slack...")

        title = meta.get("report_title", meta.get("name", "Crewlyze Executive Analysis"))
        rows = results_data.get("rows_count", 0)
        cols = results_data.get("cols_count", 0)
        
        insights_section = results_data.get("insights", "")
        observations = []
        if isinstance(insights_section, str):
            for line in insights_section.split("\n"):
                if "observation:" in line.lower() or "**observation**:" in line.lower():
                    clean_obs = re.sub(r'^\s*[-*]?\s*\d*\.?\s*\**Observation\**:\s*', '', line, flags=re.IGNORECASE)
                    observations.append(clean_obs.strip())
        elif isinstance(insights_section, dict):
            observations = insights_section.get("observations", [])
            
        obs_text = "\n".join([f"• {o}" for o in observations[:3]]) if observations else "Insights generated successfully."
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📊 Automated Crewlyze Analysis Completed",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Project Name:* {meta.get('name')}\n*Report Title:* {title}\n*Dataset:* `{rows} rows x {cols} columns`"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Key Observations:*\n{obs_text}"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "plain_text",
                        "text": f"Session ID: {session_id} | Powered by CrewAI Multi-Agent Swarm",
                        "emoji": True
                    }
                ]
            }
        ]
        
        payload = {"blocks": blocks}
        req = urllib.request.Request(
            webhook_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            res_body = response.read().decode("utf-8")
        print(f"[Automation Slack] Automated Slack message posted successfully: {res_body}")
    except Exception as e:
        print(f"[Automation Slack] Failed to post automated Slack message: {e}")

def send_automated_webhook(session_id: str, results_data: dict, meta: dict, cfg: dict):
    try:
        import requests
        
        webhook_url = (cfg.get("OUTBOUND_WEBHOOK_URL") or "").strip()
        if not is_valid_url(webhook_url):
            print("[Automation Webhook] No active Outbound Webhook URL configured. Skipping.")
            return

        send_json = parse_bool(cfg.get("WEBHOOK_SEND_JSON", True))
        attach_pdf = parse_bool(cfg.get("WEBHOOK_ATTACH_PDF", True))

        print(f"[Automation Webhook] Dispatched automated webhook payload to {webhook_url}...")

        payload = {
            "event": "analysis_completed",
            "timestamp": time.time() * 1000,
            "session_id": session_id,
            "project_name": meta.get("name"),
            "report_title": meta.get("report_title"),
            "status": "success",
        }
        
        if send_json:
            payload["resultsSummary"] = {
                "rows_count": results_data.get("rows_count", 0),
                "cols_count": results_data.get("cols_count", 0),
                "numeric_count": results_data.get("numeric_count", 0),
                "cat_count": results_data.get("cat_count", 0),
                "cleaning_steps": results_data.get("cleaning_steps", []),
                "relations": results_data.get("relations", []),
                "insights": results_data.get("insights", "")
            }
            
        files = {}
        opened_files = []
        
        session_dir = get_safe_session_dir(session_id)
        output_dir = get_safe_output_dir(session_id)
        
        if attach_pdf:
            pdf_path = output_dir / f"{session_id}_report.pdf"
            if not pdf_path.exists():
                try:
                    cleaned_csv = session_dir / "cleaned.csv"
                    df = read_csv_robust(cleaned_csv)
                    report_dict = {
                        "dataframe":      df,
                        "cleaning_steps": results_data.get("cleaning_steps", ""),
                        "relations":      results_data.get("relations", ""),
                        "insights":       results_data.get("insights", ""),
                        "code":           results_data.get("code", ""),
                        "output_dir":     str(output_dir),
                        "report_title":   meta.get("report_title", meta.get("name", "Analysis Report")),
                        "goal":           meta.get("optimized_goal") or meta.get("goal") or "",
                    }
                    modules = load_crew_modules()
                    _export_pdf = modules["export_pdf"]
                    if _export_pdf:
                        pdf_bytes = _export_pdf(report_dict)
                        with open(pdf_path, "wb") as pf:
                            pf.write(pdf_bytes)
                except Exception as pdf_err:
                    print(f"[Webhook Outbound] Failed to pre-compile PDF attachment: {pdf_err}")
            
            if pdf_path.exists():
                fp = open(pdf_path, "rb")
                opened_files.append(fp)
                files["file"] = (f"report_{session_id}.pdf", fp, "application/pdf")
                
        try:
            if files:
                payload_data = {"payload_json": json.dumps(payload)}
                response = requests.post(webhook_url, data=payload_data, files=files, timeout=15)
            else:
                response = requests.post(webhook_url, json=payload, timeout=15)
            response.raise_for_status()
            print(f"[Automation Webhook] Automated custom Webhook completed successfully.")
        finally:
            for fp in opened_files:
                fp.close()
    except Exception as e:
        print(f"[Automation Webhook] Failed to trigger automated custom Webhook: {e}")

def send_automated_discord(session_id: str, results_data: dict, meta: dict, cfg: dict):
    try:
        import requests
        
        username = cfg.get("DISCORD_USERNAME", "").strip()
        avatar_url = cfg.get("DISCORD_AVATAR_URL", "").strip() or "https://raw.githubusercontent.com/sowmiyan-s/crewlyze/main/assets/chat_logo.png"
        embed_color_hex = cfg.get("DISCORD_EMBED_COLOR", "#5865F2").strip()
        mention = cfg.get("DISCORD_MENTION_ROLE", "").strip()
        include_warnings = parse_bool(cfg.get("DISCORD_TOGGLE_WARNINGS", True))
        include_stats = parse_bool(cfg.get("DISCORD_TOGGLE_STATS", True))
        send_summary = parse_bool(cfg.get("DISCORD_SEND_SUMMARY", True))
        attach_pdf = parse_bool(cfg.get("DISCORD_ATTACH_PDF", True))
        attach_charts = parse_bool(cfg.get("DISCORD_ATTACH_CHARTS", False))

        color_val = 5814783
        if embed_color_hex.startswith("#"):
            try:
                color_val = int(embed_color_hex.lstrip("#"), 16)
            except Exception:
                pass

        webhook_url = (cfg.get("DISCORD_WEBHOOK_URL") or "").strip()
        if not is_valid_url(webhook_url):
            print("[Automation Discord] No active Discord webhook URL configured. Skipping.")
            return

        print("[Automation Discord] Posting automated summary to Discord...")

        title = meta.get("report_title", meta.get("name", "Crewlyze Executive Analysis"))
        rows = results_data.get("rows_count", 0)
        cols = results_data.get("cols_count", 0)
        
        insights_section = results_data.get("insights", "")
        observations = []
        warnings_found = []
        if isinstance(insights_section, str):
            for line in insights_section.split("\n"):
                if "observation:" in line.lower() or "**observation**:" in line.lower():
                    clean_obs = re.sub(r'^\s*[-*]?\s*\d*\.?\s*\**Observation\**:\s*', '', line, flags=re.IGNORECASE)
                    observations.append(clean_obs.strip())
                elif "warning" in line.lower() or "alert" in line.lower() or "risk" in line.lower():
                    clean_warn = re.sub(r'^\s*[-*]?\s*\d*\.?\s*\**Warning\**:\s*', '', line, flags=re.IGNORECASE)
                    warnings_found.append(clean_warn.strip())
        elif isinstance(insights_section, dict):
            observations = insights_section.get("observations", [])
            warnings_found = insights_section.get("warnings", [])
            
        obs_text = "\n".join([f"• {o}" for o in observations[:3]]) if observations else "Insights generated successfully."
        
        embed_fields = [
            {"name": "Project Name", "value": meta.get("name", "Unnamed Project"), "inline": True},
            {"name": "Report Title", "value": title, "inline": True}
        ]
        
        if include_stats:
            embed_fields.append({"name": "Dataset Profile", "value": f"`{rows} rows x {cols} columns`", "inline": True})
            
        embed_fields.append({"name": "Key Observations", "value": obs_text, "inline": False})
        
        if include_warnings and warnings_found:
            warn_text = "\n".join([f"⚠️ {w}" for w in warnings_found[:2]])
            embed_fields.append({"name": "Surfaced Warnings & Risks", "value": warn_text, "inline": False})
            
        embed = {
            "title": "📊 Crewlyze Analysis Completed",
            "color": color_val,
            "fields": embed_fields,
            "footer": {"text": f"Session ID: {session_id} | Powered by Crewlyze & CrewAI"}
        }
        
        payload = {}
        if send_summary:
            payload["embeds"] = [embed]
        if username:
            payload["username"] = username
        if avatar_url:
            payload["avatar_url"] = avatar_url
        if mention:
            payload["content"] = f"{mention} - Analysis Complete!"
            
        files = {}
        opened_files = []
        
        session_dir = get_safe_session_dir(session_id)
        output_dir = get_safe_output_dir(session_id)
        
        if attach_pdf:
            pdf_path = output_dir / f"{session_id}_report.pdf"
            if not pdf_path.exists():
                try:
                    cleaned_csv = session_dir / "cleaned.csv"
                    df = read_csv_robust(cleaned_csv)
                    report_dict = {
                        "dataframe":      df,
                        "cleaning_steps": results_data.get("cleaning_steps", ""),
                        "relations":      results_data.get("relations", ""),
                        "insights":       results_data.get("insights", ""),
                        "code":           results_data.get("code", ""),
                        "output_dir":     str(output_dir),
                        "report_title":   meta.get("report_title", meta.get("name", "Analysis Report")),
                        "goal":           meta.get("optimized_goal") or meta.get("goal") or "",
                    }
                    modules = load_crew_modules()
                    _export_pdf = modules["export_pdf"]
                    if _export_pdf:
                        pdf_bytes = _export_pdf(report_dict)
                        with open(pdf_path, "wb") as pf:
                            pf.write(pdf_bytes)
                except Exception as pdf_err:
                    print(f"[Discord Webhook] Failed to pre-compile PDF attachment: {pdf_err}")
            
            if pdf_path.exists():
                fp = open(pdf_path, "rb")
                opened_files.append(fp)
                files["file"] = (f"report_{session_id}.pdf", fp, "application/pdf")
                
        if attach_charts and output_dir.exists():
            png_charts = sorted(list(output_dir.glob("*.png")), key=lambda x: x.stat().st_mtime)
            for idx, chart_path in enumerate(png_charts[:3]):
                fp = open(chart_path, "rb")
                opened_files.append(fp)
                files[f"chart_{idx}"] = (chart_path.name, fp, "image/png")
                
        try:
            if files:
                payload_data = {"payload_json": json.dumps(payload)}
                response = requests.post(webhook_url, data=payload_data, files=files, timeout=15)
            else:
                response = requests.post(webhook_url, json=payload, timeout=15)
            response.raise_for_status()
            print(f"[Automation Discord] Automated Discord message posted successfully.")
        finally:
            for fp in opened_files:
                fp.close()
    except Exception as e:
        print(f"[Automation Discord] Failed to post automated Discord message: {e}")

def run_automation_pipeline(session_id: str, results_data: dict):
    """Dispatch outbound automations (Slack / Discord / Webhook) only if active valid URLs exist."""
    try:
        cfg_path = get_local_config_path()
        if not cfg_path.exists():
            return
        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)

        meta = get_project_metadata(session_id)

        slack_url = (cfg.get("SLACK_WEBHOOK_URL") or "").strip()
        if parse_bool(cfg.get("AUTOMATION_SLACK_ENABLED")) and is_valid_url(slack_url):
            try:
                send_automated_slack(session_id, results_data, meta, cfg)
            except Exception as e:
                print(f"[Automation Hub] Slack runner warning: {e}")

        discord_url = (cfg.get("DISCORD_WEBHOOK_URL") or "").strip()
        if parse_bool(cfg.get("AUTOMATION_DISCORD_ENABLED")) and is_valid_url(discord_url):
            try:
                send_automated_discord(session_id, results_data, meta, cfg)
            except Exception as e:
                print(f"[Automation Hub] Discord runner warning: {e}")

        webhook_url = (cfg.get("OUTBOUND_WEBHOOK_URL") or "").strip()
        if parse_bool(cfg.get("AUTOMATION_WEBHOOK_ENABLED")) and is_valid_url(webhook_url):
            try:
                send_automated_webhook(session_id, results_data, meta, cfg)
            except Exception as e:
                print(f"[Automation Hub] Webhook runner warning: {e}")
    except Exception as e:
        print(f"[Automation Hub] Pipeline dispatch warning: {e}")
