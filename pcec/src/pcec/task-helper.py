#!/usr/bin/env python3
"""
Helper script to run individual tasks in the workflow.
This can be useful when a specific task fails and you want to retry just that task.
Enhanced version with improved sorting, categorization, and relationship mapping.
"""

import os
import sys
import logging
import argparse
import re
from pathlib import Path
import yaml
from datetime import datetime
# Add this right after the existing import statements in task-helper.py
import sys
import os


def verify_report_sentences(report_text):
    """
    Verify and fix incomplete sentences in the report text
    """
    import re
    
    # Skip if empty
    if not report_text.strip():
        return report_text
    
    # Split the report into sections and paragraphs
    sections = []
    current_section = []
    
    for line in report_text.split('\n'):
        if line.startswith('#'):
            if current_section:
                sections.append('\n'.join(current_section))
                current_section = []
            current_section.append(line)
        else:
            current_section.append(line)
    
    if current_section:
        sections.append('\n'.join(current_section))
    
    # Process each section
    for i, section in enumerate(sections):
        paragraphs = re.split(r'\n\s*\n', section)
        
        for j, paragraph in enumerate(paragraphs):
            # Skip headers, code blocks, bullet points, tables
            if paragraph.startswith('#') or paragraph.startswith('```') or paragraph.startswith('-') or '|' in paragraph:
                continue
                
            # Handle attributes (e.g., **Description**: text)
            lines = paragraph.split('\n')
            for k, line in enumerate(lines):
                attr_match = re.match(r'^\s*\*\*([^:]+):\*\*\s*(.*)', line)
                if attr_match:
                    attr_name = attr_match.group(1)
                    attr_value = attr_match.group(2).strip()
                    
                    # Complete truncated attribute values
                    if attr_value and not any(attr_value.endswith(c) for c in ['.', '!', '?', ':', ';']):
                        # Check for common truncated endings
                        completed_value = complete_truncated_text(attr_value)
                        lines[k] = f"**{attr_name}:** {completed_value}"
                
                # Regular sentences
                elif line.strip() and not line.startswith('#') and not line.startswith('|'):
                    if not any(line.strip().endswith(c) for c in ['.', '!', '?', ':', ';']):
                        lines[k] = complete_truncated_text(line)
            
            paragraphs[j] = '\n'.join(lines)
        
        sections[i] = '\n\n'.join(paragraphs)
    
    return '\n\n'.join(sections)



def complete_truncated_text(text):
    """Complete truncated text based on common patterns"""
    text = text.strip()
    text_lower = text.lower()
    
    # Already complete
    if any(text.endswith(c) for c in ['.', '!', '?', ':', ';']):
        return text
    
    # Check for common truncated endings
    common_endings = {
        'and': " follow established procedures.",
        'or': " alternative approaches as specified.",
        'but': " exceptions must be documented.",
        'shall': " be implemented as required.",
        'should': " comply with relevant standards.",
        'must': " follow established protocols.",
        'with': " appropriate documentation.",
        'to': " relevant standards.",
        'by': " authorized personnel.",
        'for': " compliance purposes.",
        'in': " accordance with policy.",
        'as': " specified in the requirements.",
    }
    
    # Check for ending with truncating words
    for ending, completion in common_endings.items():
        if text_lower.endswith(ending):
            return text + completion
    
    # Check for sentences ending with modals followed by a word
    modal_suffix = re.search(r'(shall|should|must|will|may)\s+([a-z]+)$', text_lower)
    if modal_suffix:
        return text + " be properly documented and maintained."
    
    # Default completion
    if text.endswith(','):
        return text + " in accordance with established requirements."
    
    # Add period if no special case matched
    return text + "."

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

def determine_condition_category(description):
    """Determine the category of a condition based on its description"""
    description_lower = description.lower()
    
    # Define category keywords
    categories = {
        "Access Management": ["access", "authentication", "authorization", "login", "credential", "password"],
        "Data Protection": ["data", "information", "confidential", "encrypt", "sensitive", "store", "backup"],
        "Security": ["security", "cybersecurity", "protection", "vulnerability", "threat", "malware", "attack"],
        "Compliance": ["compliance", "regulatory", "regulation", "law", "requirement", "standard", "guideline"],
        "Training": ["training", "awareness", "education", "instruct", "teach", "learn", "knowledge"],
        "Monitoring": ["monitor", "surveillance", "detect", "alert", "observe", "track", "log"],
        "Reporting": ["report", "document", "record", "communication", "notify", "inform"],
        "Incident Management": ["incident", "event", "breach", "violation", "issue", "problem", "response"],
        "Physical Security": ["physical", "facility", "premise", "building", "location", "site", "area"],
        "Governance": ["governance", "policy", "procedure", "management", "oversight", "responsibility"]
    }
    
    # Find matching categories
    matched_categories = []
    for category, keywords in categories.items():
        if any(keyword in description_lower for keyword in keywords):
            matched_categories.append(category)
    
    # If multiple matches, choose the one with the most keyword matches
    if len(matched_categories) > 1:
        category_counts = {}
        for category in matched_categories:
            count = sum(1 for keyword in categories[category] if keyword in description_lower)
            category_counts[category] = count
        
        # Return the category with the highest count
        return max(category_counts.items(), key=lambda x: x[1])[0]
    
    # Return the matched category or default
    return matched_categories[0] if matched_categories else "General Requirements"

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

