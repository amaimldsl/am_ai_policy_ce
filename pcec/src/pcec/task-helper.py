#!/usr/bin/env python3
"""
Helper script to run individual tasks in the workflow.
This can be useful when a specific task fails and you want to retry just that task.
"""

import os
import sys
import logging
import argparse
import re
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

def determine_likelihood_impact(description):
    """Determine likelihood and impact based on description content"""
    description_lower = description.lower()
    
    # Default values
    likelihood = "Medium"
    impact = "Medium"
    
    # Check for high impact keywords
    high_impact_keywords = ["critical", "severe", "significant", "major", "catastrophic", "safety", "security"]
    if any(keyword in description_lower for keyword in high_impact_keywords):
        impact = "High"
    
    # Check for high likelihood keywords
    high_likelihood_keywords = ["always", "frequent", "common", "certain", "regular", "often"]
    if any(keyword in description_lower for keyword in high_likelihood_keywords):
        likelihood = "High"
    
    # Check for low impact keywords
    low_impact_keywords = ["minor", "minimal", "trivial", "small", "limited"]
    if any(keyword in description_lower for keyword in low_impact_keywords) and impact != "High":
        impact = "Low"
    
    # Check for low likelihood keywords
    low_likelihood_keywords = ["rare", "unlikely", "seldom", "infrequent", "occasional"]
    if any(keyword in description_lower for keyword in low_likelihood_keywords) and likelihood != "High":
        likelihood = "Low"
    
    return likelihood, impact

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
        
        # Parse the conditions
        conditions = parse_conditions_file(conditions_file)
        
        # Create risk assessment with better formatting and more comprehensive coverage
        with open(risks_file, 'w') as f:
            f.write("# Risk Assessment Results\n\n")
            
            # Group risks by priority (High, Medium, Low)
            for priority, likelihood_impact in [
                ("High", [("High", "High"), ("High", "Medium"), ("Medium", "High")]),
                ("Medium", [("Medium", "Medium"), ("High", "Low"), ("Low", "High")]),
                ("Low", [("Medium", "Low"), ("Low", "Medium"), ("Low", "Low")])
            ]:
                f.write(f"## {priority} Priority Risks\n\n")
                
                risk_count = 0
                for i, condition in enumerate(conditions, 1):
                    condition_id = condition.get('id', f'C-{i}')
                    description = condition.get('description', '')
                    reference = condition.get('reference', '')
                    
                    # For high priority conditions, create more detailed risks
                    if priority == "High":
                        # Determine likelihood and impact based on keywords
                        likelihood, impact = determine_likelihood_impact(description)
                        
                        # Only include if matches our desired priority level
                        if (likelihood, impact) not in likelihood_impact:
                            continue
                        
                        # Create risk entry
                        risk_id = f"R-{condition_id.replace('C-', '')}"
                        f.write(f"### {risk_id}\n")
                        f.write(f"**Description**: Risk of non-compliance with {condition_id}: {description}\n")
                        f.write(f"**Likelihood**: {likelihood}\n")
                        f.write(f"**Impact**: {impact}\n")
                        f.write(f"**Source**: {reference}\n\n")
                        risk_count += 1
                    
                    # For medium priority, create risks based on pattern
                    elif priority == "Medium" and i % 3 == 0:  # Every 3rd condition
                        # Determine likelihood and impact based on keywords
                        likelihood, impact = determine_likelihood_impact(description)
                        
                        # Only include if matches our desired priority level
                        if (likelihood, impact) not in likelihood_impact:
                            continue
                        
                        # Create risk entry
                        risk_id = f"R-{condition_id.replace('C-', '')}"
                        f.write(f"### {risk_id}\n")
                        f.write(f"**Description**: Risk of non-compliance with {condition_id}: {description}\n")
                        f.write(f"**Likelihood**: {likelihood}\n")
                        f.write(f"**Impact**: {impact}\n")
                        f.write(f"**Source**: {reference}\n\n")
                        risk_count += 1
                    
                    # For low priority, create risks based on different pattern
                    elif priority == "Low" and i % 5 == 0:  # Every 5th condition
                        # Determine likelihood and impact based on keywords
                        likelihood, impact = determine_likelihood_impact(description)
                        
                        # Only include if matches our desired priority level
                        if (likelihood, impact) not in likelihood_impact:
                            continue
                        
                        # Create risk entry
                        risk_id = f"R-{condition_id.replace('C-', '')}"
                        f.write(f"### {risk_id}\n")
                        f.write(f"**Description**: Risk of non-compliance with {condition_id}: {description}\n")
                        f.write(f"**Likelihood**: {likelihood}\n")
                        f.write(f"**Impact**: {impact}\n")
                        f.write(f"**Source**: {reference}\n\n")
                        risk_count += 1
                
                # If no risks in this priority level, add a placeholder
                if risk_count == 0:
                    f.write("No risks identified in this priority level.\n\n")
        
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
        
        # Parse the risks
        risks = parse_risks_file(risks_file)
        
        # Create more comprehensive control framework
        with open(controls_file, 'w') as f:
            f.write("# Control Framework\n\n")
            
            # Group controls by type
            control_types = ["Preventive", "Detective", "Corrective"]
            
            for control_type in control_types:
                f.write(f"## {control_type} Controls\n\n")
                
                for risk in risks:
                    risk_id = risk.get('id', '')
                    description = risk.get('description', '')
                    source = risk.get('reference', '')
                    priority = risk.get('priority', 'Medium')
                    
                    # Skip if no risk ID
                    if not risk_id:
                        continue
                    
                    # Create primary control ID
                    if risk_id.startswith('R-'):
                        control_id = f"C-{risk_id.replace('R-', '')}"
                    else:
                        # If ID doesn't start with R-, create a fallback ID
                        control_id = f"C-{len(f.tell())}"
                    
                    # Generate control description based on risk and control type
                    if control_type == "Preventive":
                        control_desc = f"Implement preventive measures to ensure compliance with {description} through proactive verification, validation, and restriction mechanisms."
                        implementation = "Implementation includes input validation requirements, pre-approval workflows, system restrictions, automated verification, and regular training."
                    elif control_type == "Detective":
                        control_desc = f"Establish monitoring and detection systems to identify potential non-compliance with {description} through regular audits and exception reporting."
                        implementation = "Implementation includes compliance scanning, real-time alerts, regular audits, exception reporting, and monitoring tools."
                    elif control_type == "Corrective":
                        control_desc = f"Develop remediation procedures to address identified instances of non-compliance with {description} through structured response mechanisms."
                        implementation = "Implementation includes incident response procedures, remediation plans, root cause analysis, documentation of corrective actions, and verification procedures."
                    else:
                        control_desc = f"Implement controls to ensure compliance with {description}."
                        implementation = "Regular monitoring and verification required."
                    
                    # Create a secondary control ID for high and medium priority risks
                    if priority in ["High", "Medium"]:
                        # Primary control
                        f.write(f"### {control_id}: {risk_id}\n")
                        f.write(f"**Description**: {control_desc}\n")
                        f.write(f"**Type**: {control_type}\n")
                        f.write(f"**Source**: {source}\n")
                        f.write(f"**Implementation Considerations**: {implementation}\n\n")
                        
                        # Secondary control with different focus
                        secondary_control_id = f"{control_id}-2"
                        if control_type == "Preventive":
                            secondary_type = "Detective"
                            secondary_desc = f"Establish monitoring system to detect non-compliance with {description} during operation."
                            secondary_impl = "Implementation includes logging mechanisms, periodic reviews, automated alerts, and compliance verification procedures."
                        else:
                            secondary_type = "Preventive"
                            secondary_desc = f"Implement preventive measures to ensure compliance with {description} prior to processing or execution."
                            secondary_impl = "Implementation includes system validations, input controls, restrictions, and preventive configurations."
                        
                        f.write(f"### {secondary_control_id}: {risk_id}\n")
                        f.write(f"**Description**: {secondary_desc}\n")
                        f.write(f"**Type**: {secondary_type}\n")
                        f.write(f"**Source**: {source}\n")
                        f.write(f"**Implementation Considerations**: {secondary_impl}\n\n")
                    else:
                        # Just primary control for low priority risks
                        f.write(f"### {control_id}: {risk_id}\n")
                        f.write(f"**Description**: {control_desc}\n")
                        f.write(f"**Type**: {control_type}\n")
                        f.write(f"**Source**: {source}\n")
                        f.write(f"**Implementation Considerations**: {implementation}\n\n")
        
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
        
        # Parse the controls
        controls = parse_controls_file(controls_file)
        
        # Create more comprehensive test procedures
        with open(tests_file, 'w') as f:
            f.write("# Audit Test Procedures\n\n")
            
            for control in controls:
                control_id = control.get('id', '')
                description = control.get('description', '')
                control_type = control.get('type', 'Preventive')
                reference = control.get('reference', '')
                
                # Skip if no control ID
                if not control_id:
                    continue
                
                # Create test ID based on control ID
                if control_id.startswith('C-'):
                    test_id = f"T-{control_id.replace('C-', '')}"
                else:
                    # If ID doesn't start with C-, create a fallback ID
                    test_id = f"T-{len(f.tell())}"
                
                # Generate test objective
                objective = f"Verify implementation and effectiveness of control {control_id}"
                
                # Generate test steps based on control type
                if control_type == "Preventive":
                    steps = [
                        "1. Review control implementation documentation",
                        "2. Test preventive measure with sample data",
                        "3. Attempt to bypass control (negative testing)",
                        "4. Verify logging of attempted violations",
                        "5. Confirm the control consistently prevents non-compliant actions"
                    ]
                elif control_type == "Detective":
                    steps = [
                        "1. Review detection mechanism documentation",
                        "2. Test detection capabilities with sample scenarios",
                        "3. Verify alert/notification process",
                        "4. Validate response procedures",
                        "5. Confirm detection effectiveness through simulated violations"
                    ]
                elif control_type == "Corrective":
                    steps = [
                        "1. Review correction procedures documentation",
                        "2. Validate correction workflow with sample scenarios",
                        "3. Verify timeliness of corrective actions",
                        "4. Confirm documentation of corrections",
                        "5. Test correction effectiveness through follow-up verification"
                    ]
                else:
                    steps = [
                        "1. Review control documentation",
                        "2. Interview responsible personnel",
                        "3. Test control using sample data",
                        "4. Verify effectiveness against requirements",
                        "5. Validate ongoing monitoring and maintenance processes"
                    ]
                
                # Add control-specific test steps
                if "train" in description.lower():
                    steps.append("6. Verify training materials are comprehensive and up-to-date")
                    steps.append("7. Confirm training completion records are maintained")
                
                if "report" in description.lower():
                    steps.append("6. Verify reports contain all required elements")
                    steps.append("7. Test report generation process for accuracy")
                
                if "review" in description.lower():
                    steps.append("6. Verify evidence of reviews is documented")
                    steps.append("7. Test that review findings are acted upon")
                
                # Determine appropriate evidence requirements
                evidence_items = ["Documentation"]
                
                # Add evidence types based on control type
                if control_type == "Technical" or "system" in description.lower():
                    evidence_items.extend(["System logs", "Configuration screenshots", "Access records"])
                
                if control_type == "Detective" or "monitor" in description.lower():
                    evidence_items.extend(["Alert records", "Monitoring reports", "Exception logs"])
                
                if control_type == "Administrative" or "policy" in description.lower():
                    evidence_items.extend(["Policy documents", "Training records", "Signed acknowledgements"])
                
                # Add general evidence types
                evidence_items.append("Interview notes")
                
                evidence = ", ".join(evidence_items)
                
                # Write the test procedure
                f.write(f"## {test_id}: {control_id}\n")
                f.write(f"**Objective**: {objective}\n")
                f.write("**Test Steps**:\n")
                for step in steps:
                    f.write(f"- {step}\n")
                f.write(f"**Required Evidence**: {evidence}\n")
                f.write(f"**Source**: {reference}\n\n")
                
                # For controls with secondary aspects, create an additional test
                if "-" in control_id or len(description) > 100:
                    # Create secondary test ID
                    secondary_test_id = f"{test_id}-B"
                    
                    # Generate a more specific objective for the secondary test
                    if "monitor" in description.lower():
                        secondary_aspect = "monitoring capabilities"
                        secondary_steps = [
                            "1. Review monitoring procedures and frequency",
                            "2. Verify that monitoring covers all required elements",
                            "3. Test alert mechanisms for proper functioning",
                            "4. Confirm that monitoring results are properly reviewed",
                            "5. Verify that issues identified through monitoring are addressed"
                        ]
                    elif "report" in description.lower():
                        secondary_aspect = "reporting functions"
                        secondary_steps = [
                            "1. Identify all reporting requirements specified in the control",
                            "2. Sample recent reports to verify completeness and accuracy",
                            "3. Verify timely distribution to appropriate stakeholders",
                            "4. Confirm that report content meets regulatory requirements",
                            "5. Test the reporting mechanism for reliability and consistency"
                        ]
                    elif "document" in description.lower():
                        secondary_aspect = "documentation requirements"
                        secondary_steps = [
                            "1. Identify all documentation requirements in the control",
                            "2. Verify that documentation templates are properly defined",
                            "3. Sample documentation to verify completeness and accuracy",
                            "4. Confirm retention periods are defined and followed",
                            "5. Verify accessibility of documentation when needed"
                        ]
                    else:
                        secondary_aspect = "specific control components"
                        secondary_steps = [
                            "1. Identify specific components of the control requiring detailed testing",
                            "2. Develop targeted test cases for these components",
                            "3. Execute test cases and document results",
                            "4. Verify component implementation matches design",
                            "5. Confirm effective integration with other control elements"
                        ]
                    
                    secondary_objective = f"Verify specific aspect of {control_id}: {secondary_aspect}"
                    
                    # Write the secondary test procedure
                    f.write(f"## {secondary_test_id}: {control_id}\n")
                    f.write(f"**Objective**: {secondary_objective}\n")
                    f.write("**Test Steps**:\n")
                    for step in secondary_steps:
                        f.write(f"- {step}\n")
                    f.write(f"**Required Evidence**: {evidence}\n")
                    f.write(f"**Source**: {reference}\n\n")
        
        logger.info(f"Successfully generated audit program to {tests_file}")
        return True
        
    except Exception as e:
        logger.error(f"Error running develop tests task: {str(e)}")
        return False

