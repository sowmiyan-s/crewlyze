
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
    print("CrewAI Data Analyst")
    print("=" * 50)
    
    try:
        a = input("Enter the load data/input.csv : ")
        df = pd.read_csv(a)
    except FileNotFoundError:
        print("Error: data/input.csv not found.")
        sys.exit(1)

    print(f"Loaded {len(df)} rows, {len(df.columns)} columns")
    print(f"Columns: {', '.join(df.columns[:10])}...")


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

    # Dynamic Task Updates
    clean_task.description = f"Clean the dataset ({a}) and return JSON steps or [] if none."
    
    relation_task.description = f"Identify visualization relationships between columns. The dataset is at '{a}'. The columns are: {list(df.columns)}."
    
    code_task.description = f"Generate runnable matplotlib/seaborn code for each relation. The dataset is at '{a}'. Use this exact path in the code. The columns are: {list(df.columns)}."
    
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
                    <span class="section-id">{step_number:02d}</span>
                </div>
                <div class="code-block">
                    <pre><code class="language-{lang}">{content}</code></pre>
                </div>
            </section>
            """
        return f"""
        <section class="section">
            <div class="section-header">
                <h2>{section}</h2>
                <span class="section-id">{step_number:02d}</span>
            </div>
            <p style="color: var(--text-secondary); font-style: italic;">No data available</p>
        </section>
        """
    
    html_blocks = []
    
    # Dataset Preview
    dataset_preview_html = f"""
    <section class="section">
        <div class="section-header">
            <h2>Dataset Preview</h2>
            <span class="section-id">01</span>
        </div>
        <div class="table-wrapper">
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
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CrewAI Data Analysis Report</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-body: #ffffff;
            --bg-surface: #f8f9fa;
            --border-color: #e2e8f0;
            --text-primary: #0f172a;
            --text-secondary: #475569;
            --accent-color: #2563eb;
            --code-bg: #f1f5f9;
            --success-bg: #dcfce7;
            --success-text: #166534;
            --font-sans: 'Inter', sans-serif;
            --font-mono: 'JetBrains Mono', monospace;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            background-color: var(--bg-body);
            color: var(--text-primary);
            font-family: var(--font-sans);
            line-height: 1.6;
            -webkit-font-smoothing: antialiased;
            padding: 40px 20px;
        }}

        .container {{
            max-width: 900px;
            margin: 0 auto;
        }}

        /* Header */
        .header {{
            margin-bottom: 60px;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 30px;
        }}

        .brand-label {{
            font-family: var(--font-mono);
            font-size: 0.75rem;
            color: var(--accent-color);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-weight: 600;
            margin-bottom: 12px;
            display: block;
        }}

        h1 {{
            font-size: 2.5rem;
            font-weight: 700;
            letter-spacing: -0.03em;
            color: var(--text-primary);
            margin-bottom: 20px;
            line-height: 1.1;
        }}

        .meta-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }}

        .meta-item {{
            display: flex;
            flex-direction: column;
            gap: 4px;
        }}

        .meta-label {{
            font-size: 0.75rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            font-weight: 500;
        }}

        .meta-value {{
            font-family: var(--font-mono);
            font-size: 0.9rem;
            font-weight: 500;
        }}

        /* Status Banner */
        .status-banner {{
            background: var(--success-bg);
            color: var(--success-text);
            padding: 12px 20px;
            border-radius: 6px;
            font-size: 0.9rem;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 50px;
        }}

        .status-icon {{
            width: 8px;
            height: 8px;
            background: currentColor;
            border-radius: 50%;
        }}

        /* Sections */
        .section {{
            margin-bottom: 60px;
        }}

        .section-header {{
            display: flex;
            align-items: baseline;
            justify-content: space-between;
            margin-bottom: 24px;
            border-bottom: 2px solid var(--text-primary);
            padding-bottom: 12px;
        }}

        h2 {{
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--text-primary);
        }}

        .section-id {{
            font-family: var(--font-mono);
            font-size: 0.8rem;
            color: var(--text-secondary);
        }}

        /* Code Blocks */
        .code-block {{
            background: var(--code-bg);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 20px;
            overflow-x: auto;
            font-family: var(--font-mono);
            font-size: 0.85rem;
            color: #334155;
        }}

        /* Table Styles */
        .table-wrapper {{
            overflow: auto;
            max-height: 500px;
            border: 1px solid var(--border-color);
            border-radius: 6px;
            background: var(--bg-surface);
            margin-top: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }}

        table.data-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.85rem;
            font-family: var(--font-mono);
            white-space: nowrap;
        }}

        table.data-table th, table.data-table td {{
            padding: 12px 16px;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }}

        table.data-table th {{
            background: var(--bg-surface);
            font-weight: 600;
            color: var(--text-primary);
            position: sticky;
            top: 0;
            z-index: 10;
            border-bottom: 2px solid var(--border-color);
        }}

        table.data-table tr:last-child td {{
            border-bottom: none;
        }}

        table.data-table tr:hover {{
            background-color: var(--code-bg);
        }}
        
        pre {{
            margin: 0;
        }}

        /* Syntax Highlighting */
        .key {{ color: #7c3aed; font-weight: 600; }}
        .string {{ color: #059669; }}
        .number {{ color: #ea580c; }}
        .boolean {{ color: #2563eb; font-weight: 600; }}
        .null {{ color: #db2777; }}
        .keyword {{ color: #db2777; font-weight: 600; }}
        .comment {{ color: #9ca3af; font-style: italic; }}
        .function {{ color: #2563eb; }}

        /* Footer */
        .footer {{
            margin-top: 80px;
            padding-top: 40px;
            border-top: 1px solid var(--border-color);
            text-align: center;
            color: var(--text-secondary);
            font-size: 0.85rem;
        }}

        @media (max-width: 600px) {{
            h1 {{ font-size: 2rem; }}
            .meta-grid {{ grid-template-columns: 1fr; }}
        }}
    </style>
    {script_content}
</head>
<body>
    <div class="container">
        <header class="header">
            <span class="brand-label">CrewAI Multi-Agent System : Data Analysis</span>
            <h1>OUTPUT FROM LLM : </h1>
            
       
        </header>

        <div class="status-banner">
            <div class="status-icon"></div>
            Pipeline completed successfully. All agents executed without errors.
        </div>

        {final_blocks}

        <footer class="footer">
            <p>Generated by CrewAI Multi-Agent System</p>
            <p>Prithiv.A.K  Sebin.S  Sowmiyan.s</p>
        </footer>
    </div>
</body>
</html>
"""
    
    report_file = Path("index.html")
    report_file.write_text(html_report, encoding="utf-8")
    print(f"\nReport saved: {report_file}")
    print("CrewAI Multi-Agent System : Data Analysis")
    print("Prithiv.A.K  Sebin.S  Sowmiyan.s")
    webbrowser.open("index.html")


if __name__ == "__main__":
    main()
    webbrowser.open("index.html")
