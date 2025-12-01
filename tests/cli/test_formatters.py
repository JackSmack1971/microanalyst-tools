import pytest
from src.cli.formatters import format_currency, format_percentage, format_number, format_large_number

def test_format_currency():
    assert format_currency(1234.56) == "$1,234.56"
    assert format_currency(1000) == "$1,000.00"
    assert format_currency(0) == "$0.00"
    assert format_currency(-50.5) == "$-50.50"
    assert format_currency(None) == "N/A"
    assert format_currency(1234.56, symbol="€") == "€1,234.56"

def test_format_percentage():
    # Expecting ratio input (0.1234 -> 12.34%)
    assert format_percentage(0.1234) == "12.34%"
    assert format_percentage(1.0) == "100.00%"
    assert format_percentage(0.0005, precision=2) == "0.05%"
    assert format_percentage(0.123456, precision=4) == "12.3456%"
    assert format_percentage(None) == "N/A"

def test_format_number():
    assert format_number(1234.5678) == "1,234.57"
    assert format_number(1000000) == "1,000,000.00"
    assert format_number(1234.5678, precision=0) == "1,235"
    assert format_number(None) == "N/A"

def test_format_large_number():
    assert format_large_number(100) == "100"
    assert format_large_number(1200) == "1.20K"
    assert format_large_number(2300000) == "2.30M"
    assert format_large_number(1500000000) == "1.50B"
    assert format_large_number(2500000000000) == "2.50T"
    assert format_large_number(0) == "0"
    assert format_large_number(-2300000) == "-2.30M"
    assert format_large_number(None) == "N/A"
    
    # Edge cases
    assert format_large_number(999) == "999"
    assert format_large_number(999.99) == "999.99" # Remains < 1000 so no suffix 
    # Actually logic: abs_value < 1000. 999.99 is < 1000. 
    # But formatting "999.99" might round to "1000.00".
    # Let's see how the implementation handles it.
    # f"{abs_value:.2f}" -> "1000.00" if it rounds up.
    # But it won't have suffix if it didn't enter the loop.
    # Let's test what happens.
