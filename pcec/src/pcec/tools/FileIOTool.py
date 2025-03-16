# tools/FileIOTool.py
from typing import Optional
from crewai.tools import BaseTool
from pathlib import Path

class FileIOTool(BaseTool):
    name: str = "File IO Tool"
    description: str = "Reads and writes task outputs for data exchange between agents."
    
    def _run(self, 
             action: str = "read",  # "read" or "write"
             filepath: str = "", 
             content: Optional[str] = None,
             **kwargs) -> str:
        output_dir = Path(__file__).resolve().parent.parent / "output"
        filepath = output_dir / filepath
        
        if action == "read":
            if not filepath.exists():
                return f"File not found: {filepath}"
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        elif action == "write":
            filepath.parent.mkdir(exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Content written to {filepath}"
        else:
            return f"Invalid action: {action}. Use 'read' or 'write'."