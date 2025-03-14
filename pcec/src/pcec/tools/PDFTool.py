import pdfplumber
from crewai.tools import BaseTool
from pathlib import Path
import os
import re

class PDFTool(BaseTool):
    name: str = "PDF Extraction Tool"
    description: str = "Extracts text from PDF files and performs searches within the extracted content."

    def _run(self, pdf_path: str = None, query: str = None, page_range: str = None) -> str:
        try:
            # Default to p.pdf if no path is provided
            if not pdf_path or pdf_path == "":
                base_dir = Path(__file__).resolve().parent  # path to tool.py
                pdf_path = base_dir.parent / 'policy/document.pdf'  # going up one level, then into the policy directory
            else:
                # If path is provided but doesn't exist, try to resolve it
                pdf_path = Path(pdf_path)
                if not pdf_path.exists():
                    base_dir = Path(__file__).resolve().parent
                    pdf_path = base_dir.parent / 'policy' / pdf_path.name

            # Validate the PDF exists
            if not os.path.exists(pdf_path):
                return f"Error: PDF file not found at {pdf_path}"
                
            print(f"Attempting to read PDF from: {pdf_path}")
            
            # Extract text from PDF based on optional page range
            text = self.extract_text_from_pdf(pdf_path, page_range)
            
            # Return search results if query is provided, otherwise return all text
            if query:
                search_results = self.search_text(text, query)
                if not search_results:
                    return f"No matches found for query: '{query}'"
                return f"Search results for '{query}':\n\n" + "\n".join(search_results)
            
            return text
            
        except Exception as e:
            return f"Error processing PDF: {str(e)}"

    def extract_text_from_pdf(self, pdf_path, page_range=None):
        text = []
        with pdfplumber.open(pdf_path) as pdf:
            # Process page range if specified (e.g., "1-5" or "3,7,9")
            if page_range:
                pages_to_extract = []
                
                # Handle comma-separated list of pages
                if "," in page_range:
                    for page_num in page_range.split(","):
                        try:
                            pages_to_extract.append(int(page_num.strip()) - 1)  # Convert to 0-based index
                        except ValueError:
                            pass
                
                # Handle range of pages (e.g., "1-5")
                elif "-" in page_range:
                    try:
                        start, end = page_range.split("-")
                        start_page = int(start.strip()) - 1  # Convert to 0-based
                        end_page = int(end.strip())  # Inclusive
                        pages_to_extract = range(start_page, end_page)
                    except ValueError:
                        # If range parsing fails, extract all pages
                        pages_to_extract = range(len(pdf.pages))
                
                # If we have valid pages to extract
                if pages_to_extract:
                    for i in pages_to_extract:
                        if 0 <= i < len(pdf.pages):
                            page_text = pdf.pages[i].extract_text()
                            if page_text:
                                text.append(f"[Page {i+1}]\n{page_text.strip()}")
                    return "\n\n".join(text)
            
            # Default: process all pages
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    text.append(f"[Page {i+1}]\n{page_text.strip()}")
        
        return "\n\n".join(text)

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