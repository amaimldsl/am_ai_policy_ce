# tools/FileIOTool.py - Enhanced version
from typing import Optional
from crewai.tools import BaseTool
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class FileIOTool(BaseTool):
    name: str = "File IO Tool"
    description: str = "Reads and writes task outputs for data exchange between agents."
    
    def _run(self, 
             action: str = "read",  # "read" or "write"
             filepath: str = "", 
             content: Optional[str] = None,
             **kwargs) -> str:
        try:
            # Find the output directory
            output_dir_candidates = [
                Path(__file__).resolve().parent.parent / "output",
                Path(__file__).resolve().parent.parent.parent / "output",
                Path.cwd() / "output",
                Path.cwd() / "src" / "pcec" / "output"
            ]
            
            output_dir = None
            for candidate in output_dir_candidates:
                if candidate.exists() and candidate.is_dir():
                    output_dir = candidate
                    break
            
            if not output_dir:
                output_dir = Path(__file__).resolve().parent.parent / "output"
                output_dir.mkdir(exist_ok=True)
                
            # Resolve the full path
            filepath = output_dir / filepath
            
            if action == "read":
                return self._read_file(filepath)
            elif action == "write":
                return self._write_file(filepath, content)
            else:
                return f"Invalid action: {action}. Use 'read' or 'write'."
                
        except Exception as e:
            logger.error(f"Unexpected error in FileIOTool: {str(e)}", exc_info=True)
            return f"Unexpected error: {str(e)}"
    
    def _read_file(self, filepath: Path) -> str:
        """Read from a file with size limit handling"""
        if not filepath.exists():
            return f"File not found: {filepath}"
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                
            # Limit content size to prevent issues with LLM token limits
            MAX_CONTENT_LENGTH = 15000
            if len(content) > MAX_CONTENT_LENGTH:
                logger.warning(f"File content too large ({len(content)} chars), truncating to {MAX_CONTENT_LENGTH} chars")
                content = content[:MAX_CONTENT_LENGTH] + "\n\n[Note: Content truncated due to size constraints]"
                
            return content
        except Exception as e:
            logger.error(f"Error reading file {filepath}: {str(e)}", exc_info=True)
            return f"Error reading file {filepath}: {str(e)}"
    
    def _write_file(self, filepath: Path, content: Optional[str]) -> str:
        """Write to a file with size limit handling"""
        try:
            filepath.parent.mkdir(exist_ok=True)
            
            # Ensure content is not None
            if content is None:
                content = ""
                
            # Limit content size when writing
            MAX_CONTENT_LENGTH = 100000
            if len(content) > MAX_CONTENT_LENGTH:
                logger.warning(f"Content too large ({len(content)} chars), truncating to {MAX_CONTENT_LENGTH} chars")
                content = content[:MAX_CONTENT_LENGTH] + "\n\n[Note: Content truncated due to size constraints]"
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Content written to {filepath}"
        except Exception as e:
            logger.error(f"Error writing to file {filepath}: {str(e)}", exc_info=True)
            return f"Error writing to file {filepath}: {str(e)}"