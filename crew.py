# Multi Agent Data Analysis with Crew AI
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License


import logging
import sys
import os
from pathlib import Path
import pandas as pd
import webbrowser
from dotenv import load_dotenv

load_dotenv()

logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("opentelemetry").setLevel(logging.ERROR)

if not os.getenv("GROQ_API_KEY"):
    print("ERROR: GROQ_API_KEY environment variable is not set.")
    sys.exit(1)

try:
    from crewai import Crew
except ImportError as e:
    print(f"ERROR: {e}\nRun: pip install crewai")
    sys.exit(1)


def main():
    
    
    
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    
    print("=" * 50)
    print("Multi Agent Data Analysis with Crew AI")
    print("=" * 50)
    
    try:
        default_path = (Path.cwd() / "Data Set" / "TB_Burden_Country.csv").resolve()
        a = input(f"Enter the load data/input.csv  ") or str(default_path)
        df = pd.read_csv(a)
    except FileNotFoundError:
        print("Error: data/input.csv not found.")
        sys.exit(1)

    print(f"Loaded {len(df)} rows, {len(df.columns)} columns")
    print(f"Columns: {', '.join(df.columns[:10])}...")

    # Data Cleaning
    print("\n--- Starting Data Cleaning ---")
    df = df.drop_duplicates()
    
    # Fill numeric missing values with mean
    numeric_cols = df.select_dtypes(include=['number']).columns
    df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())
    
    # Fill categorical missing values with mode
    categorical_cols = df.select_dtypes(include=['object']).columns
    for col in categorical_cols:
        if df[col].isnull().any():
            mode_val = df[col].mode()
            if not mode_val.empty:
                df[col] = df[col].fillna(mode_val[0])
            else:
                df[col] = df[col].fillna("Unknown")

    cleaned_file_path = Path("data") / "cleaned_csv.csv"
    df.to_csv(cleaned_file_path, index=False)
    print(f"Cleaned dataset saved to {cleaned_file_path}")
    
    # Update dataset path for agents
    a = str(cleaned_file_path.absolute())
    print("--- Data Cleaning Complete ---\n")


    from agents.cleaner import cleaner_agent
    from agents.validator import validator_agent
    from agents.relation import relation_agent
    from agents.code_gen import code_gen_agent
    from agents.insights import insights_agent
    from workflows.pipeline import (
        clean_task,
        validate_task,
        relation_task,
        code_task,
        insight_task,
    )



    
    crew = Crew(
        agents=[
            cleaner_agent,
            validator_agent,
            relation_agent,
            code_gen_agent,
            insights_agent,
        ],
        tasks=[
            clean_task,
            validate_task,
            relation_task,
            code_task,
            insight_task,
        ],
        verbose=True,
    )

    result = crew.kickoff()
    

    task_outputs = {}
    
   
    if hasattr(crew, 'tasks'):
        for i, task in enumerate(crew.tasks):
            if hasattr(task, 'output') and task.output:
                task_name = task.description.split()[0].lower()
                if hasattr(task.output, 'raw'):
                    task_outputs[task_name] = str(task.output.raw)
                else:
                    task_outputs[task_name] = str(task.output)
    
 
    if hasattr(result, 'raw'):
        final_output = str(result.raw)
    else:
        final_output = str(result)
    
 
    clean_output = task_outputs.get('clean', '')
    validate_output = task_outputs.get('validate', 'The Coloums in the datasets are' + str(df.columns))
    relation_output = task_outputs.get('identify', 'The Coloums in the datasets are' + str(df.columns))
    code_output = task_outputs.get('generate', 'The Coloums in the datasets are' + str(df.columns) + "and the path to database is : " + a)
    insights_output = task_outputs.get('produce', final_output)
    

    code_path = output_dir / "op.py"
    if code_output and '```python' in code_output:
        import re
        code_match = re.search(r'```python\n(.*?)\n```', code_output, re.DOTALL)
        if code_match:
            code_path.write_text(code_match.group(1), encoding="utf-8")
    
    df_html = df.head(50).to_html(index=False, classes='data-table', border=0)
    
    def prettify(section, content, step_number, lang="text"):
        if content and content.strip():
            # Basic escaping
            content = str(content).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            return f"""
            <section class="section">
                <div class="section-header">
                    <h2>{section}</h2>
                    <span class="step-number">{step_number:02d}</span>
                </div>
                <div class="content-wrapper">
                    <div class="code-block">
                        <pre><code class="language-{lang}">{content}</code></pre>
                    </div>
                </div>
            </section>
            """
        return f"""
        <section class="section">
            <div class="section-header">
                <h2>{section}</h2>
                <span class="step-number">{step_number:02d}</span>
            </div>
            <div class="content-wrapper" style="padding: 2rem; text-align: center; color: var(--text-secondary); font-style: italic;">
                No data available
            </div>
        </section>
        """
    
    html_blocks = []
    
    # Dataset Preview
    dataset_preview_html = f"""
    <section class="section">
        <div class="section-header">
            <h2>Dataset Preview</h2>
            <span class="step-number">01</span>
        </div>
        <div class="table-container">
            {df_html}
        </div>
    </section>
    """
    html_blocks.append(dataset_preview_html)
    
    html_blocks.append(prettify("Data Cleaning Steps", clean_output, 2, "json"))
    html_blocks.append(prettify("Dataset Validation Result", validate_output, 3, "json"))
    html_blocks.append(prettify("Column Relations", relation_output, 4, "json"))
    html_blocks.append(prettify("Visualization Code", code_output, 5, "python"))
    html_blocks.append(prettify("Insights", insights_output, 6, "json"))
    
    final_blocks = "\n".join(html_blocks)

    # JavaScript for syntax highlighting
    script_content = r"""
    <script>
        function highlightAll() {
            const codes = document.querySelectorAll('code');
            codes.forEach(block => {
                let html = block.innerHTML;
                if (block.classList.contains('language-json')) {
                    html = html.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, function (match) {
                        let cls = 'number';
                        if (/^"/.test(match)) {
                            if (/:$/.test(match)) {
                                cls = 'key';
                            } else {
                                cls = 'string';
                            }
                        } else if (/true|false/.test(match)) {
                            cls = 'boolean';
                        } else if (/null/.test(match)) {
                            cls = 'null';
                        }
                        return '<span class="' + cls + '">' + match + '</span>';
                    });
                } else if (block.classList.contains('language-python')) {
                     html = html.replace(/\b(def|class|import|from|return|if|else|elif|for|while|try|except|with|as|pass|break|continue|print|in|is|not|and|or)\b/g, '<span class="keyword">$1</span>');
                     html = html.replace(/(['"])(?:(?=(\\?))\2.)*?\1/g, '<span class="string">$&</span>');
                     html = html.replace(/\b\d+\b/g, '<span class="number">$&</span>');
                     html = html.replace(/#.*/g, '<span class="comment">$&</span>');
                }
                block.innerHTML = html;
            });
        }
        window.onload = highlightAll;
    </script>
    """

    html_report = f"""<!DOCTYPE html>
<!-- 
Multi Agent Data Analysis with Crew AI
Copyright (c) 2025 Sowmiyan S
Licensed under the MIT License
-->
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Multi Agent Data Analysis with Crew AI</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-body: #f3f4f6;
            --bg-card: #ffffff;
            --text-primary: #111827;
            --text-secondary: #4b5563;
            --accent-primary: #2563eb;
            --accent-secondary: #1e40af;
            --border-subtle: #e5e7eb;
            --code-bg: #1e1e1e;
            --code-text: #d4d4d4;
            --success-color: #10b981;
            --font-sans: 'Inter', system-ui, -apple-system, sans-serif;
            --font-mono: 'JetBrains Mono', monospace;
            --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
            --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
            --radius-md: 0.5rem;
            --radius-lg: 0.75rem;
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            background-color: var(--bg-body);
            color: var(--text-primary);
            font-family: var(--font-sans);
            line-height: 1.6;
            -webkit-font-smoothing: antialiased;
            padding: 2rem;
        }}

        .container {{
            max-width: 1000px;
            margin: 0 auto;
        }}

        /* Header */
        .header {{
            text-align: center;
            margin-bottom: 3rem;
            padding: 2rem 0;
        }}

        .brand-badge {{
            display: inline-block;
            background: var(--accent-primary);
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            margin-bottom: 1rem;
            box-shadow: var(--shadow-sm);
        }}

        h1 {{
            font-size: 2.5rem;
            font-weight: 800;
            color: var(--text-primary);
            letter-spacing: -0.025em;
            margin-bottom: 0.5rem;
            background: linear-gradient(135deg, var(--text-primary) 0%, var(--text-secondary) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .subtitle {{
            color: var(--text-secondary);
            font-size: 1.1rem;
        }}

        /* Status Banner */
        .status-banner {{
            background: white;
            border-left: 4px solid var(--success-color);
            padding: 1rem 1.5rem;
            border-radius: var(--radius-md);
            box-shadow: var(--shadow-sm);
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 3rem;
            font-weight: 500;
            color: var(--text-primary);
        }}

        .status-dot {{
            width: 10px;
            height: 10px;
            background-color: var(--success-color);
            border-radius: 50%;
            box-shadow: 0 0 0 4px rgba(16, 185, 129, 0.2);
        }}

        /* Cards */
        .section {{
            background: var(--bg-card);
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-md);
            margin-bottom: 2rem;
            overflow: hidden;
            border: 1px solid var(--border-subtle);
            transition: transform 0.2s ease;
        }}

        .section:hover {{
            transform: translateY(-2px);
        }}

        .section-header {{
            padding: 1.5rem 2rem;
            border-bottom: 1px solid var(--border-subtle);
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: #fafafa;
        }}

        h2 {{
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .step-number {{
            font-family: var(--font-mono);
            font-size: 0.875rem;
            color: var(--text-secondary);
            background: var(--border-subtle);
            padding: 0.25rem 0.5rem;
            border-radius: var(--radius-md);
        }}

        /* Content Areas */
        .content-wrapper {{
            padding: 0;
        }}

        .code-block {{
            background: var(--code-bg);
            padding: 1.5rem;
            overflow-x: auto;
            font-family: var(--font-mono);
            font-size: 0.9rem;
            line-height: 1.5;
            color: var(--code-text);
            border-bottom-left-radius: var(--radius-lg);
            border-bottom-right-radius: var(--radius-lg);
        }}

        /* Table Styles */
        .table-container {{
            overflow-x: auto;
            max-height: 500px;
        }}

        table.data-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.875rem;
            font-family: var(--font-mono);
            white-space: nowrap;
        }}

        table.data-table th {{
            background: #f8fafc;
            color: var(--text-secondary);
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.75rem;
            letter-spacing: 0.05em;
            padding: 1rem 1.5rem;
            text-align: left;
            border-bottom: 1px solid var(--border-subtle);
            position: sticky;
            top: 0;
            z-index: 10;
        }}

        table.data-table td {{
            padding: 1rem 1.5rem;
            border-bottom: 1px solid var(--border-subtle);
            color: var(--text-primary);
        }}

        table.data-table tr:last-child td {{ border-bottom: none; }}
        table.data-table tr:hover td {{ background-color: #f9fafb; }}

        /* Syntax Highlighting (Dark Theme) */
        .keyword {{ color: #c586c0; font-weight: bold; }} /* Purple */
        .string {{ color: #ce9178; }} /* Orange */
        .number {{ color: #b5cea8; }} /* Light Green */
        .boolean {{ color: #569cd6; }} /* Blue */
        .key {{ color: #9cdcfe; }} /* Light Blue */
        .comment {{ color: #6a9955; font-style: italic; }} /* Green */
        .null {{ color: #569cd6; }}

        /* Footer */
        .footer {{
            text-align: center;
            margin-top: 4rem;
            padding-top: 2rem;
            border-top: 1px solid var(--border-subtle);
            color: var(--text-secondary);
            font-size: 0.875rem;
        }}

        .footer p {{ margin-bottom: 0.5rem; }}

        @media (max-width: 768px) {{
            body {{ padding: 1rem; }}
            h1 {{ font-size: 2rem; }}
            .section-header {{ padding: 1rem; }}
            .code-block {{ padding: 1rem; }}
        }}
    </style>
    {script_content}
</head>
<body>
    <div class="container">
        <header class="header">
            <span class="brand-badge">Multi Agent Data Analysis with Crew AI</span>
            <h1>Data Analysis Report</h1>
            <p class="subtitle">Data Analysis as a Service | Automated insights generated by multi-agent swarm</p>
        </header>

        <div class="status-banner">
            <div class="status-dot"></div>
            <span>Pipeline executed successfully. All agents completed their tasks.</span>
        </div>

        {final_blocks}

        <footer class="footer">
            <p><strong>Multi Agent Data Analysis with Crew AI</strong></p>
            <p>Developed by Prithiv.A.K, Sebin.S, Sowmiyan.s</p>
            <p style="font-size: 0.75rem; margin-top: 1rem; opacity: 0.7;">Generated on {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </footer>
    </div>
</body>
<!-- 
Multi Agent Data Analysis with Crew AI
Copyright (c) 2025 Sowmiyan S
Licensed under the MIT License
-->
</html>
"""
    
    report_file = Path("index.html")
    report_file.write_text(html_report, encoding="utf-8")
    print(f"\nReport saved: {report_file}")
    print("Multi Agent Data Analysis with Crew AI")
    print("Prithiv.A.K  Sebin.S  Sowmiyan.s")
    webbrowser.open("index.html")


if __name__ == "__main__":
    main()
    webbrowser.open("index.html")
