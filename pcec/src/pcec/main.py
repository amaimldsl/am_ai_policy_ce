import sys
import time
import traceback
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("crewai_run.log"),
        logging.StreamHandler()
    ]
)

from crew import pcec
from pdftest import test_pdf_extraction
import document_processor

def main():
    """Main function to run the policy compliance analysis."""
    try:
        logging.info("Testing PDF tool...")
        
        test_pdf_extraction()
        
        logging.info("Preprocessing documents...")
        document_processor.preprocess_documents()
        
        # Check if tools are available
        logging.info("Checking available tools...")
        tool_checks = [
            "PDFTool",
            "FileIOTool",
            "RiskAnalysisTool", 
            "ControlDesignTool",
            "AuditPlanningTool"
        ]
        
        for tool in tool_checks:
            try:
                # Simple check to see if the tool is importable
                exec(f"from tools.{tool} import {tool}")
                logging.info(f"✓ {tool} is available")
            except ImportError:
                logging.error(f"✗ {tool} is NOT available")
        
        logging.info("Starting Policy Compliance Analysis...")
        start_time = time.time()
        
        # Run the crew with error handling
        try:
            result = pcec.kickoff()
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            logging.info(f"✅ Analysis completed successfully in {execution_time:.2f} seconds!")
            logging.info(f"Task outputs have been saved to the output directory.")
            
            # You can still access the final result if needed
            logging.info(f"Final crew output length: {len(str(result))} characters")
        except Exception as crew_error:
            logging.error(f"Crew execution failed: {str(crew_error)}")
            logging.error("Attempting to save partial results...")
            
            # Try to save whatever was completed
            output_dir = Path(__file__).parent / "output"
            output_dir.mkdir(exist_ok=True)
            with open(output_dir / "partial_results.md", "w") as f:
                f.write(f"# Partial Results\n\nThe crew execution failed with error: {str(crew_error)}\n\n")
                f.write("Some tasks may have completed successfully. Check individual task output files.\n")
            
            return 1
        
        return 0
    
    except Exception as e:
        error_info = f"❌ ERROR: Analysis failed with exception: {str(e)}\n"
        error_info += "Detailed error information:\n"
        error_info += traceback.format_exc()
        
        # Save error information
        output_dir = Path(__file__).parent / "output"
        output_dir.mkdir(exist_ok=True)
        error_path = output_dir / f"error_log_{time.strftime('%Y%m%d-%H%M%S')}.txt"
        
        with open(error_path, "w", encoding="utf-8") as f:
            f.write(error_info)
        
        logging.error(error_info)
        logging.info(f"Error details have been saved to: {error_path}")
        logging.info("Please check the error log for more information.")
        
        return 1

if __name__ == "__main__":
    sys.exit(main())