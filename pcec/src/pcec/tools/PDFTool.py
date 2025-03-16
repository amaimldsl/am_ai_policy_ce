# tools/PDFTool.py - Enhanced version
from typing import Optional, List, Dict, Any
from crewai.tools import BaseTool
from pathlib import Path
import os
import re
import logging

logger = logging.getLogger(__name__)

class PDFTool(BaseTool):
    name: str = "PDF Extraction Tool"
    description: str = "Extracts text from preprocessed PDF chunks or searches within them."

    def _run(
        self, 
        chunk_path: Optional[str] = None,
        chunk_index: Optional[int] = None,
        query: Optional[str] = None,
        process_all: bool = False,
        **kwargs
    ) -> str:
        try:
            # Find the preprocessed directory
            base_dir_candidates = [
                Path(__file__).resolve().parent.parent,
                Path(__file__).resolve().parent.parent.parent,
                Path.cwd(),
                Path.cwd() / "src" / "pcec"
            ]
            
            preprocessed_dir = None
            for base_dir in base_dir_candidates:
                candidate = base_dir / "preprocessed"
                if candidate.exists() and candidate.is_dir():
                    preprocessed_dir = candidate
                    break
            
            if not preprocessed_dir:
                preprocessed_dir = Path(__file__).resolve().parent.parent / "preprocessed"
                preprocessed_dir.mkdir(exist_ok=True)
                
            # Process all chunks if requested
            if process_all:
                return self._process_all_chunks(preprocessed_dir)
            
            # List available chunks if no specific chunk is requested
            if (chunk_path is None or chunk_path == "") and chunk_index is None:
                return self._list_available_chunks(preprocessed_dir)
            
            # Get chunk by index if specified
            if chunk_index is not None:
                chunk_path = self._get_chunk_by_index(preprocessed_dir, chunk_index)
                if isinstance(chunk_path, str):
                    return chunk_path  # Error message
            
            # Handle chunk path
            if isinstance(chunk_path, str):
                chunk_path = Path(chunk_path)
                if not chunk_path.is_absolute():
                    chunk_path = preprocessed_dir / chunk_path
            
            # Read the chunk file
            if not chunk_path.exists():
                return f"Chunk file not found: {chunk_path}"
            
            # Read content with size limit check
            text = self._read_chunk_with_limit(chunk_path)
            
            # Search if query is provided
            if query:
                return self._search_in_text(text, query)
            
            return text
            
        except Exception as e:
            logger.error(f"Error in PDFTool: {str(e)}", exc_info=True)
            return f"Error processing chunk: {str(e)}\nPlease try again with a different approach or contact support."

    def _list_available_chunks(self, preprocessed_dir: Path) -> str:
        """List all available chunks in the preprocessed directory"""
        chunks = list(preprocessed_dir.glob("*.txt"))
        if not chunks:
            return "No preprocessed chunks found. Please run document_processor.py first."
        
        return f"Available chunks ({len(chunks)}):\n" + "\n".join(
            f"{i}: {chunk.name}" for i, chunk in enumerate(chunks)
        )
    
    def _get_chunk_by_index(self, preprocessed_dir: Path, chunk_index: int) -> Path:
        """Get a chunk file by its index"""
        chunks = list(preprocessed_dir.glob("*.txt"))
        if not chunks:
            return "No preprocessed chunks found. Please run document_processor.py first."
            
        if 0 <= chunk_index < len(chunks):
            return chunks[chunk_index]
        else:
            return f"Invalid chunk index. Please specify a value between 0 and {len(chunks)-1}."
    
    def _read_chunk_with_limit(self, chunk_path: Path) -> str:
        """Read a chunk file with size limits"""
        with open(chunk_path, "r", encoding="utf-8") as f:
            text = f.read()
        
        # Limit text size to prevent issues with LLM token limits
        MAX_TEXT_LENGTH = 15000
        if len(text) > MAX_TEXT_LENGTH:
            logger.warning(f"Chunk text too large ({len(text)} chars), truncating to {MAX_TEXT_LENGTH} chars")
            text = text[:MAX_TEXT_LENGTH] + "\n\n[Note: Text truncated due to size constraints]"
        
        return text
    
    def _search_in_text(self, text: str, query: str) -> str:
        """Search for query in text with context"""
        search_results = self.search_text(text, query)
        
        if not search_results:
            return f"No matches found for query: '{query}'"
        
        # Limit search results size
        MAX_TEXT_LENGTH = 15000
        combined_results = "\n".join(search_results)
        if len(combined_results) > MAX_TEXT_LENGTH:
            return f"Search results for '{query}' (truncated to {MAX_TEXT_LENGTH} chars):\n\n" + combined_results[:MAX_TEXT_LENGTH]
        
        return f"Search results for '{query}':\n\n" + combined_results
    
    def _process_all_chunks(self, preprocessed_dir: Path) -> str:
        """Process all chunks and extract key requirements"""
        chunks = list(preprocessed_dir.glob("*.txt"))
        if not chunks:
            return "No preprocessed chunks found. Please run document_processor.py first."
        
        # Limit to first 5 chunks to avoid overwhelming the LLM
        if len(chunks) > 5:
            chunks = chunks[:5]
            summary = f"Processing first 5 of {len(chunks)} available chunks:\n"
        else:
            summary = f"Processing all {len(chunks)} available chunks:\n"
        
        # Add chunk names to summary
        for i, chunk in enumerate(chunks):
            summary += f"{i}: {chunk.name}\n"
        
        return summary

    def search_text(self, text: str, query: str) -> List[str]:
        """Search for query in text and return matching sections with context"""
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
            try:
                # Look for requirements using keywords
                requirement_keywords = ['shall', 'must', 'should', 'required', 'obligated', 'necessary', 
                                        'mandatory', 'comply', 'compliance', 'adhere']
                
                for keyword in requirement_keywords:
                    if keyword.lower() in query.lower() or query.lower() in keyword.lower():
                        # Search for lines containing requirement keywords
                        for i, line in enumerate(lines):
                            for req_keyword in requirement_keywords:
                                if req_keyword.lower() in line.lower():
                                    start = max(0, i-1)
                                    end = min(len(lines), i+2)
                                    context = "\n".join(lines[start:end])
                                    results.append(f"{context}\n---")
                                    
                                    # Limit to prevent overwhelming results
                                    if len(results) >= 10:
                                        return results
            except Exception as e:
                logger.warning(f"Error in advanced search: {str(e)}")
                # Fallback to simple substring search
                for i, line in enumerate(lines):
                    if query.lower() in line.lower():
                        start = max(0, i-1)
                        end = min(len(lines), i+2)
                        context = "\n".join(lines[start:end])
                        results.append(f"{context}\n---")
        
        return results