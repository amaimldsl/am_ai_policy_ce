# pdftest.py - Tool testing module
from pathlib import Path
import logging
import os
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("pdftest.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def find_tools_directory():
    """Find the tools directory from various possible locations"""
    tools_dir_candidates = [
        Path(__file__).resolve().parent / "tools",
        Path(__file__).resolve().parent.parent / "tools",
        Path.cwd() / "tools",
        Path.cwd() / "src" / "pcec" / "tools"
    ]
    
    for candidate in tools_dir_candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate
    
    # If not found, use the script directory
    return Path(__file__).resolve().parent / "tools"

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
    
    # If not found, use the script directory
    return Path(__file__).resolve().parent / "preprocessed"

def test_pdf_extraction():
    """Test script to verify PDF extraction functionality"""
    try:
        # Add tools directory to path
        tools_dir = find_tools_directory()
        if tools_dir not in sys.path:
            sys.path.append(str(tools_dir.parent))
        
        # Import the tools
        try:
            from tools.PDFTool import PDFTool
            from tools.FileIOTool import FileIOTool
        except ImportError as e:
            logger.error(f"Error importing tools: {str(e)}")
            return {
                "error": f"Could not import tools: {str(e)}"
            }
        
        logger.info("\n===== TESTING PDF TOOL =====")
        pdf_tool = PDFTool()
        
        # Try with compatible params
        result = pdf_tool.run(chunk_path="", chunk_index=None, query="")
        logger.info(f"Test result: {result[:200] + '...' if len(result) > 200 else result}")
        
        # Test listing available chunks
        logger.info("\n===== TESTING CHUNK LISTING =====")
        chunks_list = pdf_tool._run(chunk_path="", chunk_index=None, query="")
        logger.info(chunks_list)
        
        # If you have created chunks already, try accessing one by index
        if "Available chunks" in chunks_list and "0:" in chunks_list:
            logger.info("\n===== TESTING SINGLE CHUNK EXTRACTION =====")
            single_chunk_text = pdf_tool._run(chunk_path="", chunk_index=0, query="")
            logger.info(f"Total extracted text length: {len(single_chunk_text)}")
            logger.info(f"Sample of extracted text:\n{single_chunk_text[:500] + '...'}\n")
            
            # Count pages in single extraction
            page_count = single_chunk_text.count("[Page ")
            doc_count = single_chunk_text.count("[Document:")
            logger.info(f"Number of pages extracted: {page_count}")
            logger.info(f"Number of documents referenced: {doc_count}")
            
            # Test search within chunk
            logger.info("\n===== TESTING SEARCH FUNCTIONALITY =====")
            search_result = pdf_tool._run(chunk_path="", chunk_index=0, query="shall")
            logger.info(f"{search_result[:500] + '...' if len(search_result) > 500 else search_result}")
        else:
            logger.warning("\n⚠️ WARNING: No preprocessed chunks found. Please run document_processor.py first.")
            return {
                "error": "No preprocessed chunks available"
            }
        
        # Test FileIOTool
        logger.info("\n===== TESTING FILE IO TOOL =====")
        file_io_tool = FileIOTool()
        
        # Write a test file
        test_content = "This is a test file."
        write_result = file_io_tool._run(action="write", filepath="test_file.txt", content=test_content)
        logger.info(write_result)
        
        # Read the test file
        read_result = file_io_tool._run(action="read", filepath="test_file.txt")
        logger.info(f"Read result: {read_result}")
        logger.info(f"Read matches write: {read_result == test_content}")
        
        return {
            "chunk_extraction": {
                "text_length": len(single_chunk_text) if 'single_chunk_text' in locals() else 0,
                "page_count": page_count if 'page_count' in locals() else 0,
                "doc_count": doc_count if 'doc_count' in locals() else 0,
                "file_io_test": read_result == test_content if 'read_result' in locals() else False
            }
        }
    except Exception as e:
        logger.error(f"Error testing PDF extraction: {str(e)}", exc_info=True)
        return {
            "error": f"Test failed: {str(e)}"
        }

# If run directly, execute the test
if __name__ == "__main__":
    test_results = test_pdf_extraction()
    
    if "error" in test_results:
        logger.error(f"Test failed: {test_results['error']}")
        sys.exit(1)
    else:
        logger.info("Tests completed successfully!")
        sys.exit(0)