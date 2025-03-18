#!/usr/bin/env python3
"""
Helper script to run individual tasks in the workflow.
This can be useful when a specific task fails and you want to retry just that task.
Enhanced version with improved sorting, relationship mapping, and reporting.
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

def natural_sort_key(s):
    """
    Natural sorting key function that handles numeric parts correctly
    This ensures that C-1, C-2, C-10 sort properly instead of C-1, C-10, C-2
    """
    return [int(text) if text.isdigit() else text.lower() 
            for text in re.split(r'(\d+)', str(s))]

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

def identify_domain_keywords(description):
    """Identify domain keywords from the description"""
    description_lower = description.lower()
    domains = []
    
    # Check for domain keywords
    domain_checks = [
        ("access", ["access", "authentication", "authorization", "login", "credential", "password"]),
        ("data", ["data", "information", "confidential", "encrypt", "sensitive", "store"]),
        ("security", ["security", "protect", "vulnerability", "threat", "malware", "attack"]),
        ("compliance", ["compliance", "regulatory", "regulation", "law", "requirement", "standard"]),
        ("monitoring", ["monitor", "detect", "alert", "observe", "track", "log"]),
        ("reporting", ["report", "document", "record", "communication", "notify", "inform"])
    ]
    
    for domain, keywords in domain_checks:
        if any(keyword in description_lower for keyword in keywords):
            domains.append(domain)
    
    return domains

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
        
        # Sort conditions by ID using natural sort
        conditions.sort(key=lambda x: natural_sort_key(x.get('id', '')))
        
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
                    
                    # Determine likelihood and impact based on keywords
                    likelihood, impact = determine_likelihood_impact(description)
                    
                    # Only include if matches our desired priority level
                    if (likelihood, impact) not in likelihood_impact:
                        continue
                    
                    # Create risk entry
                    risk_id = f"R-{condition_id.replace('C-', '')}"
                    
                    # Identify domain keywords for more specific risk descriptions
                    domains = identify_domain_keywords(description)
                    domain_text = ""
                    if domains:
                        domain_text = f" (domains: {', '.join(domains)})"
                    
                    f.write(f"### {risk_id}\n")
                    f.write(f"**Description**: Risk of non-compliance with {condition_id}: {description}{domain_text}\n")
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
        
        # Sort risks by ID using natural sort
        risks.sort(key=lambda x: natural_sort_key(x.get('id', '')))
        
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
                    
                    # Extract any condition IDs from the risk description
                    condition_ids = re.findall(r'C-\d+', description)
                    condition_ref = f" Related conditions: {', '.join(condition_ids)}" if condition_ids else ""
                    
                    # Extract domain keywords
                    domains = identify_domain_keywords(description)
                    domain_specifics = ""
                    
                    # Create domain-specific control descriptions
                    if domains:
                        for domain in domains:
                            if domain == "access":
                                domain_specifics += " Includes access controls, authentication, and authorization procedures."
                            elif domain == "data":
                                domain_specifics += " Includes data classification, protection, and handling protocols."
                            elif domain == "security":
                                domain_specifics += " Includes security safeguards and protection mechanisms."
                            elif domain == "compliance":
                                domain_specifics += " Includes regulatory tracking and compliance verification."
                            elif domain == "monitoring":
                                domain_specifics += " Includes continuous monitoring and alerting mechanisms."
                            elif domain == "reporting":
                                domain_specifics += " Includes reporting process and documentation requirements."
                    
                    # Generate control description based on risk and control type
                    if control_type == "Preventive":
                        control_desc = f"Implement specific preventive measures to ensure compliance with {description.replace('Risk of non-compliance with ', '')} through proactive verification, validation, and restriction mechanisms.{domain_specifics}{condition_ref}"
                        implementation = "Implementation includes specific input validation requirements, pre-approval workflows, system restrictions, automated verification, and targeted training."
                    elif control_type == "Detective":
                        control_desc = f"Establish specific monitoring and detection systems to identify potential non-compliance with {description.replace('Risk of non-compliance with ', '')} through regular audits and exception reporting.{domain_specifics}{condition_ref}"
                        implementation = "Implementation includes targeted compliance scanning, real-time alerts, specific audits, exception reporting, and specialized monitoring tools."
                    elif control_type == "Corrective":
                        control_desc = f"Develop specific remediation procedures to address identified instances of non-compliance with {description.replace('Risk of non-compliance with ', '')} through structured response mechanisms.{domain_specifics}{condition_ref}"
                        implementation = "Implementation includes detailed incident response procedures, targeted remediation plans, root cause analysis, documentation of corrective actions, and verification procedures."
                    else:
                        control_desc = f"Implement specific controls to ensure compliance with {description.replace('Risk of non-compliance with ', '')}.{domain_specifics}{condition_ref}"
                        implementation = "Implementation requires targeted monitoring and verification mechanisms specific to the compliance requirements."
                    
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
                            secondary_desc = f"Establish targeted monitoring system to detect non-compliance with {description.replace('Risk of non-compliance with ', '')} during operation.{domain_specifics}{condition_ref}"
                            secondary_impl = "Implementation includes specific logging mechanisms, periodic reviews, targeted alerts, and compliance verification procedures."
                        else:
                            secondary_type = "Preventive"
                            secondary_desc = f"Implement specific preventive measures to ensure compliance with {description.replace('Risk of non-compliance with ', '')} prior to processing or execution.{domain_specifics}{condition_ref}"
                            secondary_impl = "Implementation includes system validations, input controls, restrictions, and preventive configurations specific to the compliance requirements."
                        
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
        
        # Sort controls by ID using natural sort
        controls.sort(key=lambda x: natural_sort_key(x.get('id', '')))
        
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
                
                # Extract risk IDs for comprehensive testing
                risk_ids = []
                risk_match = re.search(r'(R-\d+)', description)
                if risk_match:
                    risk_ids.append(risk_match.group(1))
                
                # Extract domain keywords
                domains = identify_domain_keywords(description)
                domain_specifics = ""
                
                if domains:
                    domain_specifics = f" Domains: {', '.join(domains)}."
                
                # Generate test objective - make it specific to the control
                objective = f"Verify implementation and effectiveness of control {control_id}{domain_specifics}"
                
                # Generate test steps based on control type
                if control_type == "Preventive":
                    steps = [
                        "1. Review specific control implementation documentation",
                        "2. Test the preventive measure with targeted sample data",
                        "3. Attempt to bypass the control through authorized testing",
                        "4. Verify logging of attempted violations and prevention activities",
                        "5. Confirm the control consistently prevents non-compliant actions in all required scenarios"
                    ]
                elif control_type == "Detective":
                    steps = [
                        "1. Review the specific detection mechanism configuration",
                        "2. Test detection capabilities using targeted test scenarios",
                        "3. Verify the alert/notification process functions as designed",
                        "4. Validate the response procedures for detected violations",
                        "5. Confirm detection effectiveness through simulated compliance violations"
                    ]
                elif control_type == "Corrective":
                    steps = [
                        "1. Review specific correction procedures documentation",
                        "2. Test the correction workflow using realistic scenarios",
                        "3. Verify timeliness of corrective actions against requirements",
                        "4. Confirm proper documentation of all correction activities",
                        "5. Test correction effectiveness through follow-up verification"
                    ]
                else:
                    steps = [
                        "1. Review control documentation for completeness",
                        "2. Interview responsible personnel to confirm understanding",
                        "3. Test control implementation with specific test cases",
                        "4. Verify control effectiveness against defined requirements",
                        "5. Validate ongoing monitoring and maintenance processes"
                    ]
                
                # Add domain-specific test steps
                additional_steps = []
                
                if "access" in domains:
                    additional_steps.append("Test access restrictions with multiple user profiles")
                    additional_steps.append("Verify segregation of duties is properly enforced")
                
                if "data" in domains:
                    additional_steps.append("Verify data protection measures meet specific requirements")
                    additional_steps.append("Test data handling procedures against compliance criteria")
                
                if "monitoring" in domains:
                    additional_steps.append("Verify monitoring thresholds are appropriately configured")
                    additional_steps.append("Test alert generation and escalation processes")
                
                if "reporting" in domains:
                    additional_steps.append("Verify reports contain all required elements")
                    additional_steps.append("Test report generation process for accuracy and completeness")
                
                # Add step numbers to additional steps
                for i, step in enumerate(additional_steps, 6):
                    steps.append(f"{i}. {step}")
                
                # Determine appropriate evidence requirements
                evidence = "Documentation of control implementation, test results, screenshots of configurations"
                
                if "access" in domains:
                    evidence += ", access control matrices, user permission lists"
                
                if "data" in domains:
                    evidence += ", data protection configurations, encryption settings"
                
                if "monitoring" in domains:
                    evidence += ", monitoring logs, alert configurations"
                
                if "reporting" in domains:
                    evidence += ", sample reports, report verification documentation"
                
                # Write the test procedure
                f.write(f"## {test_id}: {control_id}\n")
                f.write(f"**Objective**: {objective}\n")
                f.write("**Test Steps**:\n")
                for step in steps:
                    f.write(f"- {step}\n")
                f.write(f"**Required Evidence**: {evidence}\n")
                f.write(f"**Source**: {reference}\n\n")
                
                # For complex controls, create an additional test procedure
                if '-' in control_id or len(description) > 100:
                    # Create secondary test ID
                    secondary_test_id = f"{test_id}-B"
                    
                    # Generate a more specific objective for the secondary test
                    if "report" in description.lower():
                        secondary_aspect = "reporting capabilities and accuracy"
                        secondary_steps = [
                            "1. Identify all reporting requirements in the control",
                            "2. Sample reports to verify completeness and accuracy",
                            "3. Trace reported data to source systems to verify accuracy",
                            "4. Verify report distribution follows requirements",
                            "5. Test the reporting mechanism for reliability"
                        ]
                    elif "monitor" in description.lower():
                        secondary_aspect = "monitoring effectiveness"
                        secondary_steps = [
                            "1. Review monitoring configurations and thresholds",
                            "2. Verify monitoring covers all required elements",
                            "3. Test alert mechanisms with specific scenarios",
                            "4. Confirm monitoring results are properly reviewed",
                            "5. Verify issues identified through monitoring are addressed"
                        ]
                    elif "access" in description.lower():
                        secondary_aspect = "access control enforcement"
                        secondary_steps = [
                            "1. Review access control matrices and configurations",
                            "2. Test access permissions with different user profiles",
                            "3. Verify authentication mechanisms meet requirements",
                            "4. Test access recertification and removal processes",
                            "5. Verify segregation of duties is properly enforced"
                        ]
                    else:
                        secondary_aspect = "specific control components"
                        secondary_steps = [
                            "1. Identify specific components requiring detailed testing",
                            "2. Develop targeted test cases for these components",
                            "3. Execute specific test cases and document results",
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
            
            # Extract related condition IDs from description
            condition_ids = re.findall(r'C-\d+', description)
            if not condition_ids:
                # If no condition IDs found, infer from risk ID
                condition_ids = [f"C-{risk_id.replace('R-', '')}"]
            
            # Determine priority based on likelihood and impact
            priority = "Medium"  # Default
            if likelihood == "High" and impact == "High":
                priority = "High"
            elif likelihood == "Low" and impact == "Low":
                priority = "Low"
            
            risks.append({
                'id': risk_id,
                'condition_id': condition_ids[0],  # Primary condition
                'condition_ids': condition_ids,    # All related conditions
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
            
            # Extract all related risk IDs
            risk_ids = re.findall(r'R-\d+', description)
            if not risk_ids:
                risk_ids = [risk_id]
            elif risk_id not in risk_ids:
                risk_ids.insert(0, risk_id)  # Ensure primary risk ID is included
            
            controls.append({
                'id': control_id,
                'risk_id': risk_id,
                'risk_ids': risk_ids,
                'description': description,
                'type': control_type,
                'implementation': implementation,
                'reference': reference,
                'domains': identify_domain_keywords(description)
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
                if line.strip().startswith('-'):
                    # Remove leading dash and whitespace
                    step = line.strip()[2:].strip()
                    steps.append(step)
            
            # Extract all related control IDs
            control_ids = re.findall(r'C-\d+(?:-\d+)?', objective)
            if not control_ids:
                control_ids = [control_id]
            elif control_id not in control_ids:
                control_ids.insert(0, control_id)  # Ensure primary control ID is included
            
            tests.append({
                'test_id': test_id,
                'control_id': control_id,
                'control_ids': control_ids,
                'objective': objective,
                'steps': steps,
                'evidence': evidence,
                'reference': reference,
                'domains': identify_domain_keywords(objective)
            })
        
        return tests
    except Exception as e:
        logger.error(f"Error parsing tests file: {str(e)}")
        return []
    
def create_traceability_mapping(conditions, risks, controls, tests):
    """Create a comprehensive traceability mapping from conditions to risks to controls to tests"""
    traceability_map = {}
    
    # Initialize entries for each condition
    for condition in conditions:
        condition_id = condition.get('id', '')
        if condition_id:
            traceability_map[condition_id] = []
    
    # Map risks to conditions
    for risk in risks:
        risk_id = risk.get('id', '')
        condition_ids = risk.get('condition_ids', [risk.get('condition_id', '')])
        
        for condition_id in condition_ids:
            if condition_id in traceability_map:
                traceability_map[condition_id].append({
                    'risk_id': risk_id,
                    'description': risk.get('description', ''),
                    'priority': risk.get('priority', 'Medium')
                })
    
    # Map controls to risks and conditions
    for control in controls:
        control_id = control.get('id', '')
        risk_ids = control.get('risk_ids', [control.get('risk_id', '')])
        
        for risk_id in risk_ids:
            # Find conditions related to this risk
            for condition_id, rels in traceability_map.items():
                for rel in rels:
                    if rel.get('risk_id') == risk_id:
                        # Add control to the relationship
                        if 'control_id' not in rel:
                            rel['control_id'] = control_id
                            rel['control_type'] = control.get('type', 'Preventive')
                        elif 'additional_controls' not in rel:
                            rel['additional_controls'] = [control_id]
                        else:
                            rel['additional_controls'].append(control_id)
    
    # Map tests to controls, risks, and conditions
    for test in tests:
        test_id = test.get('test_id', '')
        control_ids = test.get('control_ids', [test.get('control_id', '')])
        
        for control_id in control_ids:
            # Find relationships containing this control
            for condition_id, rels in traceability_map.items():
                for rel in rels:
                    if rel.get('control_id') == control_id or (
                        'additional_controls' in rel and control_id in rel['additional_controls']):
                        # Add test to the relationship
                        if 'test_id' not in rel:
                            rel['test_id'] = test_id
                        elif 'additional_tests' not in rel:
                            rel['additional_tests'] = [test_id]
                        else:
                            rel['additional_tests'].append(test_id)
    
    return traceability_map

def generate_traceability_table(traceability_map):
    """Generate a traceability table from relationship data"""
    rows = []
    
    # Process all relationships into flattened rows for the table
    for condition_id, rels in traceability_map.items():
        for rel in rels:
            risk_id = rel.get('risk_id', '')
            control_id = rel.get('control_id', '')
            test_id = rel.get('test_id', '')
            priority = rel.get('priority', 'Medium')
            
            # Add main row
            rows.append({
                'condition_id': condition_id,
                'risk_id': risk_id,
                'control_id': control_id,
                'test_id': test_id,
                'priority': priority
            })
            
            # Add rows for additional controls if any
            if 'additional_controls' in rel:
                for additional_control in rel['additional_controls']:
                    rows.append({
                        'condition_id': condition_id,
                        'risk_id': risk_id,
                        'control_id': additional_control,
                        'test_id': test_id,
                        'priority': priority
                    })
            
            # Add rows for additional tests if any
            if 'additional_tests' in rel:
                for additional_test in rel['additional_tests']:
                    rows.append({
                        'condition_id': condition_id,
                        'risk_id': risk_id,
                        'control_id': control_id,
                        'test_id': additional_test,
                        'priority': priority
                    })
    
    # Sort rows by priority and then by condition ID for better readability
    priority_values = {'High': 0, 'Medium': 1, 'Low': 2}
    sorted_rows = sorted(rows, key=lambda x: (
        priority_values.get(x['priority'], 1),
        natural_sort_key(x['condition_id']),
        natural_sort_key(x['risk_id']),
        natural_sort_key(x['control_id']),
        natural_sort_key(x['test_id'])
    ))
    
    # Remove duplicates (can happen due to many-to-many relationships)
    unique_rows = []
    seen = set()
    for row in sorted_rows:
        row_key = f"{row['condition_id']}|{row['risk_id']}|{row['control_id']}|{row['test_id']}"
        if row_key not in seen:
            unique_rows.append(row)
            seen.add(row_key)
    
    # Generate table
    table = "| Condition ID | Risk ID | Control ID | Test ID | Priority |\n"
    table += "|-------------|---------|------------|---------|----------|\n"
    
    for row in unique_rows:
        table += f"| {row['condition_id']} | {row['risk_id']} | {row['control_id']} | {row['test_id']} | {row['priority']} |\n"
    
    return table

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
        
        # Generate traceability table
        traceability_table = generate_traceability_table(traceability_map)
        
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
                # Sort high risks by ID
                sorted_high_risks = sorted(high_risks, key=lambda r: natural_sort_key(r.get('id', '')))
                f.write("**Key High-Priority Risks**:\n")
                for i, risk in enumerate(sorted_high_risks[:5], 1):  # Show top 5 high risks
                    f.write(f"{i}. {risk.get('description', 'No description')[:100]}...\n")
                f.write("\n")
            
            # 2. Compliance Conditions Summary
            f.write("## 2. Compliance Conditions Summary\n\n")
            f.write("This section provides a summary of the identified compliance conditions. Full details are available in the extract_conditions_task_output.md file.\n\n")
            
            # Sort conditions by ID
            sorted_conditions = sorted(conditions_data, key=lambda x: natural_sort_key(x.get('id', '')))
            
            f.write("| Condition ID | Description | Source |\n")
            f.write("|-------------|-------------|--------|\n")
            
            for condition in sorted_conditions:
                # Truncate description for table readability
                desc = condition.get('description', 'No description')
                if len(desc) > 100:
                    desc = desc[:97] + "..."
                
                f.write(f"| {condition.get('id', 'Unknown')} | {desc} | {condition.get('reference', 'Unknown')} |\n")
            
            # 3. Risk Assessment Summary
            f.write("\n## 3. Risk Assessment Summary\n\n")
            f.write("This section provides a summary of the risk assessment. Full details are available in the identify_risks_task_output.md file.\n\n")
            
            # Group risks by priority
            priorities = ['High', 'Medium', 'Low']
            
            for priority in priorities:
                priority_risks = [r for r in risks_data if r.get('priority', 'Medium') == priority]
                if priority_risks:
                    # Sort risks by ID within priority group
                    sorted_risks = sorted(priority_risks, key=lambda x: natural_sort_key(x.get('id', '')))
                    
                    f.write(f"### {priority} Priority Risks\n\n")
                    f.write("| Risk ID | Related Conditions | Description | Likelihood | Impact |\n")
                    f.write("|---------|-------------------|-------------|------------|--------|\n")
                    
                    for risk in sorted_risks:
                        # Get all related conditions
                        condition_ids = risk.get('condition_ids', [risk.get('condition_id', 'Unknown')])
                        conditions_text = ', '.join(condition_ids)
                        
                        # Truncate description for table readability
                        desc = risk.get('description', 'No description')
                        if len(desc) > 100:
                            desc = desc[:97] + "..."
                        
                        f.write(f"| {risk.get('id', 'Unknown')} | {conditions_text} | {desc} | {risk.get('likelihood', 'Medium')} | {risk.get('impact', 'Medium')} |\n")
            
            # 4. Control Framework Summary
            f.write("\n## 4. Control Framework Summary\n\n")
            f.write("This section provides a summary of the control framework. Full details are available in the design_controls_task_output.md file.\n\n")
            
            # Group controls by type
            control_types = set(c.get('type', 'Unknown') for c in controls_data)
            
            for control_type in sorted(control_types):
                type_controls = [c for c in controls_data if c.get('type', 'Unknown') == control_type]
                if type_controls:
                    # Sort controls by ID within type
                    sorted_controls = sorted(type_controls, key=lambda x: natural_sort_key(x.get('id', '')))
                    
                    f.write(f"### {control_type} Controls\n\n")
                    f.write("| Control ID | Related Risks | Description |\n")
                    f.write("|------------|--------------|-------------|\n")
                    
                    for control in sorted_controls:
                        # Get all related risks
                        risk_ids = control.get('risk_ids', [control.get('risk_id', 'Unknown')])
                        risks_text = ', '.join(risk_ids)
                        
                        # Truncate description for table readability
                        desc = control.get('description', 'No description')
                        if len(desc) > 100:
                            desc = desc[:97] + "..."
                        
                        f.write(f"| {control.get('id', 'Unknown')} | {risks_text} | {desc} |\n")
            
            # 5. Audit Test Procedures Summary
            f.write("\n## 5. Audit Test Procedures Summary\n\n")
            f.write("This section provides a summary of the audit test procedures. Full details are available in the develop_tests_task_output.md file.\n\n")
            
            # Sort tests by ID for consistent display
            sorted_tests = sorted(tests_data, key=lambda x: natural_sort_key(x.get('test_id', '')))
            
            f.write("| Test ID | Related Controls | Test Objective |\n")
            f.write("|---------|-----------------|----------------|\n")
            
            for test in sorted_tests:
                # Get all related controls
                control_ids = test.get('control_ids', [test.get('control_id', 'Unknown')])
                controls_text = ', '.join(control_ids)
                
                # Truncate objective for table readability
                objective = test.get('objective', 'No objective')
                if len(objective) > 100:
                    objective = objective[:97] + "..."
                
                f.write(f"| {test.get('test_id', 'Unknown')} | {controls_text} | {objective} |\n")
            
            # 6. Comprehensive Traceability Matrix
            f.write("\n## 6. Comprehensive Traceability Matrix\n\n")
            f.write("This matrix shows the relationships between compliance conditions, risks, controls, and test procedures with full many-to-many relationship support.\n\n")
            
            # Insert the generated traceability table
            f.write(traceability_table)
            
            # 7. Coverage Analysis
            f.write("\n## 7. Coverage Analysis\n\n")
            
            # Calculate coverage metrics
            conditions_with_risks = set()
            conditions_with_controls = set()
            conditions_with_tests = set()
            
            for condition_id, rels in traceability_map.items():
                if any('risk_id' in rel for rel in rels):
                    conditions_with_risks.add(condition_id)
                if any('control_id' in rel for rel in rels):
                    conditions_with_controls.add(condition_id)
                if any('test_id' in rel for rel in rels):
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
                
                # Sort the lists using natural sort
                conditions_without_risks.sort(key=natural_sort_key)
                conditions_without_controls.sort(key=natural_sort_key)
                conditions_without_tests.sort(key=natural_sort_key)
                
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