def parse_conditions_file(file_path):
    """Parse conditions from the extract_conditions_task_output.md file"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        conditions = []
        
        # Extract condition sections
        condition_pattern = re.compile(r'###\s+(C-\d+)\s*\n\n\*\*Description:\*\*\s*(.*?)\n\n\*\*Reference:\*\*\s*(.*?)\n\n---', re.DOTALL)
        
        for match in condition_pattern.finditer(content):
            condition_id = match.group(1).strip()
            description = match.group(2).strip()
            reference = match.group(3).strip()
            
            conditions.append({
                'id': condition_id,
                'description': description,
                'reference': reference
            })
        
        return conditions
    except Exception as e:
        logger.error(f"Error parsing conditions file: {str(e)}")
        return []

def parse_risks_file(file_path):
    """Parse risks from the identify_risks_task_output.md file"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        risks = []
        
        # Extract risk sections
        risk_pattern = re.compile(r'###\s+(R-\d+)\s*\n\*\*Description\*\*:\s*(.*?)\n\*\*Likelihood\*\*:\s*(.*?)\n\*\*Impact\*\*:\s*(.*?)\n\*\*Source\*\*:\s*(.*?)(?:\n\n|\Z)', re.DOTALL)
        
        for match in risk_pattern.finditer(content):
            risk_id = match.group(1).strip()
            description = match.group(2).strip()
            likelihood = match.group(3).strip()
            impact = match.group(4).strip()
            reference = match.group(5).strip()
            
            # Determine priority based on likelihood and impact
            priority = "Medium"  # Default
            if likelihood == "High" and impact == "High":
                priority = "High"
            elif likelihood == "Low" and impact == "Low":
                priority = "Low"
            
            # Extract condition ID from risk ID if possible
            condition_id = f"C-{risk_id.replace('R-', '')}"
            
            risks.append({
                'id': risk_id,
                'condition_id': condition_id,
                'description': description,
                'likelihood': likelihood,
                'impact': impact,
                'priority': priority,
                'reference': reference
            })
        
        return risks
    except Exception as e:
        logger.error(f"Error parsing risks file: {str(e)}")
        return []

