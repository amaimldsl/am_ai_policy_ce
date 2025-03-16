#!/usr/bin/env python3
"""
Helper script to run individual tasks in the workflow.
This can be useful when a specific task fails and you want to retry just that task.
"""

import os
import sys
import logging
import argparse
from pathlib import Path
import yaml
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"task_helper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def find_config_directory():
    """Find the config directory from various possible locations"""
    config_dir_candidates = [
        Path(__file__).resolve().parent / "config",
        Path(__file__).resolve().parent.parent / "config",
        Path.cwd() / "config",
        Path.cwd() / "src" / "pcec" / "config"
    ]
    
    for candidate in config_dir_candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate
    
    # If not found, use the script directory
    config_dir = Path(__file__).resolve().parent / "config"
    config_dir.mkdir(exist_ok=True)
    return config_dir

def find_output_directory():
    """Find or create the output directory"""
    output_dir_candidates = [
        Path(__file__).resolve().parent / "output",
        Path(__file__).resolve().parent.parent / "output",
        Path.cwd() / "output",
        Path.cwd() / "src" / "pcec" / "output"
    ]
    
    for candidate in output_dir_candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate
    
    # If not found, create in the script directory
    output_dir = Path(__file__).resolve().parent / "output"
    output_dir.mkdir(exist_ok=True)
    return output_dir

def load_config(filename):
    """Load configuration from YAML file"""
    config_dir = find_config_directory()
    config_path = config_dir / filename
    
    if not config_path.exists():
        logger.error(f"Configuration file {filename} not found in {config_dir}")
        return None
    
    try:
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        logger.error(f"Error loading configuration from {filename}: {str(e)}")
        return None

def run_extract_conditions():
    """Run the extract conditions task"""
    logger.info("Running extract conditions task")
    
    # Call the parse_conditions.py script
    try:
        import parse_conditions
        parse_conditions.main()
        logger.info("Successfully ran extract conditions task")
        return True
    except ImportError:
        logger.error("Could not import parse_conditions module. Please make sure it exists.")
        return False
    except Exception as e:
        logger.error(f"Error running extract conditions task: {str(e)}")
        return False

def run_identify_risks():
    """Run the identify risks task"""
    logger.info("Running identify risks task")
    
    # Check if extract_conditions_task_output.md exists
    output_dir = find_output_directory()
    conditions_file = output_dir / "extract_conditions_task_output.md"
    
    if not conditions_file.exists():
        logger.error(f"Conditions file {conditions_file} not found. Please run extract conditions task first.")
        return False
    
    # Generate a risk assessment using the conditions
    try:
        risks_file = output_dir / "identify_risks_task_output.md"
        
        # Get the conditions content
        with open(conditions_file, 'r') as f:
            conditions_content = f.read()
        
        # Simple risk assessment
        with open(risks_file, 'w') as f:
            f.write("# Risk Assessment Results\n\n")
            
            # Extract conditions and generate risks
            condition_sections = conditions_content.split("###")[1:]  # Skip the header
            for i, section in enumerate(condition_sections, 1):
                lines = section.strip().split("\n")
                condition_id = lines[0].strip()
                description = ""
                reference = ""
                
                for line in lines:
                    if line.startswith("**Description:**"):
                        description = line.replace("**Description:**", "").strip()
                    elif line.startswith("**Reference:**"):
                        reference = line.replace("**Reference:**", "").strip()
                
                if description:
                    f.write(f"## R-{i}: C-{i}\n")
                    f.write(f"**Description**: Risk of non-compliance with {condition_id}: {description}\n")
                    f.write("**Likelihood**: Medium\n")
                    f.write("**Impact**: Medium\n")
                    f.write(f"**Source**: {reference}\n\n")
        
        logger.info(f"Successfully generated risk assessment to {risks_file}")
        return True
        
    except Exception as e:
        logger.error(f"Error running identify risks task: {str(e)}")
        return False

