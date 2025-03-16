import sys
import time
import traceback
from pathlib import Path

from crew import pcec
from pdftest import test_pdf_extraction
import document_processor

def main():
    """Main function to run the policy compliance analysis."""
    try:
        print("Testing PDF tool...")
        
        test_pdf_extraction()
        
        print("Preprocessing documents...")
        document_processor.preprocess_documents()
        
        # Check if tools are available
        print("Checking available tools...")
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
                print(f"✓ {tool} is available")
            except ImportError:
                print(f"✗ {tool} is NOT available")
        
        print("Starting Policy Compliance Analysis...")
        start_time = time.time()
        
        # Run the crew
        result = pcec.kickoff()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"✅ Analysis completed successfully in {execution_time:.2f} seconds!")
        print(f"Task outputs have been saved to the output directory.")
        
        # You can still access the final result if needed
        print(f"Final crew output length: {len(str(result))} characters")
        
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
        
        print(error_info)
        print(f"Error details have been saved to: {error_path}")
        print("Please check the error log for more information.")
        
        return 1

if __name__ == "__main__":
    sys.exit(main())