def parse_controls_file(file_path):
    """Parse controls from the design_controls_task_output.md file"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        controls = []
        
        # Extract control sections
        control_pattern = re.compile(r'###\s+(C-\d+(?:-\d+)?)\s*:\s*(R-\d+)\s*\n\*\*Description\*\*:\s*(.*?)\n\*\*Type\*\*:\s*(.*?)\n\*\*Source\*\*:\s*(.*?)\n\*\*Implementation Considerations\*\*:\s*(.*?)(?:\n\n|\Z)', re.DOTALL)
        
        for match in control_pattern.finditer(content):
            control_id = match.group(1).strip()
            risk_id = match.group(2).strip()
            description = match.group(3).strip()
            control_type = match.group(4).strip()
            reference = match.group(5).strip()
            implementation = match.group(6).strip()
            
            controls.append({
                'id': control_id,
                'risk_id': risk_id,
                'description': description,
                'type': control_type,
                'implementation': implementation,
                'reference': reference
            })
        
        return controls
    except Exception as e:
        logger.error(f"Error parsing controls file: {str(e)}")
        return []

def parse_tests_file(file_path):
    """Parse test procedures from the develop_tests_task_output.md file"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        tests = []
        
        # Extract test sections
        test_pattern = re.compile(r'##\s+(T-\d+(?:-[A-Z])?)\s*:\s*(C-\d+(?:-\d+)?)\s*\n\*\*Objective\*\*:\s*(.*?)\n\*\*Test Steps\*\*:\s*(.*?)\n\*\*Required Evidence\*\*:\s*(.*?)\n\*\*Source\*\*:\s*(.*?)(?:\n\n|\Z)', re.DOTALL)
        
        for match in test_pattern.finditer(content):
            test_id = match.group(1).strip()
            control_id = match.group(2).strip()
            objective = match.group(3).strip()
            steps_text = match.group(4).strip()
            evidence = match.group(5).strip()
            reference = match.group(6).strip()
            
            # Parse steps
            steps = []
            for line in steps_text.split("\n"):
                if line.strip().startswith("-"):
                    # Remove leading dash and whitespace
                    step = line.strip()[2:].strip()
                    steps.append(step)
            
            tests.append({
                'test_id': test_id,
                'control_id': control_id,
                'objective': objective,
                'steps': steps,
                'evidence': evidence,
                'reference': reference
            })
        
        return tests
    except Exception as e:
        logger.error(f"Error parsing tests file: {str(e)}")
        return []
    