def run_design_controls():
    """Run the design controls task"""
    logger.info("Running design controls task")
    
    # Check if identify_risks_task_output.md exists
    output_dir = find_output_directory()
    risks_file = output_dir / "identify_risks_task_output.md"
    
    if not risks_file.exists():
        logger.error(f"Risks file {risks_file} not found. Please run identify risks task first.")
        return False
    
    # Generate a control framework using the risks
    try:
        controls_file = output_dir / "design_controls_task_output.md"
        
        # Get the risks content
        with open(risks_file, 'r') as f:
            risks_content = f.read()
        
        # Simple control design
        with open(controls_file, 'w') as f:
            f.write("# Control Framework\n\n")
            
            # Extract risks and design controls
            risk_sections = risks_content.split("##")[1:]  # Skip the header
            for section in risk_sections:
                lines = section.strip().split("\n")
                if not lines:
                    continue
                    
                risk_info = lines[0].strip()
                parts = risk_info.split(":")
                if len(parts) < 2:
                    continue
                    
                risk_id = parts[0].strip()
                condition_id = parts[1].strip() if len(parts) > 1 else ""
                
                description = ""
                source = ""
                
                for line in lines:
                    if line.startswith("**Description**:"):
                        description = line.replace("**Description**:", "").strip()
                    elif line.startswith("**Source**:"):
                        source = line.replace("**Source**:", "").strip()
                
                if description:
                    control_id = f"C-{risk_id.replace('R-', '')}"
                    control_type = "Preventive"
                    if "detect" in description.lower():
                        control_type = "Detective"
                    elif "correct" in description.lower():
                        control_type = "Corrective"
                    
                    f.write(f"## {control_id}: {risk_id}\n")
                    f.write(f"**Description**: Control to mitigate {description}\n")
                    f.write(f"**Type**: {control_type}\n")
                    f.write(f"**Source**: {source}\n")
                    f.write("**Implementation Considerations**: Regular monitoring and verification required.\n\n")
        
        logger.info(f"Successfully generated control framework to {controls_file}")
        return True
        
    except Exception as e:
        logger.error(f"Error running design controls task: {str(e)}")
        return False

def run_develop_tests():
    """Run the develop tests task"""
    logger.info("Running develop tests task")
    
    # Check if design_controls_task_output.md exists
    output_dir = find_output_directory()
    controls_file = output_dir / "design_controls_task_output.md"
    
    if not controls_file.exists():
        logger.error(f"Controls file {controls_file} not found. Please run design controls task first.")
        return False
    
    # Generate an audit program using the controls
    try:
        tests_file = output_dir / "develop_tests_task_output.md"
        
        # Get the controls content
        with open(controls_file, 'r') as f:
            controls_content = f.read()
        
        # Simple test procedure design
        with open(tests_file, 'w') as f:
            f.write("# Audit Test Procedures\n\n")
            
            # Extract controls and design test procedures
            control_sections = controls_content.split("##")[1:]  # Skip the header
            for section in control_sections:
                lines = section.strip().split("\n")
                if not lines:
                    continue
                    
                control_info = lines[0].strip()
                parts = control_info.split(":")
                if len(parts) < 2:
                    continue
                    
                control_id = parts[0].strip()
                risk_id = parts[1].strip() if len(parts) > 1 else ""
                
                description = ""
                control_type = ""
                source = ""
                
                for line in lines:
                    if line.startswith("**Description**:"):
                        description = line.replace("**Description**:", "").strip()
                    elif line.startswith("**Type**:"):
                        control_type = line.replace("**Type**:", "").strip()
                    elif line.startswith("**Source**:"):
                        source = line.replace("**Source**:", "").strip()
                
                if description:
                    test_id = f"T-{control_id.replace('C-', '')}"
                    
                    f.write(f"## {test_id}: {control_id}\n")
                    f.write(f"**Objective**: Verify implementation and effectiveness of {control_id}\n")
                    f.write("**Test Steps**:\n")
                    
                    # Generate steps based on control type
                    if control_type.lower() == "detective":
                        f.write("- 1. Review detection mechanism documentation\n")
                        f.write("- 2. Test detection capabilities with sample scenarios\n")
                        f.write("- 3. Verify alert/notification process\n")
                        f.write("- 4. Validate response procedures\n")
                    elif control_type.lower() == "preventive":
                        f.write("- 1. Review control implementation documentation\n")
                        f.write("- 2. Test preventive measure with sample data\n")
                        f.write("- 3. Attempt to bypass control (negative testing)\n")
                        f.write("- 4. Verify logging of attempted violations\n")
                    else:
                        f.write("- 1. Review control documentation\n")
                        f.write("- 2. Interview responsible personnel\n")
                        f.write("- 3. Test control using sample data\n")
                        f.write("- 4. Verify effectiveness against requirements\n")
                    
                    f.write(f"**Required Evidence**: Documentation, system logs, and interview notes\n")
                    f.write(f"**Source**: {source}\n\n")
        
        logger.info(f"Successfully generated audit program to {tests_file}")
        return True
        
    except Exception as e:
        logger.error(f"Error running develop tests task: {str(e)}")
        return False

