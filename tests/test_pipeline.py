import pytest
from workflows.pipeline import make_pipeline, make_cooldown_callback, cooldown_task_callback
from config.context import current_cooldown


def test_cooldown_callback():
    cb = make_cooldown_callback(min_sleep=0)
    assert callable(cb)
    token = current_cooldown.set("0")
    try:
        # Should execute without errors with 0 cooldown
        cooldown_task_callback(None)
    finally:
        current_cooldown.reset(token)


def test_make_pipeline_basic():
    agents, tasks = make_pipeline(
        session_id="test_session_abc",
        profile="4 rows, 2 columns",
        project_goal="Increase revenue",
        report_title="Q3 Performance",
        deep_analysis=False,
    )

    assert len(agents) == 7
    assert len(tasks) == 7

    # Verify task agents
    for a, t in zip(agents, tasks):
        assert t.agent == a

    # Clean task check
    assert "test_session_abc" in tasks[0].description
    assert "Increase revenue" in tasks[0].description

    # Relation task check
    assert "4 rows, 2 columns" in tasks[1].description
    assert "STANDARD ANALYSIS MODE" in tasks[1].description


def test_make_pipeline_deep_analysis():
    agents, tasks = make_pipeline(
        session_id="test_deep_session",
        profile="1000 rows, 10 columns",
        project_goal="Detect fraudulent transactions",
        deep_analysis=True,
    )

    assert len(agents) == 7
    assert len(tasks) == 7

    # Verify deep analysis prompt is present
    assert "DEEP ANALYSIS MODE" in tasks[1].description
    assert "DEEP ANALYSIS MODE" in tasks[2].description
    assert "DEEP ANALYSIS MODE" in tasks[3].description
