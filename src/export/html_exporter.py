"""
HTML Exporter module for Microanalyst.
Handles rendering of report data to HTML using Jinja2 templates.
"""
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader, select_autoescape

def export_to_html(data: Dict[str, Any], filepath: Path) -> None:
    """
    Exports data to an HTML file using Jinja2 template.
    
    Args:
        data: Dictionary of data to render.
        filepath: Path to the output file.
        
    Raises:
        IOError: If file writing fails.
        TemplateError: If template rendering fails.
    """
    # Setup Jinja2 Environment
    template_dir = Path(__file__).parent / "templates"
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(['html', 'xml'])
    )
    
    try:
        template = env.get_template("report.html.jinja2")
        html_content = template.render(**data)
    except Exception as e:
        raise ValueError(f"Failed to render HTML template: {e}")

    # Ensure parent directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    # Atomic write
    temp_dir = filepath.parent
    try:
        with tempfile.NamedTemporaryFile(mode='w', dir=temp_dir, delete=False, encoding='utf-8') as tmp_file:
            tmp_file.write(html_content)
            temp_path = Path(tmp_file.name)
            
        shutil.move(str(temp_path), str(filepath))
        
    except (IOError, OSError) as e:
        if 'temp_path' in locals() and temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass
        raise IOError(f"Failed to export HTML to {filepath}: {e}")
