# Multi Agent Data Analysis with Crew AI
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

"""
Dataset tools for CrewAI agents.

Security note
-------------
All LLM-generated code is executed in an isolated child process (subprocess),
never via exec() in the parent process. This eliminates RCE risk: the child
has no access to the parent's globals, secrets, or in-memory state.
"""

import os
import re
import sys
import textwrap
import tempfile
import subprocess


import pandas as pd
from crewai.tools import tool


def _strip_markdown_fences(code: str) -> str:
    """Remove leading/trailing markdown code fences from LLM output."""
    code = code.strip()
    code = re.sub(r"^```(?:python)?\s*\n?", "", code)
    code = re.sub(r"\n?```\s*$", "", code)
    return code.strip()


def _run_in_subprocess(script: str, timeout: int = 120) -> tuple[bool, str]:
    """
    Write *script* to a temp file and execute it in an isolated subprocess.

    Returns (success: bool, output: str) where output is stdout+stderr.
    """
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(script)
        tmp_path = tmp.name

    try:
        proc = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = (proc.stdout + proc.stderr).strip()
        success = proc.returncode == 0
        return success, output or "(no output)"
    except subprocess.TimeoutExpired:
        return False, f"Execution timed out after {timeout}s."
    except Exception as e:
        return False, f"Failed to launch subprocess: {e}"
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


class DatasetTools:

    @tool("Read Dataset Head")
    def read_dataset_head(file_path: str) -> str:
        """Reads the first 10 rows of the dataset to understand its structure.
        Uses nrows=10 so the entire file is never loaded into memory.
        """
        try:
            df = pd.read_csv(file_path, nrows=10)
            return df.to_markdown(index=False)
        except Exception as e:
            return f"Error reading file: {e}"

    @tool("Get Dataset Info")
    def get_dataset_info(file_path: str) -> str:
        """Returns basic information about the dataset: shape, columns, data types,
        and missing-value counts.
        """
        try:
            df = pd.read_csv(file_path)
            lines = [f"Shape: {df.shape}", "\nColumns and Types:"]
            for col, dtype in df.dtypes.items():
                missing = df[col].isnull().sum()
                lines.append(f"  - {col}: {dtype} (Missing: {missing})")
            return "\n".join(lines)
        except Exception as e:
            return f"Error analyzing file: {e}"

    @tool("Get Correlation Matrix")
    def get_correlation_matrix(file_path: str) -> str:
        """Returns the top-20 strongest column-pair correlations (by absolute value).

        Sending a full N×N matrix to the LLM wastes tokens and may exceed context
        limits for wide datasets. Only the most informative pairs are returned.
        """
        try:
            df = pd.read_csv(file_path)
            numeric_df = df.select_dtypes(include=["number"])
            if numeric_df.empty:
                return "No numeric columns found."

            corr = numeric_df.corr()
            # Unstack, drop self-correlations, take top 20 by abs value
            unstacked = (
                corr.unstack()
                .reset_index()
                .rename(columns={"level_0": "Col_A", "level_1": "Col_B", 0: "Correlation"})
            )
            unstacked = unstacked[unstacked["Col_A"] < unstacked["Col_B"]]   # unique pairs
            unstacked["AbsCorr"] = unstacked["Correlation"].abs()
            top = (
                unstacked.sort_values("AbsCorr", ascending=False)
                .head(20)
                .drop(columns=["AbsCorr"])
                .reset_index(drop=True)
            )
            return top.to_markdown(index=False)
        except Exception as e:
            return f"Error calculating correlation: {e}"

    @tool("Clean Dataset with Python Code")
    def clean_dataset_with_python(file_path: str, python_code: str) -> str:
        """Cleans the dataset at *file_path* by executing *python_code* in an
        isolated subprocess.

        The subprocess receives the dataset path as `FILE_PATH` env var.
        Your code must:
          1. Read the CSV:  df = pd.read_csv(os.environ['FILE_PATH'])
          2. Perform cleaning on df
          3. Save the result: df.to_csv(os.environ['FILE_PATH'], index=False)

        Do NOT include markdown code fences. Do NOT use any other file paths.
        """
        clean_code = _strip_markdown_fences(python_code)

        # Wrap the user code so the subprocess knows the file path via env var
        script = textwrap.dedent(f"""\
            import os
            import pandas as pd

            FILE_PATH = {repr(str(file_path))}
            df = pd.read_csv(FILE_PATH)

            # ---- LLM-generated cleaning code ----
            {textwrap.indent(clean_code, "            ").lstrip()}
            # ---- end LLM code ----

            df.to_csv(FILE_PATH, index=False)
            print("Dataset cleaned and saved successfully.")
        """)

        success, output = _run_in_subprocess(script)
        if success:
            return f"Dataset cleaned successfully.\n{output}"
        return f"Error executing cleaning code:\n{output}"

    @tool("Execute Visualization Code")
    def execute_visualization_code(python_code: str) -> str:
        """Executes Python code to generate and save visualizations to the
        'outputs' directory.

        The code runs in an isolated subprocess — it MUST import all libraries
        it needs (pandas, matplotlib, seaborn, etc.) and read data from
        'data/cleaned_csv.csv' (or the session-specific path given in the task).
        Save plots as PNG files under the 'outputs' directory.

        Example:
            import pandas as pd
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import seaborn as sns
            df = pd.read_csv('data/cleaned_csv.csv')
            plt.figure(figsize=(10, 6))
            sns.scatterplot(data=df, x='col_x', y='col_y')
            plt.savefig('outputs/plot1.png', bbox_inches='tight', dpi=150)
            plt.close()
        """
        clean_code = _strip_markdown_fences(python_code)

        # NOTE: The session-specific output directory is created by run_crew()
        # before agents are invoked. Do NOT create a root-level "outputs/" here
        # as it would bypass per-session file isolation.
        success, output = _run_in_subprocess(clean_code)
        if success:
            return f"Visualization code executed successfully. Plots saved.\n{output}"
        return f"Error executing visualization code:\n{output}"