def determine_risk_category(description):
    """Determine the risk category based on description content"""
    description_lower = description.lower()
    
    # Check for keywords that indicate specific risk categories
    categories = {
        "Data Protection": ["data", "information", "privacy", "confidential", "sensitive"],
        "Access Control": ["access", "authentication", "authorization", "credential"],
        "Compliance": ["comply", "compliance", "regulatory", "regulation", "requirement"],
        "Operational": ["operation", "process", "procedure", "workflow", "efficiency"],
        "Financial": ["financial", "cost", "expense", "budget", "penalty", "fine"],
        "Security": ["security", "breach", "attack", "vulnerability", "threat"],
        "Reporting": ["report", "document", "notification", "disclosure"],
        "Governance": ["governance", "oversight", "management", "accountability"]
    }
    
    # Find matching categories
    matched_categories = []
    for category, keywords in categories.items():
        if any(keyword in description_lower for keyword in keywords):
            matched_categories.append(category)
    
    if matched_categories:
        # Return the first matched category
        return matched_categories[0]
    
    # Default category
    return "General Risk"

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
    conditions_file = output_dir / "1_extract_conditions_task_output.md"
    
    if not conditions_file.exists():
        logger.error(f"Conditions file {conditions_file} not found. Please run extract conditions task first.")
        return False
    
    # Generate a risk assessment using the conditions
    try:
        risks_file = output_dir / "2_identify_risks_task_output.md"
        
        # Parse the conditions
        conditions = parse_conditions_file(conditions_file)
        
        # Sort conditions by ID using natural sort
        conditions.sort(key=lambda x: natural_sort_key(x.get('id', '')))
        
        # Create risk assessment with categorization
        with open(risks_file, 'w') as f:
            f.write("# 2. Risk Assessment Results\n\n")
            
            # Group risks by priority (High, Medium, Low)
            for priority, likelihood_impact in [
                ("High", [("High", "High"), ("High", "Medium"), ("Medium", "High")]),
                ("Medium", [("Medium", "Medium"), ("High", "Low"), ("Low", "High")]),
                ("Low", [("Medium", "Low"), ("Low", "Medium"), ("Low", "Low")])
            ]:
                f.write(f"## {priority} Priority Risks\n\n")
                
                # Track risks by category within this priority
                risks_by_category = {}
                
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
                    
                    # Determine risk category
                    category = determine_risk_category(description)
                    
                    # Add to category tracking
                    if category not in risks_by_category:
                        risks_by_category[category] = []
                    
                    risks_by_category[category].append({
                        "id": risk_id,
                        "description": f"Risk of non-compliance with {condition_id}: {description}{domain_text}",
                        "likelihood": likelihood,
                        "impact": impact,
                        "source": reference
                    })
                    
                    risk_count += 1
                
                # Process each category
                for category, risks in sorted(risks_by_category.items()):
                    f.write(f"### {category}\n\n")
                    
                    # Sort risks by ID within category
                    sorted_risks = sorted(risks, key=lambda x: natural_sort_key(x.get('id', '')))
                    
                    for risk in sorted_risks:
                        f.write(f"#### {risk['id']}\n")
                        f.write(f"**Description**: {risk['description']}\n")
                        f.write(f"**Likelihood**: {risk['likelihood']}\n")
                        f.write(f"**Impact**: {risk['impact']}\n")
                        f.write(f"**Source**: {risk['source']}\n\n")
                
                # If no risks in this priority level, add a placeholder
                if risk_count == 0:
                    f.write("No risks identified in this priority level.\n\n")
        
        logger.info(f"Successfully generated risk assessment to {risks_file}")
        return True
        
    except Exception as e:
        logger.error(f"Error running identify risks task: {str(e)}")
        return False
def determine_control_category(control_type, description):
    """Determine the category of a control based on its type and description"""
    description_lower = description.lower()
    
    # Control categories based on common frameworks
    control_categories = {
        "Access Control": ["access", "authentication", "authorization", "credential", "login", "password"],
        "Change Management": ["change", "modification", "update", "version", "release"],
        "Configuration Management": ["configuration", "settings", "parameter", "setup"],
        "Data Protection": ["data", "information", "encryption", "protection", "confidential"],
        "Incident Management": ["incident", "breach", "event", "response", "recovery"],
        "Security Monitoring": ["monitor", "detect", "alert", "surveillance", "logging"],
        "Physical Security": ["physical", "facility", "premise", "building", "location"],
        "Risk Management": ["risk", "assessment", "mitigation", "treatment"],
        "Compliance": ["comply", "compliance", "regulation", "regulatory", "requirement"],
        "Business Continuity": ["continuity", "disaster", "recovery", "backup", "resilience"],
        "Security Awareness": ["awareness", "training", "education", "knowledge"]
    }
    
    # First try to match based on description
    for category, keywords in control_categories.items():
        if any(keyword in description_lower for keyword in keywords):
            return category
    
    # If no match, use control type for categorization
    if control_type:
        if control_type == "Preventive":
            return "Preventive Controls"
        elif control_type == "Detective":
            return "Detective Controls"
        elif control_type == "Corrective":
            return "Corrective Controls"
        elif control_type == "Administrative":
            return "Administrative Controls"
        elif control_type == "Technical":
            return "Technical Controls"
        elif control_type == "Physical":
            return "Physical Controls"
    
    # Default category
    return "General Controls"

def run_design_controls():
    """Run the design controls task"""
    logger.info("Running design controls task")
    
    # Check if identify_risks_task_output.md exists
    output_dir = find_output_directory()
    risks_file = output_dir / "2_identify_risks_task_output.md"
    
    if not risks_file.exists():
        logger.error(f"Risks file {risks_file} not found. Please run identify risks task first.")
        return False
    
    # Generate a control framework using the risks
    try:
        controls_file = output_dir / "3_design_controls_task_output.md"
        
        # Parse the risks
        risks = parse_risks_file(risks_file)
        
        # Sort risks by ID using natural sort
        risks.sort(key=lambda x: natural_sort_key(x.get('id', '')))
        
        # Create more comprehensive control framework
        with open(controls_file, 'w') as f:
            f.write("# 3. Control Framework\n\n")
            
            # Group controls by type
            control_types = ["Preventive", "Detective", "Corrective"]
            
            for control_type in control_types:
                f.write(f"## {control_type} Controls\n\n")
                
                # Track controls by category
                controls_by_category = {}
                
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
                    
                    # Determine control category
                    category = determine_control_category(control_type, control_desc)
                    
                    # Add to category tracking
                    if category not in controls_by_category:
                        controls_by_category[category] = []
                    
                    # Create a secondary control ID for high and medium priority risks
                    if priority in ["High", "Medium"]:
                        # Primary control
                        controls_by_category[category].append({
                            "id": control_id,
                            "risk_id": risk_id,
                            "description": control_desc,
                            "type": control_type,
                            "source": source,
                            "implementation": implementation
                        })
                        
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
                        
                        # Secondary control inherits the category of primary
                        controls_by_category[category].append({
                            "id": secondary_control_id,
                            "risk_id": risk_id,
                            "description": secondary_desc,
                            "type": secondary_type,
                            "source": source,
                            "implementation": secondary_impl
                        })
                    else:
                        # Just primary control for low priority risks
                        controls_by_category[category].append({
                            "id": control_id,
                            "risk_id": risk_id,
                            "description": control_desc,
                            "type": control_type,
                            "source": source,
                            "implementation": implementation
                        })
                
                # Process each category
                for category, controls in sorted(controls_by_category.items()):
                    f.write(f"### {category}\n\n")
                    
                    # Sort controls by ID within category
                    sorted_controls = sorted(controls, key=lambda x: natural_sort_key(x.get('id', '')))
                    
                    for control in sorted_controls:
                        f.write(f"#### {control['id']}: {control['risk_id']}\n")
                        f.write(f"**Description**: {control['description']}\n")
                        f.write(f"**Type**: {control['type']}\n")
                        f.write(f"**Source**: {control['source']}\n")
                        f.write(f"**Implementation Considerations**: {control['implementation']}\n\n")
        
        logger.info(f"Successfully generated control framework to {controls_file}")
        return True
        
    except Exception as e:
        logger.error(f"Error running design controls task: {str(e)}")
        return False
