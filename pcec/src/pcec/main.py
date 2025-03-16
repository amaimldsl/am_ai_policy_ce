# Enhanced main.py
import sys
import time
import traceback
import logging
from pathlib import Path
import os
from crew import pcec

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("compliance_analysis.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def check_prerequisites():
    """Check if all necessary files and directories exist"""
    try:
        # Check for policy directory
        policy_dir = Path("policy")
        if not policy_dir.exists() or not policy_dir.is_dir():
            # Try alternate locations
            alt_policy_dirs = [
                Path(__file__).resolve().parent / "policy",
                Path(__file__).resolve().parent.parent / "policy",
                Path.cwd() / "src" / "pcec" / "policy"
            ]
            
            policy_dir = next((d for d in alt_policy_dirs if d.exists() and d.is_dir()), None)
            
            if not policy_dir:
                logger.warning("Policy directory not found. Will create one.")
                policy_dir = Path(__file__).resolve().parent / "policy"
                policy_dir.mkdir(exist_ok=True)
        
        # Check for PDF files in policy directory
        pdf_files = list(policy_dir.glob("*.pdf"))
        if not pdf_files:
            logger.warning("No PDF files found in policy directory. Please add PDF files before processing.")
            example_file = policy_dir / "example_policy.txt"
            if not example_file.exists():
                with open(example_file, "w") as f:
                    f.write("This is an example policy file. Replace with actual PDF policy documents.")
                logger.info(f"Created example file at {example_file}")
        
        # Check for required tool directories
        tools_dir = Path(__file__).resolve().parent / "tools"
        if not tools_dir.exists():
            tools_dir.mkdir(exist_ok=True)
            logger.info(f"Created tools directory at {tools_dir}")
        
        # Check for config directory or create it
        config_dir = Path(__file__).resolve().parent / "config"
        if not config_dir.exists():
            config_dir.mkdir(exist_ok=True)
            logger.info(f"Created config directory at {config_dir}")
            
            # Create default configuration files
            create_default_config_files(config_dir)
        
        # Check output directory or create it
        output_dir = Path(__file__).resolve().parent / "output"
        output_dir.mkdir(exist_ok=True)
        
        # Check preprocessed directory or create it
        preprocessed_dir = Path(__file__).resolve().parent / "preprocessed"
        preprocessed_dir.mkdir(exist_ok=True)
        
        return True
    except Exception as e:
        logger.error(f"Error checking prerequisites: {str(e)}")
        return False

def create_default_config_files(config_dir):
    """Create default configuration files in the config directory"""
    try:
        # Create default agents.yaml
        agents_yaml = config_dir / "agents.yaml"
        if not agents_yaml.exists():
            agents_config = """policy_analyzer:
  role: Policy Analyzer
  goal: Extract all policy compliance conditions, requirements, and obligations from the PDF
  backstory: You are an expert in policy analysis with experience in regulatory frameworks and compliance requirements extraction.
  tools:
    - PDFTool
    - FileIOTool
  verbose: true

risk_assessor:
  role: Risk Assessor
  goal: Identify and categorize all potential risks associated with each compliance condition
  backstory: You are a risk management professional who specializes in identifying compliance-related risks and their potential impacts.
  tools:
    - FileIOTool
    - RiskAnalysisTool
  verbose: true

control_designer:
  role: Control Designer
  goal: Design appropriate controls for mitigating each identified risk
  backstory: You are a control framework specialist who develops robust control mechanisms to ensure policy compliance.
  tools:
    - FileIOTool
    - ControlDesignTool
  verbose: true

audit_planner:
  role: Audit Planner
  goal: Create comprehensive test procedures to verify compliance with all conditions
  backstory: You are an experienced compliance auditor who develops thorough audit plans with specific test procedures.
  tools:
    - FileIOTool
    - AuditPlanningTool
  verbose: true"""

            with open(agents_yaml, "w") as f:
                f.write(agents_config)
            logger.info(f"Created default agents.yaml configuration at {agents_yaml}")
        
        # Create default tasks.yaml
        tasks_yaml = config_dir / "tasks.yaml"
        if not tasks_yaml.exists():
            tasks_config = """extract_conditions_task:
  description: |
    Thoroughly analyze ALL PDF documents in the policy folder and extract ALL policy requirements.
    Use the PDFTool with process_all=True to examine all PDF files.
    Use keywords like 'shall', 'should', 'must', 'required', 'obligated' and other modal verbs to extract ALL requirements.
    Ensure COMPLETE coverage by reviewing EVERY section and EVERY page of EVERY document.
    Format the output as a structured list with condition ID, description, and reference (document name, page/section).
    Include the source document name in each reference.
  expected_output: A comprehensive, structured list of all policy compliance conditions with unique IDs, descriptions, and source references including document names.
  agent: policy_analyzer

identify_risks_task:
  description: |
    For each extracted compliance condition, identify and analyze potential risks of non-compliance.
    Assess the likelihood and potential impact of each risk.
    Format the output as a structured list with risk ID, related condition ID, risk description, likelihood, and impact.
    Include references to the source document and page for each risk.
  expected_output: A detailed risk register mapping risks to compliance conditions with assessment of likelihood and impact and source references.
  agent: risk_assessor
  context:
    - extract_conditions_task

design_controls_task:
  description: |
    For each identified risk, design appropriate controls to mitigate the risk and ensure compliance.
    Specify whether each control is preventive, detective, or corrective.
    Format the output as a structured list with control ID, related risk ID, control description, control type, and implementation considerations.
    Include references to the original policy condition's document source and page.
  expected_output: A comprehensive control framework with specific controls mapped to each identified risk and traceability to source documents.
  agent: control_designer
  context:
    - identify_risks_task

develop_tests_task:
  description: |
    For each control, develop detailed test procedures to verify implementation and effectiveness.
    Include specific steps, expected results, and evidence requirements for each test.
    Format the output as a structured audit program with test ID, related control ID, test objective, detailed test steps, and evidence requirements.
    Maintain traceability to the original source documents by including references to document names and page numbers.
  expected_output: A detailed audit program with specific test procedures for each control to verify compliance with policy requirements with source traceability.
  agent: audit_planner
  context:
    - design_controls_task

generate_report_task:
  description: |
    Compile all findings into a comprehensive report that includes:
    1. Executive summary of the policy analysis
    2. Complete listing of all compliance conditions with document sources
    3. Risk assessment results
    4. Control framework
    5. Audit test procedures
    6. Traceability matrix showing relationships between conditions, risks, controls, and tests, including document sources
    Format the report in a professional, well-structured manner suitable for executive review.
    Ensure full traceability to source documents by including document names and page numbers in all references.
  expected_output: A comprehensive compliance analysis report with all components and a traceability matrix that includes source document references.
  agent: policy_analyzer
  context:
    - extract_conditions_task
    - identify_risks_task
    - design_controls_task
    - develop_tests_task"""

            with open(tasks_yaml, "w") as f:
                f.write(tasks_config)
            logger.info(f"Created default tasks.yaml configuration at {tasks_yaml}")
            
    except Exception as e:
        logger.error(f"Error creating default configuration files: {str(e)}")

def preprocess_documents():
    """Preprocess documents and return True if successful"""
    try:
        from document_processor import preprocess_documents
        
        logger.info("Starting document preprocessing...")
        chunks = preprocess_documents()
        
        if not chunks:
            logger.error("Document preprocessing failed to produce any chunks")
            return False
            
        logger.info(f"Document preprocessing completed successfully with {len(chunks)} chunks")
        return True
    except Exception as e:
        logger.error(f"Error during document preprocessing: {str(e)}")
        return False

def test_tools():
    """Test PDF extraction and other tools"""
    try:
        from pdftest import test_pdf_extraction
        
        logger.info("Testing PDF extraction tool...")
        result = test_pdf_extraction()
        
        if result and "error" in result:
            logger.error(f"PDF extraction test failed: {result['error']}")
            return False
            
        logger.info("PDF extraction test completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error testing PDF extraction: {str(e)}")
        return False

def main():
    """Main function to run the policy compliance analysis."""
    try:
        logger.info("Starting Policy Compliance Analysis Framework")
        
        # Check prerequisites
        logger.info("Checking prerequisites...")
        if not check_prerequisites():
            logger.error("Prerequisites check failed. Exiting.")
            return 1
            
        # Test tools
        logger.info("Testing tools...")
        if not test_tools():
            logger.warning("Tool testing encountered issues. Proceeding with caution.")
            
        # Preprocess documents
        logger.info("Preprocessing documents...")
        if not preprocess_documents():
            logger.error("Document preprocessing failed. Exiting.")
            return 1
        
        # Import crew after preprocessing to ensure it has access to chunks
        logger.info("Importing CrewAI framework...")
        
        
        # Start the analysis
        logger.info("Starting comprehensive compliance analysis...")
        start_time = time.time()
        
        # Run the crew with error handling
        try:
            result = pcec.kickoff()
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            logger.info(f"✅ Analysis completed successfully in {execution_time:.2f} seconds!")
            logger.info(f"Task outputs have been saved to the output directory.")
            
            # Verify outputs
            output_dir = Path("output")
            output_files = list(output_dir.glob("*.md"))
            logger.info(f"Generated {len(output_files)} output files")
            
            # Log final report location
            final_report = output_dir / "6_final_compliance_report.md"
            if final_report.exists():
                logger.info(f"Final compliance report saved to: {final_report}")
                logger.info(f"Report size: {final_report.stat().st_size / 1024:.1f} KB")
            else:
                logger.warning("Final compliance report not found")
            
            return 0
        except Exception as crew_error:
            logger.error(f"Crew execution failed: {str(crew_error)}")
            logger.error("Attempting to save partial results...")
            
            # Try to save whatever was completed
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            
            error_report = output_dir / "error_report.md"
            with open(error_report, "w") as f:
                f.write(f"# Compliance Analysis Error Report\n\n")
                f.write(f"The analysis encountered an error: {str(crew_error)}\n\n")
                f.write("## Available Partial Results\n\n")
                
                # List any output files that were created
                output_files = list(output_dir.glob("*.md"))
                if output_files:
                    f.write("The following partial results are available:\n\n")
                    for file in output_files:
                        if file.name != "error_report.md":
                            f.write(f"- [{file.name}]({file.name})\n")
                else:
                    f.write("No partial results were generated before the error occurred.\n")
            
            logger.info(f"Error report saved to: {error_report}")
            return 1
    
    except Exception as e:
        error_info = f"❌ CRITICAL ERROR: Analysis failed with exception: {str(e)}\n"
        error_info += "Detailed error information:\n"
        error_info += traceback.format_exc()
        
        # Save error information
        timestamp = time.strftime('%Y%m%d-%H%M%S')
        error_path = Path(f"error_log_{timestamp}.txt")
        
        with open(error_path, "w", encoding="utf-8") as f:
            f.write(error_info)
        
        logger.error(error_info)
        logger.info(f"Error details have been saved to: {error_path}")
        
        return 1

if __name__ == "__main__":
    sys.exit(main())