def run_generate_report():
    """Run the generate report task - ENHANCED VERSION"""
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
    
    # Generate the final report with proper mappings and structure
    try:
        report_file = output_dir / "6_final_compliance_report.md"
        
        # Load all component data
        conditions_data = parse_conditions_file(output_dir / "extract_conditions_task_output.md")
        risks_data = parse_risks_file(output_dir / "identify_risks_task_output.md")
        controls_data = parse_controls_file(output_dir / "design_controls_task_output.md")
        tests_data = parse_tests_file(output_dir / "develop_tests_task_output.md")
        
        # Create traceability mapping
        traceability_map = create_traceability_mapping(conditions_data, risks_data, controls_data, tests_data)
        
        # Generate report with Executive Summary first
        with open(report_file, 'w') as f:
            f.write("# Comprehensive Compliance Analysis Report\n\n")
            
            # 1. Executive Summary
            f.write("## 1. Executive Summary\n\n")
            f.write("This report provides a comprehensive analysis of compliance conditions identified from policy documents, ")
            f.write("the associated risks of non-compliance, controls designed to mitigate these risks, and test procedures ")
            f.write("to verify control effectiveness. The analysis ensures full traceability from compliance conditions to ")
            f.write("risks, controls, and audit procedures.\n\n")
            
            # Add summary statistics
            f.write(f"**Summary Statistics**:\n")
            f.write(f"- **Compliance Conditions Identified**: {len(conditions_data)}\n")
            f.write(f"- **Risks Assessed**: {len(risks_data)}\n")
            f.write(f"- **Controls Designed**: {len(controls_data)}\n")
            f.write(f"- **Test Procedures Developed**: {len(tests_data)}\n\n")
            
            # Add key risk summary, focusing on high-priority risks
            high_risks = [r for r in risks_data if r.get('priority', 'Medium') == 'High']
            if high_risks:
                f.write("**Key High-Priority Risks**:\n")
                for i, risk in enumerate(high_risks[:5], 1):  # Show top 5 high risks
                    f.write(f"{i}. {risk.get('description', 'No description')[:100]}...\n")
                f.write("\n")
            
            # 2. Compliance Conditions (sorted by ID for reference)
            f.write("## 2. Compliance Conditions\n\n")
            for condition in sorted(conditions_data, key=lambda x: x.get('id', '')):
                f.write(f"### {condition.get('id', 'Unknown')}\n\n")
                f.write(f"**Description:** {condition.get('description', 'No description')}\n\n")
                f.write(f"**Reference:** {condition.get('reference', 'Unknown')}\n\n")
                f.write("---\n\n")
            
            # 3. Risk Assessment (sorted by priority)
            f.write("## 3. Risk Assessment\n\n")
            
            # Group risks by priority
            priorities = ['High', 'Medium', 'Low']
            for priority in priorities:
                priority_risks = [r for r in risks_data if r.get('priority', 'Medium') == priority]
                if priority_risks:
                    f.write(f"### {priority} Priority Risks\n\n")
                    for risk in priority_risks:
                        f.write(f"#### {risk.get('id', 'Unknown')}: {risk.get('condition_id', 'Unknown')}\n")
                        f.write(f"**Description**: {risk.get('description', 'No description')}\n")
                        f.write(f"**Likelihood**: {risk.get('likelihood', 'Medium')}\n")
                        f.write(f"**Impact**: {risk.get('impact', 'Medium')}\n")
                        f.write(f"**Source**: {risk.get('reference', 'Unknown')}\n\n")
            
            # 4. Control Framework (grouped by type)
            f.write("## 4. Control Framework\n\n")
            
            # Group controls by type
            control_types = set(c.get('type', 'Unknown') for c in controls_data)
            for control_type in sorted(control_types):
                type_controls = [c for c in controls_data if c.get('type', 'Unknown') == control_type]
                if type_controls:
                    f.write(f"### {control_type} Controls\n\n")
                    for control in type_controls:
                        f.write(f"#### {control.get('id', 'Unknown')}: {control.get('risk_id', 'Unknown')}\n")
                        f.write(f"**Description**: {control.get('description', 'No description')}\n")
                        f.write(f"**Implementation Considerations**: {control.get('implementation', 'No implementation guidance')}\n")
                        f.write(f"**Source**: {control.get('reference', 'Unknown')}\n\n")
            
            # 5. Audit Test Procedures (prioritized)
            f.write("## 5. Audit Test Procedures\n\n")
            
            # Categorize tests based on the priority of underlying risks
            for priority in priorities:
                # Find tests that test controls for risks with this priority
                priority_tests = []
                for test in tests_data:
                    control_id = test.get('control_id', '')
                    related_controls = [c for c in controls_data if c.get('id', '') == control_id]
                    if related_controls:
                        risk_id = related_controls[0].get('risk_id', '')
                        related_risks = [r for r in risks_data if r.get('id', '') == risk_id]
                        if related_risks and related_risks[0].get('priority', 'Medium') == priority:
                            priority_tests.append(test)
                
                if priority_tests:
                    f.write(f"### {priority} Priority Test Procedures\n\n")
                    for test in priority_tests:
                        f.write(f"#### {test.get('test_id', 'Unknown')}: {test.get('control_id', 'Unknown')}\n")
                        f.write(f"**Objective**: {test.get('objective', 'No objective')}\n")
                        f.write("**Test Steps**:\n")
                        for step in test.get('steps', ['No steps defined']):
                            f.write(f"- {step}\n")
                        f.write(f"**Required Evidence**: {test.get('evidence', 'No evidence requirements')}\n")
                        f.write(f"**Source**: {test.get('reference', 'Unknown')}\n\n")
            
            # 6. Comprehensive Traceability Matrix
            f.write("## 6. Comprehensive Traceability Matrix\n\n")
            f.write("This matrix shows the relationships between compliance conditions, risks, controls, and test procedures.\n\n")
            
            f.write("| Condition ID | Risk ID | Control ID | Test ID | Priority | Document Source |\n")
            f.write("|-------------|---------|------------|---------|----------|----------------|\n")
            
            # Sort by priority and then by condition ID for better readability
            # First build a list of rows with their priorities
            matrix_rows = []
            for condition_id, related_items in traceability_map.items():
                for item in related_items:
                    risk_id = item.get('risk_id', 'Unknown')
                    control_id = item.get('control_id', 'Unknown')
                    test_id = item.get('test_id', 'Unknown')
                    
                    # Find the priority of the risk
                    priority = 'Medium'  # Default
                    source = 'Unknown'
                    
                    for risk in risks_data:
                        if risk.get('id', '') == risk_id:
                            priority = risk.get('priority', 'Medium')
                            source = risk.get('reference', 'Unknown')
                            break
                    
                    matrix_rows.append({
                        'condition_id': condition_id,
                        'risk_id': risk_id,
                        'control_id': control_id,
                        'test_id': test_id,
                        'priority': priority,
                        'source': source
                    })
            
            # Sort rows by priority (High -> Medium -> Low) and then by condition ID
            priority_values = {'High': 0, 'Medium': 1, 'Low': 2}
            sorted_rows = sorted(matrix_rows, key=lambda x: (priority_values.get(x['priority'], 1), x['condition_id']))
            
            # Write sorted rows to matrix
            for row in sorted_rows:
                f.write(f"| {row['condition_id']} | {row['risk_id']} | {row['control_id']} | {row['test_id']} | {row['priority']} | {row['source']} |\n")
            
            # 7. Coverage Analysis
            f.write("\n## 7. Coverage Analysis\n\n")
            
            # Calculate coverage metrics
            conditions_with_risks = set()
            conditions_with_controls = set()
            conditions_with_tests = set()
            
            for condition_id, related_items in traceability_map.items():
                if any('risk_id' in item for item in related_items):
                    conditions_with_risks.add(condition_id)
                if any('control_id' in item for item in related_items):
                    conditions_with_controls.add(condition_id)
                if any('test_id' in item for item in related_items):
                    conditions_with_tests.add(condition_id)
            
            total_conditions = len(conditions_data)
            if total_conditions > 0:
                risk_coverage = (len(conditions_with_risks) / total_conditions) * 100
                control_coverage = (len(conditions_with_controls) / total_conditions) * 100
                test_coverage = (len(conditions_with_tests) / total_conditions) * 100
                
                f.write("**Coverage Metrics**:\n\n")
                f.write(f"- **Risk Coverage**: {risk_coverage:.1f}% of compliance conditions have associated risks\n")
                f.write(f"- **Control Coverage**: {control_coverage:.1f}% of compliance conditions have mitigating controls\n")
                f.write(f"- **Test Coverage**: {test_coverage:.1f}% of compliance conditions have verification tests\n\n")
                
                # Identify gaps in coverage
                conditions_without_risks = [c.get('id', '') for c in conditions_data if c.get('id', '') not in conditions_with_risks]
                conditions_without_controls = [c.get('id', '') for c in conditions_data if c.get('id', '') not in conditions_with_controls]
                conditions_without_tests = [c.get('id', '') for c in conditions_data if c.get('id', '') not in conditions_with_tests]
                
                if conditions_without_risks:
                    f.write("**Conditions Without Risk Assessment**:\n")
                    for i, cond_id in enumerate(conditions_without_risks[:10], 1):  # Limit to first 10
                        f.write(f"{i}. {cond_id}\n")
                    if len(conditions_without_risks) > 10:
                        f.write(f"...and {len(conditions_without_risks) - 10} more.\n")
                    f.write("\n")
                
                if conditions_without_controls:
                    f.write("**Conditions Without Controls**:\n")
                    for i, cond_id in enumerate(conditions_without_controls[:10], 1):  # Limit to first 10
                        f.write(f"{i}. {cond_id}\n")
                    if len(conditions_without_controls) > 10:
                        f.write(f"...and {len(conditions_without_controls) - 10} more.\n")
                    f.write("\n")
                
                if conditions_without_tests:
                    f.write("**Conditions Without Test Procedures**:\n")
                    for i, cond_id in enumerate(conditions_without_tests[:10], 1):  # Limit to first 10
                        f.write(f"{i}. {cond_id}\n")
                    if len(conditions_without_tests) > 10:
                        f.write(f"...and {len(conditions_without_tests) - 10} more.\n")
            
            # 8. Recommendations
            f.write("\n## 8. Recommendations\n\n")
            
            f.write("Based on the compliance analysis, the following recommendations are provided:\n\n")
            
            # Generate recommendations based on coverage analysis
            recommendations = []
            
            if conditions_without_risks:
                recommendations.append("Complete risk assessments for all identified compliance conditions to ensure comprehensive risk coverage.")
            
            if conditions_without_controls:
                recommendations.append("Design controls for all identified risks to ensure complete mitigation coverage.")
            
            if conditions_without_tests:
                recommendations.append("Develop test procedures for all controls to enable verification of control effectiveness.")
            
            # Add general recommendations
            recommendations.extend([
                "Prioritize addressing high-risk compliance gaps identified in the risk assessment.",
                "Establish a regular compliance monitoring program based on the test procedures.",
                "Implement the controls using a phased approach, starting with high-priority items.",
                "Develop training materials for staff on compliance requirements and controls.",
                "Establish a mechanism for periodically reviewing and updating the compliance framework."
            ])
            
            # Write recommendations
            for i, recommendation in enumerate(recommendations, 1):
                f.write(f"{i}. {recommendation}\n")
        
        logger.info(f"Successfully generated comprehensive final report to {report_file}")
        return True
        
    except Exception as e:
        logger.error(f"Error running generate report task: {str(e)}")
        return False

