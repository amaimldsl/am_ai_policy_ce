# document_processor.py
from pathlib import Path
import glob
import logging
import os
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("document_processor.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def find_policy_directory():
    """Find the policy directory from various possible locations"""
    policy_dir_candidates = [
        Path(__file__).resolve().parent / "policy",
        Path(__file__).resolve().parent.parent / "policy",
        Path.cwd() / "policy",
        Path.cwd() / "src" / "pcec" / "policy"
    ]
    
    for candidate in policy_dir_candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate
    
    # If not found, create in the script directory
    policy_dir = Path(__file__).resolve().parent / "policy"
    policy_dir.mkdir(exist_ok=True)
    return policy_dir

def find_preprocessed_directory():
    """Find the preprocessed directory from various possible locations"""
    preprocessed_dir_candidates = [
        Path(__file__).resolve().parent / "preprocessed",
        Path(__file__).resolve().parent.parent / "preprocessed",
        Path.cwd() / "preprocessed",
        Path.cwd() / "src" / "pcec" / "preprocessed"
    ]
    
    for candidate in preprocessed_dir_candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate
    
    # If not found, create in the script directory
    preprocessed_dir = Path(__file__).resolve().parent / "preprocessed"
    preprocessed_dir.mkdir(exist_ok=True)
    return preprocessed_dir

def list_policy_documents():
    """List all PDF files in the policy directory."""
    policy_dir = find_policy_directory()
    pdf_files = list(policy_dir.glob("*.pdf"))
    
    # If no PDFs found, look for text files as fallback
    if not pdf_files:
        text_files = list(policy_dir.glob("*.txt"))
        if text_files:
            logger.warning("No PDF files found. Using text files instead.")
            return text_files
        else:
            # Create an example policy file if nothing exists
            example_file = policy_dir / "example_policy.txt"
            if not example_file.exists():
                with open(example_file, "w") as f:
                    f.write("""# Example Policy Document

This is an example policy document. Replace this with actual PDF policy documents.

## Sample Requirements

1. All employees shall complete security awareness training annually.
2. Passwords must be changed every 90 days.
3. Access to production systems should be reviewed quarterly.
4. Vendors are required to sign NDAs before accessing company data.
5. Security incidents must be reported within 24 hours.
""")
                logger.info(f"Created example policy file: {example_file}")
            return [example_file]
    
    return pdf_files

def count_pages(file_path):
    """Count the number of pages in a document file."""
    try:
        # Check if file is PDF or text
        if file_path.suffix.lower() == '.pdf':
            try:
                import pdfplumber
                with pdfplumber.open(file_path) as pdf:
                    return len(pdf.pages)
            except ImportError:
                logger.warning("pdfplumber not installed. Treating PDF as single page.")
                return 1
            except Exception as e:
                logger.error(f"Error reading PDF: {str(e)}")
                return 1
        else:
            # For text files, count lines and estimate pages (1 page = ~50 lines)
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                line_count = sum(1 for _ in f)
            return max(1, line_count // 50 + (1 if line_count % 50 > 0 else 0))
    except Exception as e:
        logger.error(f"Error counting pages: {str(e)}")
        return 1

def extract_text_from_file(file_path, start_page=0, end_page=None):
    """Extract text from a document file, limited to specific page range."""
    text = []
    doc_name = file_path.name
    
    try:
        # Handle PDF files
        if file_path.suffix.lower() == '.pdf':
            try:
                import pdfplumber
                with pdfplumber.open(file_path) as pdf:
                    total_pages = len(pdf.pages)
                    if end_page is None:
                        end_page = total_pages
                    
                    end_page = min(end_page, total_pages)
                    
                    for i in range(start_page, end_page):
                        try:
                            page_text = pdf.pages[i].extract_text()
                            if page_text:
                                text.append(f"[Document: {doc_name}, Page {i+1}]\n{page_text.strip()}")
                        except Exception as e:
                            text.append(f"[Document: {doc_name}, Page {i+1}]\nError extracting text: {str(e)}")
            except ImportError:
                logger.warning("pdfplumber not installed. Trying to read PDF as text.")
                with open(file_path, 'rb') as f:
                    try:
                        content = f.read().decode('utf-8', errors='replace')
                        text.append(f"[Document: {doc_name}]\n{content}")
                    except:
                        text.append(f"[Document: {doc_name}]\nCould not extract text from PDF.")
        else:
            # Handle text files
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                # Estimate page breaks (every 3000 characters)
                page_size = 3000
                if end_page is None:
                    end_page = (len(content) + page_size - 1) // page_size
                
                start_char = start_page * page_size
                end_char = min(len(content), end_page * page_size)
                
                # Extract the requested range
                content_part = content[start_char:end_char]
                
                # Add document header
                text.append(f"[Document: {doc_name}, Pages {start_page+1}-{end_page}]\n{content_part}")
    except Exception as e:
        logger.error(f"Error extracting text from {file_path}: {str(e)}")
        text.append(f"[Document: {doc_name}]\nError extracting text: {str(e)}")
    
    return "\n\n".join(text)

def preprocess_documents(chunk_size=10):
    """
    Preprocess all document files and save them as chunks.
    Returns a list of chunk files that can be processed by agents.
    """
    try:
        preprocessed_dir = find_preprocessed_directory()
        
        pdf_files = list_policy_documents()
        chunk_files = []
        
        for pdf_idx, pdf_file in enumerate(pdf_files):
            pages = count_pages(pdf_file)
            logger.info(f"Processing {pdf_file.name} ({pages} pages)")
            
            for chunk_idx in range(0, (pages + chunk_size - 1) // chunk_size):
                start_page = chunk_idx * chunk_size
                end_page = min((chunk_idx + 1) * chunk_size, pages)
                
                # Extract with smaller chunk size
                chunk_text = extract_text_from_file(pdf_file, start_page, end_page)
                
                # If chunk is very large, split it further
                if len(chunk_text) > 10000:  # Limit chunk size to around 10K characters
                    midpoint = len(chunk_text) // 2
                    # Find a newline near the midpoint to split cleanly
                    split_point = chunk_text.find('\n', midpoint)
                    if split_point == -1:
                        split_point = midpoint
                    
                    chunk_text_1 = chunk_text[:split_point]
                    chunk_text_2 = chunk_text[split_point:]
                    
                    # Save the first half
                    output_file_1 = preprocessed_dir / f"doc_{pdf_idx}_{pdf_file.stem}_pages_{start_page+1}-{start_page+((end_page-start_page)//2)}.txt"
                    with open(output_file_1, "w", encoding="utf-8") as f:
                        f.write(chunk_text_1)
                    chunk_files.append(output_file_1)
                    
                    # Save the second half
                    output_file_2 = preprocessed_dir / f"doc_{pdf_idx}_{pdf_file.stem}_pages_{start_page+((end_page-start_page)//2)+1}-{end_page}.txt"
                    with open(output_file_2, "w", encoding="utf-8") as f:
                        f.write(chunk_text_2)
                    chunk_files.append(output_file_2)
                    
                    logger.info(f"  Split and saved chunk {chunk_idx+1}/{(pages + chunk_size - 1) // chunk_size} into two parts")
                else:
                    # Save as a single chunk if not too large
                    output_file = preprocessed_dir / f"doc_{pdf_idx}_{pdf_file.stem}_pages_{start_page+1}-{end_page}.txt"
                    with open(output_file, "w", encoding="utf-8") as f:
                        f.write(chunk_text)
                    chunk_files.append(output_file)
                    logger.info(f"  Saved chunk {chunk_idx+1}/{(pages + chunk_size - 1) // chunk_size}: {output_file.name}")
        
        # Save list of chunks for easy reference
        with open(preprocessed_dir / "chunk_index.txt", "w", encoding="utf-8") as f:
            for idx, chunk_file in enumerate(chunk_files):
                f.write(f"{idx}: {chunk_file.name}\n")
        
        logger.info(f"Created {len(chunk_files)} document chunks for processing")
        return chunk_files
        
    except Exception as e:
        logger.error(f"Error preprocessing documents: {str(e)}")
        logger.error(traceback.format_exc())
        return []

# If this script is run directly, preprocess documents
if __name__ == "__main__":
    logger.info("Starting document preprocessing...")
    chunks = preprocess_documents()
    logger.info(f"Preprocessing complete. Created {len(chunks)} chunks.")