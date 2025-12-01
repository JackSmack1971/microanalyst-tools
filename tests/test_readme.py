import pytest
from pathlib import Path

def test_readme_exists():
    readme = Path("README.md")
    assert readme.exists()

def test_readme_content():
    readme = Path("README.md")
    content = readme.read_text(encoding="utf-8")
    
    # Check for key sections and flags
    assert "Enhanced CLI Features" in content
    assert "--compare" in content
    assert "--charts" in content
    assert "--no-color" in content
    assert "--config" in content
    assert "config.yaml" in content
    assert "export NO_COLOR=1" in content
