import pytest
from rich.progress import Progress
from src.cli.progress import create_progress_bar, STAGE_DESCRIPTIONS

def test_create_progress_bar():
    progress = create_progress_bar()
    assert isinstance(progress, Progress)
    # Check columns (Spinner, Text, Bar, Percentage, TimeElapsed)
    assert len(progress.columns) == 5

def test_stage_descriptions():
    assert "token_search" in STAGE_DESCRIPTIONS
    assert "market_data" in STAGE_DESCRIPTIONS
    assert STAGE_DESCRIPTIONS["token_search"] == "Resolving Token ID"

def test_progress_usage(rich_console):
    # Verify we can use it in a context manager
    with create_progress_bar() as progress:
        task = progress.add_task("Test Task", total=100)
        progress.update(task, advance=50)
        assert not progress.finished
