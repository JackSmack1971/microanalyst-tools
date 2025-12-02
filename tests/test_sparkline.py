import pytest
from src.visualization.sparkline import generate_sparkline

def test_generate_sparkline_empty():
    assert generate_sparkline([]) == ""

def test_generate_sparkline_flat():
    data = [10.0] * 10
    result = generate_sparkline(data, length=5)
    # Expect 5 chars, all same (middle level usually, or just handled)
    # Implementation uses levels[3] for flat
    assert "▄▄▄▄▄" in result
    assert "[white]" in result # Flat = white

def test_generate_sparkline_increasing():
    data = [1.0, 2.0, 3.0, 4.0, 5.0]
    result = generate_sparkline(data, length=5)
    # Should be green
    assert "[green]" in result
    # Should contain rising bars
    assert " " in result # Lowest
    assert "█" in result # Highest

def test_generate_sparkline_decreasing():
    data = [5.0, 4.0, 3.0, 2.0, 1.0]
    result = generate_sparkline(data, length=5)
    # Should be red
    assert "[red]" in result
    
def test_generate_sparkline_downsampling():
    data = list(range(100))
    result = generate_sparkline(data, length=10)
    # Should return length 10 string (plus markup)
    # Markup adds chars, so check content length roughly or strip markup
    from rich.text import Text
    plain = Text.from_markup(result).plain
    assert len(plain) == 10
