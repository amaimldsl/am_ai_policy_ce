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
            output_dir = Path(__file__).resolve().parent.parent / "output"
            filepath = output_dir / filepath
            
            if action == "read":
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
                    
            elif action == "write":
                try:
                    filepath.parent.mkdir(exist_ok=True)
                    
                    # Limit content size when writing
                    MAX_CONTENT_LENGTH = 100000
                    if content and len(content) > MAX_CONTENT_LENGTH:
                        logger.warning(f"Content too large ({len(content)} chars), truncating to {MAX_CONTENT_LENGTH} chars")
                        content = content[:MAX_CONTENT_LENGTH] + "\n\n[Note: Content truncated due to size constraints]"
                    
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(content)
                    return f"Content written to {filepath}"
                except Exception as e:
                    logger.error(f"Error writing to file {filepath}: {str(e)}", exc_info=True)
                    return f"Error writing to file {filepath}: {str(e)}"
            else:
                return f"Invalid action: {action}. Use 'read' or 'write'."
        except Exception as e:
            logger.error(f"Unexpected error in FileIOTool: {str(e)}", exc_info=True)
            return f"Unexpected error: {str(e)}"