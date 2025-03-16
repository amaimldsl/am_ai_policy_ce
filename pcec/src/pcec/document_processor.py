# document_processor.py - Create this new script
from pathlib import Path
import glob
import pdfplumber
import os

def list_policy_documents():
    """List all PDF files in the policy directory."""
    base_dir = Path(__file__).resolve().parent
    policy_dir = base_dir / 'policy'
    pdf_files = list(policy_dir.glob("*.pdf"))
    return pdf_files

def count_pages(pdf_path):
    """Count the number of pages in a PDF."""
    with pdfplumber.open(pdf_path) as pdf:
        return len(pdf.pages)

def extract_text_from_pdf(pdf_path, start_page=0, end_page=None):
    """Extract text from a PDF, limited to specific page range."""
    text = []
    doc_name = pdf_path.name
    
    with pdfplumber.open(pdf_path) as pdf:
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
    
    return "\n\n".join(text)


def preprocess_documents(chunk_size=10):  # Reduced from 15 to 10 pages per chunk
    """
    Preprocess all PDF documents and save them as chunks.
    Returns a list of chunk files that can be processed by agents.
    """
    output_dir = Path(__file__).resolve().parent / "preprocessed"
    output_dir.mkdir(exist_ok=True)
    
    pdf_files = list_policy_documents()
    chunk_files = []
    
    for pdf_idx, pdf_file in enumerate(pdf_files):
        pages = count_pages(pdf_file)
        print(f"Processing {pdf_file.name} ({pages} pages)")
        
        for chunk_idx in range(0, (pages + chunk_size - 1) // chunk_size):
            start_page = chunk_idx * chunk_size
            end_page = min((chunk_idx + 1) * chunk_size, pages)
            
            # Extract with smaller chunk size
            chunk_text = extract_text_from_pdf(pdf_file, start_page, end_page)
            
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
                output_file_1 = output_dir / f"doc_{pdf_idx}_{pdf_file.stem}_pages_{start_page+1}-{start_page+((end_page-start_page)//2)}.txt"
                with open(output_file_1, "w", encoding="utf-8") as f:
                    f.write(chunk_text_1)
                chunk_files.append(output_file_1)
                
                # Save the second half
                output_file_2 = output_dir / f"doc_{pdf_idx}_{pdf_file.stem}_pages_{start_page+((end_page-start_page)//2)+1}-{end_page}.txt"
                with open(output_file_2, "w", encoding="utf-8") as f:
                    f.write(chunk_text_2)
                chunk_files.append(output_file_2)
                
                print(f"  Split and saved chunk {chunk_idx+1}/{(pages + chunk_size - 1) // chunk_size} into two parts")
            else:
                # Save as a single chunk if not too large
                output_file = output_dir / f"doc_{pdf_idx}_{pdf_file.stem}_pages_{start_page+1}-{end_page}.txt"
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(chunk_text)
                chunk_files.append(output_file)
                print(f"  Saved chunk {chunk_idx+1}/{(pages + chunk_size - 1) // chunk_size}: {output_file.name}")
    
    # Save list of chunks for easy reference
    with open(output_dir / "chunk_index.txt", "w", encoding="utf-8") as f:
        for idx, chunk_file in enumerate(chunk_files):
            f.write(f"{idx}: {chunk_file.name}\n")
    
    print(f"Created {len(chunk_files)} document chunks for processing")
    return chunk_files