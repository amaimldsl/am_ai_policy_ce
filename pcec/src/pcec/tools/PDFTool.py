# tools/PDFTool.py - Fixed version
from typing import Optional, List, Dict, Any
from crewai.tools import BaseTool
from pathlib import Path
import os
import re


class PDFTool(BaseTool):
    name: str = "PDF Extraction Tool"
    description: str = "Extracts text from preprocessed PDF chunks or searches within them."

    def _run(
        self, 
        chunk_path: Optional[str] = None,
        chunk_index: Optional[int] = None,
        query: Optional[str] = None,
        **kwargs  # Add this to accept any additional parameters
    ) -> str:
        try:
            base_dir = Path(__file__).resolve().parent.parent
            preprocessed_dir = base_dir / "preprocessed"
            
            # List available chunks if no specific chunk is requested
            if (chunk_path is None or chunk_path == "") and chunk_index is None:
                chunks = list(preprocessed_dir.glob("*.txt"))
                if not chunks:
                    return "No preprocessed chunks found. Please run document_processor.py first."
                
                return f"Available chunks ({len(chunks)}):\n" + "\n".join(
                    f"{i}: {chunk.name}" for i, chunk in enumerate(chunks)
                )
            
            # Get chunk by index if specified
            if chunk_index is not None:
                chunks = list(preprocessed_dir.glob("*.txt"))
                if 0 <= chunk_index < len(chunks):
                    chunk_path = chunks[chunk_index]
                else:
                    return f"Invalid chunk index. Please specify a value between 0 and {len(chunks)-1}."
            
            # Handle chunk path
            if isinstance(chunk_path, str):
                chunk_path = Path(chunk_path)
                if not chunk_path.is_absolute():
                    chunk_path = preprocessed_dir / chunk_path
            
            # Read the chunk file
            if not chunk_path.exists():
                return f"Chunk file not found: {chunk_path}"
            
            with open(chunk_path, "r", encoding="utf-8") as f:
                text = f.read()
            
            # Search if query is provided
            if query:
                search_results = self.search_text(text, query)
                if not search_results:
                    return f"No matches found for query: '{query}'"
                return f"Search results for '{query}':\n\n" + "\n".join(search_results)
            
            return text
            
        except Exception as e:
            import traceback
            return f"Error processing chunk: {str(e)}\n{traceback.format_exc()}"

    def search_text(self, text, query):
        # More sophisticated search that returns context
        results = []
        lines = text.split('\n')
        
        # Simple search for exact matches with context
        for i, line in enumerate(lines):
            if query.lower() in line.lower():
                # Get context (lines before and after match)
                start = max(0, i-1)
                end = min(len(lines), i+2)
                context = "\n".join(lines[start:end])
                results.append(f"{context}\n---")
        
        # If no exact matches, try to find partial matches or similar content
        if not results:
            # Case-insensitive pattern matching
            pattern = re.compile(r'.*' + re.escape(query) + r'.*', re.IGNORECASE)
            for i, line in enumerate(lines):
                if pattern.search(line):
                    start = max(0, i-1)
                    end = min(len(lines), i+2)
                    context = "\n".join(lines[start:end])
                    results.append(f"{context}\n---")
        
        return results