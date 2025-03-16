# Expand pdftest.py to test the new tools
from pathlib import Path
from tools.PDFTool import PDFTool
from tools.FileIOTool import FileIOTool
import document_processor

def test_pdf_extraction():
    """Test script to verify PDF extraction functionality"""
    print("\n===== TESTING PDF TOOL =====")
    pdf_tool = PDFTool()
    
    # Try with compatible params
    result = pdf_tool.run(chunk_path="", chunk_index=None, query="")
    print("Test result:", result[:200] + "..." if len(result) > 200 else result)
    
    # Test listing available chunks
    print("\n===== TESTING CHUNK LISTING =====")
    chunks_list = pdf_tool._run(chunk_path="", chunk_index=None, query="")
    print(chunks_list)
    
    # If you have created chunks already, try accessing one by index
    if "Available chunks" in chunks_list and "0:" in chunks_list:
        print("\n===== TESTING SINGLE CHUNK EXTRACTION =====")
        single_chunk_text = pdf_tool._run(chunk_path="", chunk_index=0, query="")
        print(f"Total extracted text length: {len(single_chunk_text)}")
        print("Sample of extracted text:")
        print(single_chunk_text[:500] + "...\n")
        
        # Count pages in single extraction
        page_count = single_chunk_text.count("[Page ")
        doc_count = single_chunk_text.count("[Document:")
        print(f"Number of pages extracted: {page_count}")
        print(f"Number of documents referenced: {doc_count}")
        
        # Test search within chunk
        print("\n===== TESTING SEARCH FUNCTIONALITY =====")
        search_result = pdf_tool._run(chunk_path="", chunk_index=0, query="shall")
        print(search_result[:500] + "..." if len(search_result) > 500 else search_result)
    else:
        print("\n⚠️ WARNING: No preprocessed chunks found. Please run document_processor.py first.")
        return {
            "error": "No preprocessed chunks available"
        }
    
    # Test FileIOTool
    print("\n===== TESTING FILE IO TOOL =====")
    file_io_tool = FileIOTool()
    
    # Write a test file
    test_content = "This is a test file."
    write_result = file_io_tool._run(action="write", filepath="test_file.txt", content=test_content)
    print(write_result)
    
    # Read the test file
    read_result = file_io_tool._run(action="read", filepath="test_file.txt")
    print(f"Read result: {read_result}")
    print(f"Read matches write: {read_result == test_content}")
    
    return {
        "chunk_extraction": {
            "text_length": len(single_chunk_text) if 'single_chunk_text' in locals() else 0,
            "page_count": page_count if 'page_count' in locals() else 0,
            "doc_count": doc_count if 'doc_count' in locals() else 0,
            "file_io_test": read_result == test_content if 'read_result' in locals() else False
        }
    }