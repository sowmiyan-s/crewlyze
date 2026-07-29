# Crewlyze Relational Database Engine
# Copyright (c) 2025 Sowmiyan S
# Licensed under the MIT License

"""
Relational multi-table SQL query engine using DuckDB and SQLite.
Enables relational JOINs, aggregations, and multi-table queries across imported datasets.
"""

import os
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd

def execute_relational_sql_query(tables_dict: Dict[str, pd.DataFrame], sql_query: str, max_rows: int = 500) -> Dict[str, Any]:
    """
    Executes a read-only SQL query across multiple relational DataFrames using DuckDB or SQLite.

    Args:
        tables_dict: Dictionary of { "table_name": DataFrame }
        sql_query: SQL SELECT query string.
        max_rows: Maximum output rows.

    Returns:
        Dict with keys: success, columns, results, total_count, error
    """
    clean_query = sql_query.strip()
    if not clean_query:
        return {"success": False, "error": "SQL query cannot be empty."}

    # Security check: Enforce read-only SELECT queries
    first_word = clean_query.split()[0].upper() if clean_query.split() else ""
    if first_word not in ("SELECT", "EXPLAIN", "WITH"):
        return {"success": False, "error": "Security Error: Only read-only queries (SELECT / WITH) are permitted."}

    forbidden = ["ATTACH", "DETACH", "PRAGMA", "CREATE", "DROP", "ALTER", "INSERT", "UPDATE", "DELETE", "VACUUM"]
    if any(kw in clean_query.upper() for kw in forbidden):
        return {"success": False, "error": "Security Error: Mutating statements are blocked."}

    # Try DuckDB first for high-performance vectorized SQL JOINs
    try:
        import duckdb
        conn = duckdb.connect(database=":memory:")
        for table_name, df in tables_dict.items():
            safe_name = "".join(c if c.isalnum() else "_" for c in table_name)
            clean_df = df.copy()
            clean_df.columns = [c.strip().replace(" ", "_").replace("-", "_") for c in clean_df.columns]
            conn.register(safe_name, clean_df)

        res_df = conn.execute(clean_query).df()
        conn.close()

        res_df = res_df.replace([float('inf'), float('-inf')], float('nan')).fillna("")
        return {
            "success": True,
            "engine": "duckdb",
            "columns": list(res_df.columns),
            "results": res_df.head(max_rows).to_dict(orient="records"),
            "total_count": len(res_df)
        }
    except Exception as duck_err:
        # Fallback to SQLite
        try:
            import sqlite3
            conn = sqlite3.connect(":memory:")
            for table_name, df in tables_dict.items():
                safe_name = "".join(c if c.isalnum() else "_" for c in table_name)
                df.to_sql(safe_name, conn, index=False)

            res_df = pd.read_sql_query(clean_query, conn)
            conn.close()

            res_df = res_df.replace([float('inf'), float('-inf')], float('nan')).fillna("")
            return {
                "success": True,
                "engine": "sqlite",
                "columns": list(res_df.columns),
                "results": res_df.head(max_rows).to_dict(orient="records"),
                "total_count": len(res_df)
            }
        except Exception as sql_err:
            return {"success": False, "error": f"SQL execution error: {sql_err} (DuckDB error: {duck_err})"}