def determine_test_category(control_type, objective):
    """Determine the test category based on control type and test objective"""
    objective_lower = objective.lower()
    
    # Test categories based on control types and common test approaches
    test_categories = {
        "Access Control Testing": ["access", "authentication", "authorization", "credential", "login", "password"],
        "Change Management Testing": ["change", "modification", "update", "version", "release"],
        "Configuration Testing": ["configuration", "settings", "parameter", "setup"],
        "Data Protection Testing": ["data", "information", "encryption", "protection", "confidential"],
        "Incident Response Testing": ["incident", "breach", "event", "response", "recovery"],
        "Monitoring Testing": ["monitor", "detect", "alert", "surveillance", "logging"],
        "Physical Security Testing": ["physical", "facility", "premise", "building", "location"],
        "Compliance Testing": ["comply", "compliance", "regulation", "regulatory", "requirement"],
        "Performance Testing": ["performance", "efficiency", "throughput", "response time", "capacity"],
        "Security Testing": ["security", "vulnerability", "penetration", "exploit", "attack"]
    }
    
    # First try to match based on objective
    for category, keywords in test_categories.items():
        if any(keyword in objective_lower for keyword in keywords):
            return category
    
    # If no match, use control type for categorization
    if control_type:
        if control_type == "Preventive":
            return "Preventive Control Testing"
        elif control_type == "Detective":
            return "Detective Control Testing"
        elif control_type == "Corrective":
            return "Corrective Control Testing"
        elif control_type == "Administrative":
            return "Administrative Control Testing"
        elif control_type == "Technical":
            return "Technical Control Testing"
        elif control_type == "Physical":
            return "Physical Control Testing"
    
    # Default category
    return "General Test Procedures"

