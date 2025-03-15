import pdfplumber
from crewai.tools import BaseTool
from pathlib import Path
import os
import re
import glob

class PDFTool(BaseTool):
    name: str = "PDF Extraction Tool"
    description: str = "Extracts text from PDF files, performs searches, and provides chunked processing to manage token limits."

    def _run(self, pdf_path: str = None, query: str = "", page_range: str = "all", 
             chunk_size: int = 1000, chunk_index: int = 0, 
             find_modal_verbs: bool = False) -> str:
        try:
            # Get the policy directory path
            base_dir = Path(__file__).resolve().parent
            policy_dir = base_dir.parent / 'policy'
            
            # Ensure policy directory exists
            policy_dir.mkdir(exist_ok=True)
            
            # If no specific PDF is requested or path doesn't exist, list available PDFs
            if not pdf_path or pdf_path == "" or pdf_path in ["provided_text", "path_to_pdf"]:
                # List all PDF files in the policy directory
                pdf_files = list(policy_dir.glob("*.pdf"))
                
                if not pdf_files:
                    return f"Error: No PDF files found in {policy_dir}. Please place PDF files in this directory."
                
                # If no specific PDF requested, use the first one found
                pdf_path = pdf_files[0]
                print(f"No specific PDF requested. Using: {pdf_path.name}")
            else:
                # If path is provided but doesn't exist, try to resolve it
                pdf_path = Path(pdf_path)
                if not pdf_path.exists():
                    # Try to find it in the policy directory
                    potential_path = policy_dir / pdf_path.name
                    if potential_path.exists():
                        pdf_path = potential_path
                    else:
                        # Check if any PDF file exists with a similar name
                        similar_files = list(policy_dir.glob(f"*{pdf_path.stem}*.pdf"))
                        if similar_files:
                            pdf_path = similar_files[0]
                        else:
                            # If still not found, use any available PDF
                            pdf_files = list(policy_dir.glob("*.pdf"))
                            if pdf_files:
                                pdf_path = pdf_files[0]
                                print(f"Requested PDF not found. Using available PDF: {pdf_path.name}")
                            else:
                                return f"Error: No PDF files found in {policy_dir}. Please place PDF files in this directory."

            # Validate the PDF exists
            if not os.path.exists(pdf_path):
                return f"Error: PDF file not found at {pdf_path}. Available PDFs: {[f.name for f in policy_dir.glob('*.pdf')]}"
                
            print(f"Reading PDF from: {pdf_path}")
            
            # If find_modal_verbs is True, pre-extract sentences with modal verbs
            if find_modal_verbs:
                # Handle batched processing for large documents
                if page_range == "all":
                    # Count total pages in the PDF
                    with pdfplumber.open(pdf_path) as pdf:
                        total_pages = len(pdf.pages)
                        
                    # Process in batches of 20 pages
                    batch_size = 20
                    all_modal_sentences = []
                    
                    # Process each batch
                    for start_page in range(1, total_pages + 1, batch_size):
                        end_page = min(start_page + batch_size - 1, total_pages)
                        batch_range = f"{start_page}-{end_page}"
                        print(f"Processing pages {batch_range}...")
                        
                        # Extract text for this batch
                        batch_text = self.extract_text_from_pdf(pdf_path, batch_range)
                        
                        # Find modal sentences in batch
                        batch_modal_sentences = self.extract_modal_sentences(batch_text)
                        if batch_modal_sentences:
                            all_modal_sentences.append(batch_modal_sentences)
                    
                    # Combine results from all batches
                    modal_sentences = "\n\n".join(all_modal_sentences)
                    if not modal_sentences.strip():
                        return f"No sentences with modal verbs found in {pdf_path.name}"
                    
                    return f"Extracted sentences with modal verbs and compliance indicators from {pdf_path.name} (all {total_pages} pages):\n\n{modal_sentences}"
                else:
                    # Extract text based on provided page range
                    text = self.extract_text_from_pdf(pdf_path, page_range)
                    modal_sentences = self.extract_modal_sentences(text)
                    
                    if not modal_sentences.strip():
                        return f"No sentences with modal verbs found in pages {page_range} of {pdf_path.name}"
                    
                    return f"Extracted sentences with modal verbs and compliance indicators from {pdf_path.name} (pages {page_range}):\n\n{modal_sentences}"
            
            # Extract text from PDF based on optional page range
            text = self.extract_text_from_pdf(pdf_path, page_range)
            
            # Process text in chunks if requested
            if chunk_size and chunk_index is not None:
                chunks = self.chunk_text(text, chunk_size)
                if 0 <= chunk_index < len(chunks):
                    return f"Chunk {chunk_index+1}/{len(chunks)} from {pdf_path.name}:\n\n{chunks[chunk_index]}"
                else:
                    return f"Error: Chunk index {chunk_index} is out of range. There are {len(chunks)} chunks available."
            
            # Return search results if query is provided, otherwise return all text
            if query and query.strip():
                search_results = self.search_text(text, query)
                if not search_results:
                    return f"No matches found for query: '{query}' in {pdf_path.name}"
                return f"Search results for '{query}' in {pdf_path.name}:\n\n" + "\n".join(search_results)
            
            return f"Full text from {pdf_path.name}:\n\n{text}"
            
        except Exception as e:
            return f"Error processing PDF: {str(e)}"

    def extract_text_from_pdf(self, pdf_path, page_range=None):
        text = []
        with pdfplumber.open(pdf_path) as pdf:
            # Process page range if specified (e.g., "1-5" or "3,7,9")
            if page_range and page_range.lower() != "all":
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
    
    def chunk_text(self, text, chunk_size):
        """Split text into chunks of approximately equal size."""
        words = text.split()
        chunks = []
        current_chunk = []
        current_size = 0
        
        for word in words:
            current_chunk.append(word)
            current_size += 1
            
            if current_size >= chunk_size:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_size = 0
                
        # Add the last chunk if there is any
        if current_chunk:
            chunks.append(" ".join(current_chunk))
            
        return chunks
    
    def extract_modal_sentences(self, text):
        """Extract sentences containing modal verbs and compliance indicators."""
        # Patterns to match sentences with modal verbs and compliance indicators
        modal_patterns = [
            r"(?i)[^.!?]*\b(shall|must|should|will|required to|obligated to)\b[^.!?]*[.!?]",
            r"(?i)[^.!?]*\b(may not|cannot|prohibited from|restricted from|not permitted to)\b[^.!?]*[.!?]",
            r"(?i)[^.!?]*\b(ensure that|provide|maintain|establish|comply with|in accordance with|adherence to)\b[^.!?]*[.!?]"
        ]
        
        extracted_sentences = []
        page_markers = re.findall(r"\[Page \d+\]", text)
        
        # Split text by page markers to maintain page references
        text_by_page = re.split(r"(\[Page \d+\])", text)
        current_page = "Unknown"
        
        for i in range(len(text_by_page)):
            if i % 2 == 0 and i > 0:  # This is content after a page marker
                page_content = text_by_page[i]
                # Split into sentences (simple approach)
                sentences = re.split(r'(?<=[.!?])\s+', page_content)
                
                for sentence in sentences:
                    # Check if sentence contains any of the modal patterns
                    for pattern in modal_patterns:
                        if re.search(pattern, sentence):
                            # Add the sentence with its page reference
                            extracted_sentences.append(f"{current_page}: {sentence.strip()}")
                            break
            else:  # This is a page marker
                if text_by_page[i].strip():
                    current_page = text_by_page[i].strip()
        
        return "\n\n".join(extracted_sentences)
        
    def list_available_pdfs(self):
        """List all available PDF files in the policy directory."""
        base_dir = Path(__file__).resolve().parent
        policy_dir = base_dir.parent / 'policy'
        policy_dir.mkdir(exist_ok=True)
        
        pdf_files = list(policy_dir.glob("*.pdf"))
        if not pdf_files:
            return "No PDF files found in the policy directory."
        
        return f"Available PDF files:\n" + "\n".join([f"- {pdf.name}" for pdf in pdf_files])