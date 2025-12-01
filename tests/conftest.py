"""
Pytest fixtures for testing Rich console output.
"""
import pytest
from io import StringIO
from rich.console import Console

@pytest.fixture
def rich_console():
    """
    Returns a Rich Console that writes to a StringIO buffer.
    force_terminal=True ensures that ANSI codes are generated if needed,
    but for pure content assertion we might want to check plain text too.
    """
    return Console(file=StringIO(), force_terminal=True, width=80)

@pytest.fixture
def capture_rich_output(rich_console):
    """
    Fixture that returns a function to get the captured output from the console.
    """
    def _get_output(plain: bool = False) -> str:
        # Get the value from the StringIO buffer
        output = rich_console.file.getvalue()
        return output
    return _get_output

@pytest.fixture
def assert_rich_contains():
    """
    Fixture that returns a helper function to assert console output.
    """
    def _assert(console: Console, expected_text: str):
        output = console.file.getvalue()
        assert expected_text in output, f"Expected '{expected_text}' not found in output:\n{output}"
    return _assert

