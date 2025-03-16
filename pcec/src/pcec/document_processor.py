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

def preprocess_documents(chunk_size=15):
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
            
            chunk_text = extract_text_from_pdf(pdf_file, start_page, end_page)
            output_file = output_dir / f"doc_{pdf_idx}_{pdf_file.stem}_pages_{start_page+1}-{end_page}.txt"
            
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(chunk_text)
            
            chunk_files.append(output_file)
            print(f"  Saved chunk {chunk_idx+1}/{(pages + chunk_size - 1) // chunk_size}: {output_file.name}")
    
    # Save list of chunks for easy reference
    with open(output_dir / "chunk_index.txt", "w", encoding="utf-8") as f:
        for idx, chunk_file in enumerate(chunk_files):
            f.write(f"{idx}: {chunk_file.name}\n")
    
    return chunk_files

if __name__ == "__main__":
    print("Preprocessing policy documents...")
    chunks = preprocess_documents()
    print(f"Created {len(chunks)} document chunks for processing")