import sys
import time
import traceback
from pathlib import Path
import os

from crew import pcec

def main():
    """Main function to run the policy compliance analysis."""
    try:
        print("Starting Policy Compliance Analysis...")
        
        # Check if policy directory exists and has PDF files
        base_dir = Path(__file__).parent
        policy_dir = base_dir / "policy"
        policy_dir.mkdir(exist_ok=True)
        
        pdf_files = list(policy_dir.glob("*.pdf"))
        if not pdf_files:
            print("⚠️ No PDF files found in the policy directory!")
            print(f"Please place PDF files in: {policy_dir}")
            return 1
        
        print(f"Found {len(pdf_files)} PDF files in policy directory:")
        for pdf in pdf_files:
            print(f"  - {pdf.name}")
        
        print(f"Using {pdf_files[0].name} for analysis...")
        
        # Create output directory if it doesn't exist
        output_dir = base_dir / "output"
        output_dir.mkdir(exist_ok=True)
        
        start_time = time.time()
        
        # Run the crew - outputs will be automatically saved to the specified files
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