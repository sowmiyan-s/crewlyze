import re
import sqlite3
import pandas as pd
import pytest


def validate_and_execute_sql(query: str, df: pd.DataFrame) -> dict:
    clean_query = query.strip()
    if not clean_query:
        return {"success": False, "error": "Query cannot be empty."}

    first_word = clean_query.split()[0].upper() if clean_query.split() else ""
    if first_word not in ("SELECT", "EXPLAIN", "WITH"):
        return {"success": False, "error": "Security Error: Only read-only queries (SELECT) are permitted."}

    forbidden = [
        "ATTACH", "DETACH", "PRAGMA", "CREATE", "DROP", "ALTER",
        "INSERT", "UPDATE", "DELETE", "VACUUM", "REINDEX", "TRANSACTION",
        "COMMIT", "ROLLBACK"
    ]
    if any(re.search(rf"\b{kw}\b", clean_query, re.IGNORECASE) for kw in forbidden):
        return {"success": False, "error": "Security Error: Mutating or administrative SQL statements are blocked."}

    conn = sqlite3.connect(":memory:")
    df.to_sql("dataset", conn, index=False)
    res_df = pd.read_sql_query(clean_query, conn)
    conn.close()

    return {
        "success": True,
        "results": res_df.to_dict(orient="records"),
        "total_count": len(res_df)
    }


def test_sql_guard_allows_valid_select():
    df = pd.DataFrame({"id": [1, 2, 3], "val": [10, 20, 30]})
    res = validate_and_execute_sql("SELECT * FROM dataset WHERE val > 15", df)
    assert res["success"] is True
    assert res["total_count"] == 2
    assert res["results"][0]["val"] == 20


def test_sql_guard_allows_with_clause():
    df = pd.DataFrame({"id": [1, 2, 3], "val": [10, 20, 30]})
    res = validate_and_execute_sql("WITH sub AS (SELECT * FROM dataset) SELECT COUNT(*) AS cnt FROM sub", df)
    assert res["success"] is True
    assert res["results"][0]["cnt"] == 3


def test_sql_guard_blocks_mutating_statements():
    df = pd.DataFrame({"id": [1, 2, 3], "val": [10, 20, 30]})

    mutations = [
        "DROP TABLE dataset",
        "DELETE FROM dataset WHERE id = 1",
        "UPDATE dataset SET val = 999",
        "INSERT INTO dataset VALUES (4, 40)",
        "ALTER TABLE dataset ADD COLUMN extra TEXT",
        "PRAGMA table_info(dataset)",
    ]

    for q in mutations:
        res = validate_and_execute_sql(q, df)
        assert res["success"] is False
        assert "Security Error" in res["error"]