def run_develop_tests():
    """Run the develop tests task"""
    logger.info("Running develop tests task")
    
    # Check if design_controls_task_output.md exists
    output_dir = find_output_directory()
    controls_file = output_dir / "3_design_controls_task_output.md"
    
    if not controls_file.exists():
        logger.error(f"Controls file {controls_file} not found. Please run design controls task first.")
        return False
    
    # Generate an audit program using the controls
    try:
        tests_file = output_dir / "4_develop_tests_task_output.md"
        
        # Parse the controls
        controls = parse_controls_file(controls_file)
        
        # Sort controls by ID using natural sort
        controls.sort(key=lambda x: natural_sort_key(x.get('id', '')))
        
        # Create more comprehensive test procedures
        with open(tests_file, 'w') as f:
            f.write("# 4. Audit Test Procedures\n\n")
            
            # Group tests by category
            test_categories = {}
            
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
                if control_type.lower() == "detective":
                    steps = [
                        "1. Review detection mechanism documentation",
                        "2. Test detection capabilities with sample scenarios",
                        "3. Verify alert/notification process",
                        "4. Validate response procedures",
                        "5. Confirm detection effectiveness through simulated violations"
                    ]
                elif control_type.lower() == "preventive":
                    steps = [
                        "1. Review control implementation documentation",
                        "2. Test preventive measure with sample data",
                        "3. Attempt to bypass control (negative testing)",
                        "4. Verify logging of attempted violations",
                        "5. Confirm the control consistently prevents non-compliant actions"
                    ]
                elif control_type.lower() == "corrective":
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
                
                # Determine test category
                category = determine_test_category(control_type, objective)
                
                # Add to category tracking
                if category not in test_categories:
                    test_categories[category] = []
                
                # Add the test procedure
                test_categories[category].append({
                    "test_id": test_id,
                    "control_id": control_id,
                    "objective": objective,
                    "steps": steps,
                    "evidence": evidence,
                    "reference": reference
                })
                
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
                    
                    # Secondary test inherits the category of primary
                    test_categories[category].append({
                        "test_id": secondary_test_id,
                        "control_id": control_id,
                        "objective": secondary_objective,
                        "steps": secondary_steps,
                        "evidence": evidence,
                        "reference": reference
                    })
            
            # Process each category
            for category, tests in sorted(test_categories.items()):
                f.write(f"## {category}\n\n")
                
                # Sort tests by ID within category
                sorted_tests = sorted(tests, key=lambda x: natural_sort_key(x.get('test_id', '')))
                
                for test in sorted_tests:
                    f.write(f"### {test['test_id']}: {test['control_id']}\n")
                    f.write(f"**Objective**: {test['objective']}\n")
                    f.write("**Test Steps**:\n")
                    for step in test['steps']:
                        f.write(f"- {step}\n")
                    f.write(f"**Required Evidence**: {test['evidence']}\n")
                    f.write(f"**Source**: {test['reference']}\n\n")
        
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
        
        # Extract category sections
        category_pattern = re.compile(r'## ([^\n]+)\s*\n\n(.*?)(?=##|\Z)', re.DOTALL)
        
        for category_match in category_pattern.finditer(content):
            category = category_match.group(1).strip()
            category_content = category_match.group(2)
            
            # Extract condition entries within this category
            condition_pattern = re.compile(r'###\s+(C-\d+)\s*\n\n\*\*Description:\*\*\s*(.*?)\n\n\*\*Reference:\*\*\s*(.*?)(?:\n\n|\Z)', re.DOTALL)
            
            for match in condition_pattern.finditer(category_content):
                condition_id = match.group(1).strip()
                description = match.group(2).strip()
                reference = match.group(3).strip()
                
                conditions.append({
                    'id': condition_id,
                    'description': description,
                    'reference': reference,
                    'category': category
                })
        
        # If no category pattern matched, try the direct condition pattern
        if not conditions:
            condition_pattern = re.compile(r'###\s+(C-\d+)\s*\n\n\*\*Description:\*\*\s*(.*?)\n\n\*\*Reference:\*\*\s*(.*?)(?:\n\n|\Z)', re.DOTALL)
            
            for match in condition_pattern.finditer(content):
                condition_id = match.group(1).strip()
                description = match.group(2).strip()
                reference = match.group(3).strip()
                
                # Determine category
                category = determine_condition_category(description)
                
                conditions.append({
                    'id': condition_id,
                    'description': description,
                    'reference': reference,
                    'category': category
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
        
        # Extract priority sections
        priority_pattern = re.compile(r'## (High|Medium|Low) Priority Risks\s*\n\n(.*?)(?=##|\Z)', re.DOTALL)
        
        for priority_match in priority_pattern.finditer(content):
            priority = priority_match.group(1).strip()
            priority_content = priority_match.group(2)
            
            # Extract category sections within this priority
            category_pattern = re.compile(r'### ([^\n]+)\s*\n\n(.*?)(?=###|\Z)', re.DOTALL)
            
            for category_match in category_pattern.finditer(priority_content):
                category = category_match.group(1).strip()
                category_content = category_match.group(2)
                
                # Extract risk entries within this category
                risk_pattern = re.compile(r'####\s+(R-\d+)\s*\n\*\*Description\*\*:\s*(.*?)\n\*\*Likelihood\*\*:\s*(.*?)\n\*\*Impact\*\*:\s*(.*?)\n\*\*Source\*\*:\s*(.*?)(?:\n\n|\Z)', re.DOTALL)
                
                for match in risk_pattern.finditer(category_content):
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
                    
                    risks.append({
                        'id': risk_id,
                        'condition_id': condition_ids[0],  # Primary condition
                        'condition_ids': condition_ids,    # All related conditions
                        'description': description,
                        'likelihood': likelihood,
                        'impact': impact,
                        'priority': priority,
                        'category': category,
                        'reference': reference
                    })
        
        # If no structured sections found, try direct risk pattern
        if not risks:
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
                
                # Extract related condition IDs from description
                condition_ids = re.findall(r'C-\d+', description)
                if not condition_ids:
                    # If no condition IDs found, infer from risk ID
                    condition_ids = [f"C-{risk_id.replace('R-', '')}"]
                
                # Determine category
                category = determine_risk_category(description)
                
                risks.append({
                    'id': risk_id,
                    'condition_id': condition_ids[0],  # Primary condition
                    'condition_ids': condition_ids,    # All related conditions
                    'description': description,
                    'likelihood': likelihood,
                    'impact': impact,
                    'priority': priority,
                    'category': category,
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
        
        # Extract control type sections
        type_pattern = re.compile(r'## ([^\n]+) Controls\s*\n\n(.*?)(?=##|\Z)', re.DOTALL)
        
        for type_match in type_pattern.finditer(content):
            control_type = type_match.group(1).strip()
            type_content = type_match.group(2)
            
            # Extract category sections within this type
            category_pattern = re.compile(r'### ([^\n]+)\s*\n\n(.*?)(?=###|\Z)', re.DOTALL)
            
            for category_match in category_pattern.finditer(type_content):
                category = category_match.group(1).strip()
                category_content = category_match.group(2)
                
                # Extract control entries within this category
                control_pattern = re.compile(r'####\s+(C-\d+(?:-\d+)?):\s*(R-\d+)\s*\n\*\*Description\*\*:\s*(.*?)\n\*\*Type\*\*:\s*(.*?)\n\*\*Source\*\*:\s*(.*?)\n\*\*Implementation Considerations\*\*:\s*(.*?)(?:\n\n|\Z)', re.DOTALL)
                
                for match in control_pattern.finditer(category_content):
                    control_id = match.group(1).strip()
                    risk_id = match.group(2).strip()
                    description = match.group(3).strip()
                    specific_type = match.group(4).strip()
                    reference = match.group(5).strip()
                    implementation = match.group(6).strip()
                    
                    # Use specific type if available, otherwise use section type
                    final_type = specific_type if specific_type else control_type
                    
                    controls.append({
                        'id': control_id,
                        'risk_id': risk_id,
                        'description': description,
                        'type': final_type,
                        'implementation': implementation,
                        'category': category,
                        'reference': reference
                    })
        
        # If no structured sections found, try direct control pattern
        if not controls:
            control_pattern = re.compile(r'###\s+(C-\d+(?:-\d+)?):\s*(R-\d+)\s*\n\*\*Description\*\*:\s*(.*?)\n\*\*Type\*\*:\s*(.*?)\n\*\*Source\*\*:\s*(.*?)\n\*\*Implementation Considerations\*\*:\s*(.*?)(?:\n\n|\Z)', re.DOTALL)
            
            for match in control_pattern.finditer(content):
                control_id = match.group(1).strip()
                risk_id = match.group(2).strip()
                description = match.group(3).strip()
                control_type = match.group(4).strip()
                reference = match.group(5).strip()
                implementation = match.group(6).strip()
                
                # Determine category
                category = determine_control_category(control_type, description)
                
                controls.append({
                    'id': control_id,
                    'risk_id': risk_id,
                    'description': description,
                    'type': control_type,
                    'implementation': implementation,
                    'category': category,
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
        
        # Extract category sections
        category_pattern = re.compile(r'## ([^\n]+)\s*\n\n(.*?)(?=##|\Z)', re.DOTALL)
        
        for category_match in category_pattern.finditer(content):
            category = category_match.group(1).strip()
            category_content = category_match.group(2)
            
            # Extract test entries within this category
            test_pattern = re.compile(r'###\s+(T-\d+(?:-[A-Z])?)\s*:\s*(C-\d+(?:-\d+)?)\s*\n\*\*Objective\*\*:\s*(.*?)\n\*\*Test Steps\*\*:\s*(.*?)\n\*\*Required Evidence\*\*:\s*(.*?)\n\*\*Source\*\*:\s*(.*?)(?:\n\n|\Z)', re.DOTALL)
            
            for match in test_pattern.finditer(category_content):
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
                
                tests.append({
                    'test_id': test_id,
                    'control_id': control_id,
                    'objective': objective,
                    'steps': steps,
                    'evidence': evidence,
                    'category': category,
                    'reference': reference
                })
        
        # If no structured sections found, try direct test pattern
        if not tests:
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
                
                # Determine category
                category = determine_test_category("", objective)
                
                tests.append({
                    'test_id': test_id,
                    'control_id': control_id,
                    'objective': objective,
                    'steps': steps,
                    'evidence': evidence,
                    'category': category,
                    'reference': reference
                })
        
        return tests
    except Exception as e:
        logger.error(f"Error parsing tests file: {str(e)}")
        return []

def create_category_mappings(conditions, risks, controls, tests):
    """Create mappings between categories"""
    # Group items by category
    condition_categories = {}
    risk_categories = {}
    control_categories = {}
    test_categories = {}
    
    # Map conditions to categories
    for condition in conditions:
        category = condition.get('category', 'General Requirements')
        if category not in condition_categories:
            condition_categories[category] = []
        condition_categories[category].append(condition.get('id', ''))
    
    # Map risks to categories
    for risk in risks:
        category = risk.get('category', 'General Risk')
        if category not in risk_categories:
            risk_categories[category] = []
        risk_categories[category].append(risk.get('id', ''))
    
    # Map controls to categories
    for control in controls:
        category = control.get('category', 'General Controls')
        if category not in control_categories:
            control_categories[category] = []
        control_categories[category].append(control.get('id', ''))
    
    # Map tests to categories
    for test in tests:
        category = test.get('category', 'General Test Procedures')
        if category not in test_categories:
            test_categories[category] = []
        test_categories[category].append(test.get('test_id', ''))
    
    # Create relationships between categories
    category_mappings = {
        'condition_to_risk': {},
        'risk_to_control': {},
        'control_to_test': {}
    }
    
    # Map condition categories to risk categories
    for condition_category, condition_ids in condition_categories.items():
        category_mappings['condition_to_risk'][condition_category] = {}
        
        for risk in risks:
            risk_category = risk.get('category', 'General Risk')
            
            # Check if this risk relates to any conditions in this category
            risk_condition_ids = risk.get('condition_ids', [risk.get('condition_id', '')])
            
            if any(cond_id in condition_ids for cond_id in risk_condition_ids):
                if risk_category not in category_mappings['condition_to_risk'][condition_category]:
                    category_mappings['condition_to_risk'][condition_category][risk_category] = []
                
                category_mappings['condition_to_risk'][condition_category][risk_category].append(risk.get('id', ''))
    
    # Map risk categories to control categories
    for risk_category, risk_ids in risk_categories.items():
        category_mappings['risk_to_control'][risk_category] = {}
        
        for control in controls:
            control_category = control.get('category', 'General Controls')
            
            # Check if this control relates to any risks in this category
            control_risk_id = control.get('risk_id', '')
            
            if control_risk_id in risk_ids:
                if control_category not in category_mappings['risk_to_control'][risk_category]:
                    category_mappings['risk_to_control'][risk_category][control_category] = []
                
                category_mappings['risk_to_control'][risk_category][control_category].append(control.get('id', ''))
    
    # Map control categories to test categories
    for control_category, control_ids in control_categories.items():
        category_mappings['control_to_test'][control_category] = {}
        
        for test in tests:
            test_category = test.get('category', 'General Test Procedures')
            
            # Check if this test relates to any controls in this category
            test_control_id = test.get('control_id', '')
            
            if test_control_id in control_ids:
                if test_category not in category_mappings['control_to_test'][control_category]:
                    category_mappings['control_to_test'][control_category][test_category] = []
                
                category_mappings['control_to_test'][control_category][test_category].append(test.get('test_id', ''))
    
    return category_mappings



def run_generate_report():
    """Run the generate report task with improved handling for large reports"""
    logger.info("Running generate report task")
    
    # Check if all prerequisite files exist
    output_dir = find_output_directory()
    files_to_check = [
        "1_extract_conditions_task_output.md",
        "2_identify_risks_task_output.md",
        "3_design_controls_task_output.md",
        "4_develop_tests_task_output.md"
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
        report_file = output_dir / "5_final_compliance_report.md"
        
        # Load all component data
        logger.info("Loading component data for report generation...")
        conditions_data = parse_conditions_file(output_dir / "1_extract_conditions_task_output.md")
        risks_data = parse_risks_file(output_dir / "2_identify_risks_task_output.md")
        controls_data = parse_controls_file(output_dir / "3_design_controls_task_output.md")
        tests_data = parse_tests_file(output_dir / "4_develop_tests_task_output.md")
        
        # Log counts for debugging
        logger.info(f"Loaded {len(conditions_data)} conditions, {len(risks_data)} risks, {len(controls_data)} controls, and {len(tests_data)} tests")
        
        # Create category mappings
        logger.info("Creating category mappings...")
        category_mappings = create_category_mappings(conditions_data, risks_data, controls_data, tests_data)
        
        # Build report in chunks to avoid memory issues
        logger.info("Generating report in sections...")
        report_sections = []
        
        # 1. Executive Summary
        exec_summary = "# Comprehensive Compliance Analysis Report\n\n"
        exec_summary += "## 1. Executive Summary\n\n"
        exec_summary += "This report provides a comprehensive analysis of compliance conditions identified from policy documents, "
        exec_summary += "the associated risks of non-compliance, controls designed to mitigate these risks, and test procedures "
        exec_summary += "to verify control effectiveness. The analysis ensures full traceability from compliance conditions to "
        exec_summary += "risks, controls, and audit procedures.\n\n"
        
        # Add summary statistics
        exec_summary += f"**Summary Statistics**:\n"
        exec_summary += f"- **Compliance Conditions Identified**: {len(conditions_data)}\n"
        exec_summary += f"- **Risks Assessed**: {len(risks_data)}\n"
        exec_summary += f"- **Controls Designed**: {len(controls_data)}\n"
        exec_summary += f"- **Test Procedures Developed**: {len(tests_data)}\n\n"
        
        # Count categories
        condition_categories = set(c.get('category', 'General Requirements') for c in conditions_data)
        risk_categories = set(r.get('category', 'General Risk') for r in risks_data)
        control_categories = set(c.get('category', 'General Controls') for c in controls_data)
        test_categories = set(t.get('category', 'General Test Procedures') for t in tests_data)
        
        exec_summary += f"- **Condition Categories**: {len(condition_categories)}\n"
        exec_summary += f"- **Risk Categories**: {len(risk_categories)}\n"
        exec_summary += f"- **Control Categories**: {len(control_categories)}\n"
        exec_summary += f"- **Test Categories**: {len(test_categories)}\n\n"
        
        # Add key risk summary, focusing on high-priority risks
        high_risks = [r for r in risks_data if r.get('priority', 'Medium') == 'High']
        if high_risks:
            # Sort high risks by ID
            sorted_high_risks = sorted(high_risks, key=lambda r: natural_sort_key(r.get('id', '')))
            exec_summary += "**Key High-Priority Risks**:\n"
            for i, risk in enumerate(sorted_high_risks[:5], 1):  # Show top 5 high risks
                exec_summary += f"{i}. {risk.get('description', 'No description')[:100]}...\n"
            exec_summary += "\n"
            
        report_sections.append(exec_summary)
        
        # 2. Compliance Conditions Summary
        cond_summary = "## 2. Compliance Conditions by Category\n\n"
        
        # Group conditions by category
        cond_by_category = {}
        for condition in conditions_data:
            category = condition.get('category', 'General Requirements')
            if category not in cond_by_category:
                cond_by_category[category] = []
            cond_by_category[category].append(condition)
        
        for category, conditions in sorted(cond_by_category.items()):
            cond_summary += f"### {category}\n\n"
            cond_summary += f"Total conditions in this category: {len(conditions)}\n\n"
            
            # Sort conditions by ID within category
            sorted_conditions = sorted(conditions, key=lambda x: natural_sort_key(x.get('id', '')))
            
            cond_summary += "| Condition ID | Description | Source |\n"
            cond_summary += "|-------------|-------------|--------|\n"
            
            for condition in sorted_conditions[:10]:  # Increased to show more conditions
                # Truncate description for table readability, but avoid adding unnecessary ellipses
                desc = condition.get('description', 'No description')
                if len(desc) > 100:
                    # If it already ends with ellipsis, don't add another one
                    if desc.endswith(('...', '..', '.,')):
                        # Just truncate
                        desc = desc[:97]
                    else:
                        # Add ellipsis only if we're actually truncating
                        desc = desc[:97] + "..."
                
                cond_summary += f"| {condition.get('id', 'Unknown')} | {desc} | {condition.get('reference', 'Unknown')} |\n"
            
            if len(sorted_conditions) > 10:
                cond_summary += f"*Plus {len(sorted_conditions) - 10} more conditions in this category*\n\n"
            else:
                cond_summary += "\n"
                
        report_sections.append(cond_summary)
        
        # 3. Risk Assessment Summary
        risk_summary = "## 3. Risk Assessment by Category\n\n"
        
        # Group risks by category
        risk_by_category = {}
        for risk in risks_data:
            category = risk.get('category', 'General Risk')
            if category not in risk_by_category:
                risk_by_category[category] = []
            risk_by_category[category].append(risk)
        
        for category, risks in sorted(risk_by_category.items()):
            risk_summary += f"### {category}\n\n"
            risk_summary += f"Total risks in this category: {len(risks)}\n\n"
            
            # Count risks by priority within category
            priority_counts = {"High": 0, "Medium": 0, "Low": 0}
            for risk in risks:
                priority = risk.get('priority', 'Medium')
                priority_counts[priority] += 1
            
            risk_summary += "**Priority Distribution**:\n"
            risk_summary += f"- High: {priority_counts['High']}\n"
            risk_summary += f"- Medium: {priority_counts['Medium']}\n"
            risk_summary += f"- Low: {priority_counts['Low']}\n\n"
            
            # Sort risks by ID within category
            sorted_risks = sorted(risks, key=lambda x: natural_sort_key(x.get('id', '')))
            
            risk_summary += "| Risk ID | Related Conditions | Description | Priority |\n"
            risk_summary += "|---------|-------------------|-------------|----------|\n"
            
            for risk in sorted_risks[:10]:  # Increased to show more risks
                # Get all related conditions
                condition_ids = risk.get('condition_ids', [risk.get('condition_id', 'Unknown')])
                conditions_text = ', '.join(condition_ids)
                
                # Truncate description for table readability, but avoid adding unnecessary ellipses
                desc = risk.get('description', 'No description')
                if len(desc) > 100:
                    # If it already ends with ellipsis, don't add another one
                    if desc.endswith(('...', '..', '.,')):
                        # Just truncate
                        desc = desc[:97]
                    else:
                        # Add ellipsis only if we're actually truncating
                        desc = desc[:97] + "..."
                
                risk_summary += f"| {risk.get('id', 'Unknown')} | {conditions_text} | {desc} | {risk.get('priority', 'Medium')} |\n"
            
            if len(sorted_risks) > 10:
                risk_summary += f"*Plus {len(sorted_risks) - 10} more risks in this category*\n\n"
            else:
                risk_summary += "\n"
                
        report_sections.append(risk_summary)
        
        # 4. Control Framework Summary
        control_summary = "## 4. Control Framework by Category\n\n"
        
        # Group controls by category
        control_by_category = {}
        for control in controls_data:
            category = control.get('category', control.get('type', 'General Controls'))
            if category not in control_by_category:
                control_by_category[category] = []
            control_by_category[category].append(control)
        
        for category, controls in sorted(control_by_category.items()):
            control_summary += f"### {category}\n\n"
            control_summary += f"Total controls in this category: {len(controls)}\n\n"
            
            # Count controls by type within category
            type_counts = {}
            for control in controls:
                control_type = control.get('type', 'Unknown')
                if control_type not in type_counts:
                    type_counts[control_type] = 0
                type_counts[control_type] += 1
            
            control_summary += "**Control Type Distribution**:\n"
            for control_type, count in sorted(type_counts.items()):
                control_summary += f"- {control_type}: {count}\n"
            control_summary += "\n"
            
            # Sort controls by ID within category
            sorted_controls = sorted(controls, key=lambda x: natural_sort_key(x.get('id', '')))
            
            control_summary += "| Control ID | Related Risk | Description | Type |\n"
            control_summary += "|------------|--------------|-------------|------|\n"
            
            for control in sorted_controls[:10]:  # Increased to show more controls
                # Truncate description for table readability, but avoid adding unnecessary ellipses
                desc = control.get('description', 'No description')
                if len(desc) > 100:
                    # If it already ends with ellipsis, don't add another one
                    if desc.endswith(('...', '..', '.,')):
                        # Just truncate
                        desc = desc[:97]
                    else:
                        # Add ellipsis only if we're actually truncating
                        desc = desc[:97] + "..."
                
                control_summary += f"| {control.get('id', 'Unknown')} | {control.get('risk_id', 'Unknown')} | {desc} | {control.get('type', 'Unknown')} |\n"
            
            if len(sorted_controls) > 10:
                control_summary += f"*Plus {len(sorted_controls) - 10} more controls in this category*\n\n"
            else:
                control_summary += "\n"
                
        report_sections.append(control_summary)
        
        # 5. Audit Test Procedures Summary
        test_summary = "## 5. Audit Test Procedures by Category\n\n"
        
        # Group tests by category
        test_by_category = {}
        for test in tests_data:
            category = test.get('category', 'General Test Procedures')
            if category not in test_by_category:
                test_by_category[category] = []
            test_by_category[category].append(test)
        
        for category, tests in sorted(test_by_category.items()):
            test_summary += f"### {category}\n\n"
            test_summary += f"Total test procedures in this category: {len(tests)}\n\n"
            
            # Sort tests by ID within category
            sorted_tests = sorted(tests, key=lambda x: natural_sort_key(x.get('test_id', '')))
            
            test_summary += "| Test ID | Related Control | Test Objective |\n"
            test_summary += "|---------|-----------------|----------------|\n"
            
            for test in sorted_tests[:10]:  # Increased to show more tests
                # Truncate objective for table readability, but avoid adding unnecessary ellipses
                objective = test.get('objective', 'No objective')
                if len(objective) > 100:
                    # If it already ends with ellipsis, don't add another one
                    if objective.endswith(('...', '..', '.,')):
                        # Just truncate
                        objective = objective[:97]
                    else:
                        # Add ellipsis only if we're actually truncating
                        objective = objective[:97] + "..."
                
                test_summary += f"| {test.get('test_id', 'Unknown')} | {test.get('control_id', 'Unknown')} | {objective} |\n"
            
            if len(sorted_tests) > 10:
                test_summary += f"*Plus {len(sorted_tests) - 10} more test procedures in this category*\n\n"
            else:
                test_summary += "\n"
                
        report_sections.append(test_summary)
        
        # 6. Generate Category Traceability Matrix section
        traceability_matrix = "## 6. Category Traceability Matrices\n\n"
        
        # Condition Category to Risk Category
        traceability_matrix += "### Condition Categories to Risk Categories\n\n"
        traceability_matrix += "This matrix shows how condition categories map to risk categories.\n\n"
        traceability_matrix += "| Condition Category | Risk Category | Sample Risk IDs |\n"
        traceability_matrix += "|---------------------|---------------|---------------|\n"
        
        for condition_category, risk_mappings in sorted(category_mappings['condition_to_risk'].items()):
            if not risk_mappings:
                traceability_matrix += f"| {condition_category} | *No related risks* | - |\n"
                continue
                
            # First row with condition category
            first_row = True
            for risk_category, risk_ids in sorted(risk_mappings.items()):
                if not risk_ids:
                    continue
                    
                # Show up to 3 sample risk IDs
                sample_ids = ", ".join(sorted(risk_ids, key=natural_sort_key)[:3])
                if len(risk_ids) > 3:
                    sample_ids += f", +{len(risk_ids) - 3} more"
                
                if first_row:
                    traceability_matrix += f"| {condition_category} | {risk_category} | {sample_ids} |\n"
                    first_row = False
                else:
                    # Subsequent rows without repeating condition category
                    traceability_matrix += f"| | {risk_category} | {sample_ids} |\n"
        
        # Risk Category to Control Category
        traceability_matrix += "\n### Risk Categories to Control Categories\n\n"
        traceability_matrix += "This matrix shows how risk categories map to control categories.\n\n"
        traceability_matrix += "| Risk Category | Control Category | Sample Control IDs |\n"
        traceability_matrix += "|---------------|-----------------|-------------------|\n"
        
        for risk_category, control_mappings in sorted(category_mappings['risk_to_control'].items()):
            if not control_mappings:
                traceability_matrix += f"| {risk_category} | *No related controls* | - |\n"
                continue
                
            # First row with risk category
            first_row = True
            for control_category, control_ids in sorted(control_mappings.items()):
                if not control_ids:
                    continue
                    
                # Show up to 3 sample control IDs
                sample_ids = ", ".join(sorted(control_ids, key=natural_sort_key)[:3])
                if len(control_ids) > 3:
                    sample_ids += f", +{len(control_ids) - 3} more"
                
                if first_row:
                    traceability_matrix += f"| {risk_category} | {control_category} | {sample_ids} |\n"
                    first_row = False
                else:
                    # Subsequent rows without repeating risk category
                    traceability_matrix += f"| | {control_category} | {sample_ids} |\n"
        
        # Control Category to Test Category
        traceability_matrix += "\n### Control Categories to Test Categories\n\n"
        traceability_matrix += "This matrix shows how control categories map to test categories.\n\n"
        traceability_matrix += "| Control Category | Test Category | Sample Test IDs |\n"
        traceability_matrix += "|------------------|--------------|----------------|\n"
        
        for control_category, test_mappings in sorted(category_mappings['control_to_test'].items()):
            if not test_mappings:
                traceability_matrix += f"| {control_category} | *No related tests* | - |\n"
                continue
                
            # First row with control category
            first_row = True
            for test_category, test_ids in sorted(test_mappings.items()):
                if not test_ids:
                    continue
                    
                # Show up to 3 sample test IDs
                sample_ids = ", ".join(sorted(test_ids, key=natural_sort_key)[:3])
                if len(test_ids) > 3:
                    sample_ids += f", +{len(test_ids) - 3} more"
                
                if first_row:
                    traceability_matrix += f"| {control_category} | {test_category} | {sample_ids} |\n"
                    first_row = False
                else:
                    # Subsequent rows without repeating control category
                    traceability_matrix += f"| | {test_category} | {sample_ids} |\n"
                    
        report_sections.append(traceability_matrix)
        
        # 7. Detailed item mapping
        detailed_mapping = "## 7. Detailed Item Traceability\n\n"
        detailed_mapping += "This section provides detailed traceability between specific items.\n\n"
        
        # Create a map of conditions to all related items
        traceability_map = {}
        
        # Build condition to risk mapping
        for risk in risks_data:
            condition_ids = risk.get('condition_ids', [risk.get('condition_id', '')])
            for condition_id in condition_ids:
                if condition_id not in traceability_map:
                    traceability_map[condition_id] = {'risks': [], 'controls': [], 'tests': []}
                traceability_map[condition_id]['risks'].append(risk.get('id', ''))
        
        # Build risk to control mapping
        for control in controls_data:
            risk_id = control.get('risk_id', '')
            # Find all conditions that map to this risk
            for condition_id, mapping in traceability_map.items():
                if risk_id in mapping['risks']:
                    mapping['controls'].append(control.get('id', ''))
        
        # Build control to test mapping
        for test in tests_data:
            control_id = test.get('control_id', '')
            # Find all conditions that map to this control
            for condition_id, mapping in traceability_map.items():
                if control_id in mapping['controls']:
                    mapping['tests'].append(test.get('test_id', ''))
        
        # Create traceability table
        detailed_mapping += "### Item Traceability Matrix\n\n"
        detailed_mapping += "| Condition | Risks | Controls | Tests |\n"
        detailed_mapping += "|-----------|-------|----------|-------|\n"
        
        # Sort condition IDs using natural sort
        for condition_id in sorted(traceability_map.keys(), key=natural_sort_key):
            mapping = traceability_map[condition_id]
            
            # Get unique, sorted lists
            unique_risks = sorted(set(mapping['risks']), key=natural_sort_key)
            unique_controls = sorted(set(mapping['controls']), key=natural_sort_key)
            unique_tests = sorted(set(mapping['tests']), key=natural_sort_key)
            
            # Format for table (shorten if too many)
            risks_text = ", ".join(unique_risks[:3])
            if len(unique_risks) > 3:
                risks_text += f" +{len(unique_risks) - 3} more"
                
            controls_text = ", ".join(unique_controls[:3])
            if len(unique_controls) > 3:
                controls_text += f" +{len(unique_controls) - 3} more"
                
            tests_text = ", ".join(unique_tests[:3])
            if len(unique_tests) > 3:
                tests_text += f" +{len(unique_tests) - 3} more"
            
            detailed_mapping += f"| {condition_id} | {risks_text} | {controls_text} | {tests_text} |\n"
            
        report_sections.append(detailed_mapping)
        
        # 8. Recommendations
        recommendations = "## 8. Recommendations\n\n"
        recommendations += "Based on the comprehensive analysis of compliance requirements, risks, controls, and test procedures, the following recommendations are provided:\n\n"
        
        # Add category-specific recommendations
        recommendations += "### Category-Specific Recommendations\n\n"
        
        # Find categories with high-priority risks
        high_risk_categories = set()
        for risk in risks_data:
            if risk.get('priority', 'Medium') == 'High':
                high_risk_categories.add(risk.get('category', 'General Risk'))
        
        for category in sorted(high_risk_categories):
            recommendations += f"**{category}**:\n"
            recommendations += f"- Prioritize implementation of controls related to high-priority risks in this category\n"
            recommendations += f"- Establish dedicated oversight for all {category} compliance areas\n"
            recommendations += f"- Develop enhanced monitoring mechanisms specific to {category} risks\n\n"
        
        # Add general recommendations
        recommendations += "### General Recommendations\n\n"
        recommendations += "1. Establish a regular compliance monitoring program based on the test procedures outlined in this report\n"
        recommendations += "2. Implement a phased approach to control implementation, starting with high-priority items\n"
        recommendations += "3. Develop comprehensive training materials for staff on compliance requirements and controls\n"
        recommendations += "4. Establish a mechanism for periodically reviewing and updating the compliance framework\n"
        recommendations += "5. Create a compliance dashboard to track implementation status and effectiveness of controls\n"
        
        report_sections.append(recommendations)
        
        # Write report sections to file
        logger.info(f"Writing report to {report_file}...")
        with open(report_file, 'w', encoding='utf-8') as f:
            for section in report_sections:
                f.write(section)
                f.flush()  # Flush after each section to ensure it's written



        logger.info("Verifying report completeness...")
        try:
            report_content = ""
            with open(report_file, 'r', encoding='utf-8') as f:
                report_content = f.read()
            
            verified_content = verify_report_sentences(report_content)
            
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(verified_content)
            logger.info("Report verification and fixing complete")
        except Exception as e:
            logger.warning(f"Error during report verification: {str(e)}")



        # Make sure the file was created
        if report_file.exists():
            logger.info(f"Successfully generated comprehensive final report to {report_file}")
            
            # Also create a copy with the alternate naming pattern for compatibility
            alternate_report = output_dir / "final_compliance_report.md"
            import shutil
            shutil.copy(report_file, alternate_report)
            logger.info(f"Created compatibility copy at {alternate_report}")
            
            # Verify the report was written completely
            report_size = report_file.stat().st_size
            logger.info(f"Report size: {report_size} bytes")
            
            return True
        else:
            logger.error(f"Report generation failed - file {report_file} not found")
            return False
        
    except Exception as e:
        logger.error(f"Error running generate report task: {str(e)}")
        logger.error(f"Exception details: {traceback.format_exc()}")
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