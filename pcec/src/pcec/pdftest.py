# Save this as pdftest.py in your pcec folder
from pathlib import Path
from tools.PDFTool import PDFTool  # Add this import statement
import document_processor  # Add this import statement


def test_pdf_extraction():
    """
    Test script to verify PDF extraction functionality
    """
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
    
    # Count policy-related terms to verify content
    shall_count = single_chunk_text.lower().count("shall") if 'single_chunk_text' in locals() else 0
    must_count = single_chunk_text.lower().count("must") if 'single_chunk_text' in locals() else 0
    should_count = single_chunk_text.lower().count("should") if 'single_chunk_text' in locals() else 0
    required_count = single_chunk_text.lower().count("required") if 'single_chunk_text' in locals() else 0
    
    print("\n===== POLICY KEYWORD ANALYSIS =====")
    print(f"'shall' occurrences: {shall_count}")
    print(f"'must' occurrences: {must_count}")
    print(f"'should' occurrences: {should_count}")
    print(f"'required' occurrences: {required_count}")
    
    return {
        "chunk_extraction": {
            "text_length": len(single_chunk_text) if 'single_chunk_text' in locals() else 0,
            "page_count": page_count if 'page_count' in locals() else 0,
            "doc_count": doc_count if 'doc_count' in locals() else 0,
            "policy_terms": {
                "shall": shall_count,
                "must": must_count,
                "should": should_count,
                "required": required_count
            }
        }
    }