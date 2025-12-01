import pytest


def test_rich_console_fixture(rich_console, capture_rich_output):
    """
    Verify that the rich_console fixture correctly captures output.
    """
    rich_console.print("Hello, World!")
    output = capture_rich_output()
    assert "Hello, World!" in output

def test_assert_rich_contains(rich_console, assert_rich_contains):
    """
    Verify that assert_rich_contains helper works.
    """
    rich_console.print("[bold red]Error[/bold red]")
    assert_rich_contains(rich_console, "Error")
    
    # Test failure case
    with pytest.raises(AssertionError):
        assert_rich_contains(rich_console, "Success")

def test_rich_styles(rich_console, capture_rich_output):
    """
    Verify that styles are preserved (or at least text is present).
    Since force_terminal=True, ANSI codes will be present.
    """
    rich_console.print("[bold]Bold Text[/bold]")
    output = capture_rich_output()
    # We check for the text content. 
    # Note: Rich might wrap it in ANSI codes.
    assert "Bold Text" in output