def run_generate_report():
    """Run the generate report task"""
    logger.info("Running generate report task")
    
    # Check if all prerequisite files exist
    output_dir = find_output_directory()
    files_to_check = [
        "extract_conditions_task_output.md",
        "identify_risks_task_output.md",
        "design_controls_task_output.md",
        "develop_tests_task_output.md"
    ]
    
    missing_files = []
    for file in files_to_check:
        if not (output_dir / file).exists():
            missing_files.append(file)
    
    if missing_files:
        logger.error(f"The following files are missing: {', '.join(missing_files)}")
        logger.error("Please run the prerequisite tasks first.")
        return False
    
    # Generate the final report
    try:
        report_file = output_dir / "6_final_compliance_report.md"
        
        with open(report_file, 'w') as f:
            f.write("# Comprehensive Compliance Analysis Report\n\n")
            
            # 1. Executive Summary
            f.write("## 1. Executive Summary\n\n")
            f.write("This report provides a comprehensive analysis of compliance conditions identified from policy documents, ")
            f.write("the associated risks of non-compliance, controls designed to mitigate these risks, and test procedures ")
            f.write("to verify control effectiveness. The analysis ensures full traceability from compliance conditions to ")
            f.write("risks, controls, and audit procedures.\n\n")
            
            # 2. Load the content from previous task outputs
            try:
                with open(output_dir / "extract_conditions_task_output.md", 'r') as cf:
                    conditions_content = cf.read()
                    
                with open(output_dir / "identify_risks_task_output.md", 'r') as rf:
                    risks_content = rf.read()
                    
                with open(output_dir / "design_controls_task_output.md", 'r') as df:
                    controls_content = df.read()
                    
                with open(output_dir / "develop_tests_task_output.md", 'r') as tf:
                    tests_content = tf.read()
            except Exception as e:
                logger.error(f"Error reading task outputs: {str(e)}")
                return False
            
            # 3. Add sections
            f.write("## 2. Compliance Conditions\n\n")
            f.write(conditions_content.split("# Policy Compliance Conditions")[1] if "# Policy Compliance Conditions" in conditions_content else conditions_content)
            f.write("\n\n")
            
            f.write("## 3. Risk Assessment\n\n")
            f.write(risks_content.split("# Risk Assessment Results")[1] if "# Risk Assessment Results" in risks_content else risks_content)
            f.write("\n\n")
            
            f.write("## 4. Control Framework\n\n")
            f.write(controls_content.split("# Control Framework")[1] if "# Control Framework" in controls_content else controls_content)
            f.write("\n\n")
            
            f.write("## 5. Audit Test Procedures\n\n")
            f.write(tests_content.split("# Audit Test Procedures")[1] if "# Audit Test Procedures" in tests_content else tests_content)
            f.write("\n\n")
            
            # 6. Traceability Matrix
            f.write("## 6. Traceability Matrix\n\n")
            f.write("| Condition ID | Risk ID | Control ID | Test ID | Document Source |\n")
            f.write("|-------------|---------|------------|---------|----------------|\n")
            
            # Extract condition IDs from conditions content
            condition_ids = re.findall(r'### (C-\d+)', conditions_content)
            
            # Generate traceability rows
            for condition_id in condition_ids:
                # Extract the numeric part
                num = condition_id.replace("C-", "")
                risk_id = f"R-{num}"
                control_id = f"C-{num}"
                test_id = f"T-{num}"
                
                # Find the reference
                reference_match = re.search(f'{condition_id}.*?\n\*\*Reference:\*\* (.*?)(?:\n|$)', conditions_content)
                reference = reference_match.group(1) if reference_match else "Unknown"
                
                f.write(f"| {condition_id} | {risk_id} | {control_id} | {test_id} | {reference} |\n")
        
        logger.info(f"Successfully generated final report to {report_file}")
        return True
        
    except Exception as e:
        logger.error(f"Error running generate report task: {str(e)}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Run individual tasks in the workflow')
    parser.add_argument('task', type=str, choices=['extract', 'risks', 'controls', 'tests', 'report', 'all'],
                        help='The task to run')
    
    args = parser.parse_args()
    
    if args.task == 'extract' or args.task == 'all':
        if not run_extract_conditions():
            logger.error("Failed to run extract conditions task")
            if args.task != 'all':
                return 1
    
    if args.task == 'risks' or args.task == 'all':
        if not run_identify_risks():
            logger.error("Failed to run identify risks task")
            if args.task != 'all':
                return 1
    
    if args.task == 'controls' or args.task == 'all':
        if not run_design_controls():
            logger.error("Failed to run design controls task")
            if args.task != 'all':
                return 1
    
    if args.task == 'tests' or args.task == 'all':
        if not run_develop_tests():
            logger.error("Failed to run develop tests task")
            if args.task != 'all':
                return 1
    
    if args.task == 'report' or args.task == 'all':
        if not run_generate_report():
            logger.error("Failed to run generate report task")
            if args.task != 'all':
                return 1
    
    logger.info("All requested tasks completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())