def create_traceability_mapping(conditions, risks, controls, tests):
    """Create a comprehensive traceability mapping from conditions to risks to controls to tests"""
    traceability_map = {}
    
    # Initialize entries for each condition
    for condition in conditions:
        condition_id = condition.get('id', '')
        traceability_map[condition_id] = []
    
    # Map risks to conditions
    for risk in risks:
        risk_id = risk.get('id', '')
        condition_id = risk.get('condition_id', '')
        
        if condition_id in traceability_map:
            # Add risk mapping
            traceability_map[condition_id].append({
                'risk_id': risk_id
            })
        else:
            # If condition not found, create a placeholder entry
            traceability_map[condition_id] = [{
                'risk_id': risk_id
            }]
    
    # Map controls to risks and conditions
    for control in controls:
        control_id = control.get('id', '')
        risk_id = control.get('risk_id', '')
        
        # Find the associated condition
        condition_id = ""
        for risk in risks:
            if risk.get('id', '') == risk_id:
                condition_id = risk.get('condition_id', '')
                break
        
        # If condition not found, try to infer from control ID
        if not condition_id:
            base_id = control_id.replace('C-', '')
            if '-' in base_id:
                base_id = base_id.split('-')[0]
            if 'C-' + base_id in traceability_map:
                condition_id = 'C-' + base_id
        
        if condition_id in traceability_map:
            # Find if we already have an entry for this risk
            found = False
            for item in traceability_map[condition_id]:
                if item.get('risk_id', '') == risk_id:
                    # Add control to existing risk entry
                    item['control_id'] = control_id
                    found = True
                    break
            
            if not found:
                # Add new entry
                traceability_map[condition_id].append({
                    'risk_id': risk_id,
                    'control_id': control_id
                })
        else:
            # If condition not found, create a placeholder entry
            traceability_map[condition_id] = [{
                'risk_id': risk_id,
                'control_id': control_id
            }]
    
    # Map tests to controls, risks, and conditions
    for test in tests:
        test_id = test.get('test_id', '')
        control_id = test.get('control_id', '')
        
        # Find the associated risk and condition
        risk_id = ""
        condition_id = ""
        
        for control in controls:
            if control.get('id', '') == control_id:
                risk_id = control.get('risk_id', '')
                break
        
        if risk_id:
            for risk in risks:
                if risk.get('id', '') == risk_id:
                    condition_id = risk.get('condition_id', '')
                    break
        
        # If condition not found, try to infer from control or test ID
        if not condition_id:
            base_id = control_id.replace('C-', '')
            if '-' in base_id:
                base_id = base_id.split('-')[0]
            if 'C-' + base_id in traceability_map:
                condition_id = 'C-' + base_id
            else:
                test_base_id = test_id.replace('T-', '')
                if '.' in test_base_id:
                    test_base_id = test_base_id.split('.')[0]
                if '-' in test_base_id:
                    test_base_id = test_base_id.split('-')[0]
                if 'C-' + test_base_id in traceability_map:
                    condition_id = 'C-' + test_base_id
        
        if condition_id in traceability_map:
            # Find if we already have an entry for this control
            found = False
            for item in traceability_map[condition_id]:
                if item.get('control_id', '') == control_id:
                    # Add test to existing control entry
                    item['test_id'] = test_id
                    found = True
                    break
            
            if not found:
                # Find if we have an entry for the associated risk
                if risk_id:
                    for item in traceability_map[condition_id]:
                        if item.get('risk_id', '') == risk_id and 'control_id' not in item:
                            # Add control and test to existing risk entry
                            item['control_id'] = control_id
                            item['test_id'] = test_id
                            found = True
                            break
                
                if not found:
                    # Add new entry
                    traceability_map[condition_id].append({
                        'risk_id': risk_id if risk_id else 'Unknown',
                        'control_id': control_id,
                        'test_id': test_id
                    })
        else:
            # If condition not found, create a placeholder entry
            traceability_map[condition_id] = [{
                'risk_id': risk_id if risk_id else 'Unknown',
                'control_id': control_id,
                'test_id': test_id
            }]
    
    # Ensure coverage: add entries for any conditions without mappings
    for condition in conditions:
        condition_id = condition.get('id', '')
        if condition_id not in traceability_map or not traceability_map[condition_id]:
            # Create placeholder entry
            risk_id = f"R-{condition_id.replace('C-', '')}"
            control_id = f"C-{condition_id.replace('C-', '')}"
            test_id = f"T-{condition_id.replace('C-', '')}"
            
            traceability_map[condition_id] = [{
                'risk_id': risk_id,
                'control_id': control_id,
                'test_id': test_id,
                'placeholder': True  # Mark as a placeholder
            }]
    
    return traceability_map

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