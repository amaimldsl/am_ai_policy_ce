# tools/Parser_Utils.py - Enhanced version
import re
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class ParserUtils:
    """
    Centralized parsing utilities to standardize data extraction and formatting
    across different tools and eliminate redundancy.
    """
    
    @staticmethod
    def parse_conditions(conditions_text: str) -> List[Dict[str, Any]]:
        """
        Parse condition text into a standardized structure.
        Works with multiple input formats.
        """
        parsed = []
        
        try:
            # Primary pattern for condition extraction
            condition_patterns = [
                # Format: C-123: Description [Reference]
                re.compile(r'(C-\d+):\s*(.*?)(?:\s*\[([^]]+)\])?$', re.MULTILINE),
                
                # Format: ### C-123
                re.compile(r'###\s*(C-\d+)\s*\n\n\*\*Description:\*\*\s*(.*?)\n\n\*\*Reference:\*\*\s*(.*?)(?:\n\n|\Z)', re.DOTALL),
                
                # Format: ## C-123: Description
                re.compile(r'##\s*(C-\d+):\s*(.*?)(?:\n|$)', re.DOTALL),
                
                # Format: Condition ID: 123 - Description
                re.compile(r'Condition ID:\s*(\d+)\s*-\s*(.*?)(?:\n|$)', re.DOTALL)
            ]
            
            # Try each pattern
            for pattern in condition_patterns:
                matches = list(pattern.finditer(conditions_text))
                if matches:
                    for match in matches:
                        if len(match.groups()) >= 2:
                            # Handle condition ID variations
                            if match.group(1).startswith('C-'):
                                condition_id = match.group(1)
                            else:
                                condition_id = f"C-{match.group(1)}"
                                
                            description = match.group(2).strip()
                            reference = match.group(3) if len(match.groups()) > 2 and match.group(3) else ""
                            
                            parsed.append({
                                "id": condition_id,
                                "description": description,
                                "reference": reference
                            })
                    break  # Stop if we found matches with this pattern
            
            # If no matches found with standard patterns, try the more detailed ### C-123 format
            if not parsed:
                detailed_pattern = re.compile(r'###\s*(C-\d+)\s*\n\n\*\*Description:\*\*\s*(.*?)\n\n\*\*Reference:\*\*\s*(.*?)(?:\n\n---|\Z)', re.DOTALL)
                matches = list(detailed_pattern.finditer(conditions_text))
                if matches:
                    for match in matches:
                        condition_id = match.group(1)
                        description = match.group(2).strip()
                        reference = match.group(3).strip()
                        
                        parsed.append({
                            "id": condition_id,
                            "description": description,
                            "reference": reference
                        })
            
            # If still no matches found, try to extract from unstructured text
            if not parsed:
                # Look for lines with keywords that suggest requirements
                requirement_indicators = [
                    'shall', 'must', 'should', 'required', 'obligated', 'necessary',
                    'mandatory', 'comply', 'compliance', 'adhere', 'ensure', 'maintain',
                    'establish', 'implement', 'provide', 'responsible', 'accountable',
                    'follow', 'conduct', 'perform', 'review', 'verify', 'document',
                    'record', 'report', 'complete', 'submit', 'authorize', 'approve',
                    'prohibit', 'restrict', 'limit', 'safeguard', 'protect', 'prevent'
                ]
                lines = conditions_text.split('\n')
                
                for i, line in enumerate(lines):
                    for indicator in requirement_indicators:
                        if indicator in line.lower():
                            # Look for a potential condition ID in this or nearby lines
                            condition_id = None
                            for j in range(max(0, i-2), min(len(lines), i+3)):
                                id_match = re.search(r'C-\d+', lines[j])
                                if id_match:
                                    condition_id = id_match.group(0)
                                    break
                            
                            if not condition_id:
                                condition_id = f"C-{len(parsed)+1}"
                            
                            # Look for reference information
                            reference = "Unknown"
                            for j in range(max(0, i-5), min(len(lines), i+5)):
                                if "[Document:" in lines[j]:
                                    reference = lines[j].strip()
                                    break
                            
                            parsed.append({
                                "id": condition_id,
                                "description": line.strip(),
                                "reference": reference
                            })
                            break
        except Exception as e:
            logger.error(f"Error parsing conditions: {str(e)}")
            # Return an empty array with at least one default entry
            parsed = [{
                "id": "C-1",
                "description": "Failed to parse conditions. Please check the input format.",
                "reference": "Error"
            }]
        
        return parsed
    
    @staticmethod
    def parse_risks(risks_text: str) -> List[Dict[str, Any]]:
        """
        Parse risk text into a standardized structure.
        Works with multiple input formats.
        """
        parsed = []
        
        try:
            # Pattern for structured risk entries
            risk_patterns = [
                # Format: ### R-123
                re.compile(r'###\s*(R-\d+)\s*\n\*\*Description\*\*:\s*(.*?)\n\*\*Likelihood\*\*:\s*(.*?)\n\*\*Impact\*\*:\s*(.*?)\n\*\*Source\*\*:\s*(.*?)(?:\n\n|\Z)', re.DOTALL),
                
                # Format: ## R-123: C-456
                re.compile(r'##\s*(R-\d+):\s*(C-\d+)\s*\n', re.DOTALL),
                
                # Format with description and source separate lines
                re.compile(r'##\s*(R-\d+).*?\n\*\*Description\*\*:\s*(.*?)\n\*\*Source\*\*:\s*(.*?)(?:\n|$)', re.DOTALL),
                
                # Format: #### R-123: C-456
                re.compile(r'####\s*(R-\d+):\s*(C-\d+)\s*\n\*\*Description\*\*:\s*(.*?)\n\*\*Likelihood\*\*:\s*(.*?)\n\*\*Impact\*\*:\s*(.*?)\n\*\*Source\*\*:\s*(.*?)(?:\n\n|\Z)', re.DOTALL)
            ]
            
            # Try each structured pattern
            matched = False
            for pattern in risk_patterns:
                matches = list(pattern.finditer(risks_text))
                if matches:
                    matched = True
                    for match in matches:
                        # Handle the different patterns
                        if len(match.groups()) >= 5:  # Pattern 1 (### R-123) or Pattern 4 (#### R-123: C-456)
                            risk_id = match.group(1).strip()
                            
                            if len(match.groups()) >= 6:  # Pattern 4
                                condition_id = match.group(2).strip()
                                description = match.group(3).strip()
                                likelihood = match.group(4).strip()
                                impact = match.group(5).strip()
                                reference = match.group(6).strip()
                            else:  # Pattern 1
                                description = match.group(2).strip()
                                likelihood = match.group(3).strip()
                                impact = match.group(4).strip()
                                reference = match.group(5).strip()
                                
                                # Infer condition ID from risk ID
                                condition_id = f"C-{risk_id.replace('R-', '')}"
                        elif len(match.groups()) >= 3 and "Description" in match.group(0) and "Source" in match.group(0):  # Pattern 3
                            risk_id = match.group(1).strip()
                            description = match.group(2).strip()
                            reference = match.group(3).strip()
                            
                            # Set default values for likelihood and impact
                            likelihood = "Medium"
                            impact = "Medium"
                            
                            # Infer condition ID from risk ID
                            condition_id = f"C-{risk_id.replace('R-', '')}"
                        else:  # Pattern 2 (## R-123: C-456)
                            risk_id = match.group(1).strip()
                            condition_id = match.group(2).strip()
                            
                            # Look for description elsewhere
                            desc_match = re.search(rf'{re.escape(risk_id)}.*?\n\*\*Description\*\*:\s*(.*?)\n', risks_text, re.DOTALL)
                            source_match = re.search(rf'{re.escape(risk_id)}.*?\n\*\*Source\*\*:\s*(.*?)(?:\n|$)', risks_text, re.DOTALL)
                            likelihood_match = re.search(rf'{re.escape(risk_id)}.*?\n\*\*Likelihood\*\*:\s*(.*?)\n', risks_text, re.DOTALL)
                            impact_match = re.search(rf'{re.escape(risk_id)}.*?\n\*\*Impact\*\*:\s*(.*?)\n', risks_text, re.DOTALL)
                            
                            description = desc_match.group(1).strip() if desc_match else f"Risk associated with {condition_id}"
                            reference = source_match.group(1).strip() if source_match else "Unknown"
                            likelihood = likelihood_match.group(1).strip() if likelihood_match else "Medium"
                            impact = impact_match.group(1).strip() if impact_match else "Medium"
                        
                        # Determine priority based on likelihood and impact
                        priority = "Medium"  # Default
                        if likelihood == "High" and impact == "High":
                            priority = "High"
                        elif likelihood == "Low" and impact == "Low":
                            priority = "Low"
                        
                        parsed.append({
                            "id": risk_id,
                            "condition_id": condition_id,
                            "description": description,
                            "likelihood": likelihood,
                            "impact": impact,
                            "priority": priority,
                            "reference": reference
                        })
            
            # If no matches found with the standard patterns, try other formats
            if not matched or not parsed:
                # Try the "Risk Analysis Results" format
                section_pattern = re.compile(r'## (High|Medium|Low) Priority Risks\s*\n\n(.*?)(?=##|\Z)', re.DOTALL)
                risk_item_pattern = re.compile(r'### (R-\d+)\s*\n\*\*Description\*\*:\s*(.*?)\n\*\*Likelihood\*\*:\s*(.*?)\n\*\*Impact\*\*:\s*(.*?)\n\*\*Source\*\*:\s*(.*?)(?:\n\n|\Z)', re.DOTALL)
                
                for section_match in section_pattern.finditer(risks_text):
                    priority = section_match.group(1)
                    section_content = section_match.group(2)
                    
                    for risk_match in risk_item_pattern.finditer(section_content):
                        risk_id = risk_match.group(1)
                        description = risk_match.group(2).strip()
                        likelihood = risk_match.group(3).strip()
                        impact = risk_match.group(4).strip()
                        reference = risk_match.group(5).strip()
                        
                        # Infer condition ID from risk ID
                        condition_id = f"C-{risk_id.replace('R-', '')}"
                        
                        parsed.append({
                            "id": risk_id,
                            "condition_id": condition_id,
                            "description": description,
                            "likelihood": likelihood,
                            "impact": impact,
                            "priority": priority,
                            "reference": reference
                        })
            
            # If still no matches found, try the "Condition ID: 123" format
            if not parsed:
                # Try the "Condition ID: 123" format
                condition_pattern = re.compile(r'Condition ID:\s*(\d+)\s*-\s*(.*?)(?:\n|$)', re.DOTALL)
                matches = list(condition_pattern.finditer(risks_text))
                
                if matches:
                    for match in matches:
                        condition_id = match.group(1)
                        description = match.group(2).strip()
                        
                        parsed.append({
                            "id": f"R-{condition_id}",  # Create risk ID based on condition ID
                            "condition_id": f"C-{condition_id}",
                            "description": f"Risk of non-compliance with condition {condition_id}: {description}",
                            "likelihood": "Medium",  # Default values
                            "impact": "Medium",
                            "priority": "Medium",
                            "reference": "Risk Assessment Document"  # Default reference
                        })
                else:
                    # Last resort - create single entry from whole text
                    parsed.append({
                        "id": "R-Unknown",
                        "condition_id": "C-Unknown",
                        "description": risks_text.strip(),
                        "likelihood": "Medium",
                        "impact": "Medium",
                        "priority": "Medium",
                        "reference": "Unknown"
                    })
        except Exception as e:
            logger.error(f"Error parsing risks: {str(e)}")
            # Return an empty array with at least one default entry
            parsed = [{
                "id": "R-1",
                "condition_id": "C-1",
                "description": "Failed to parse risks. Please check the input format.",
                "likelihood": "Medium",
                "impact": "Medium",
                "priority": "Medium",
                "reference": "Error"
            }]
                
        return parsed
    
    @staticmethod
    def parse_controls(controls_text: str) -> List[Dict[str, Any]]:
        """
        Parse control text into a standardized structure.
        Works with multiple input formats.
        """
        parsed = []
        
        try:
            # First check if we have the placeholder message
            if "provides specific controls mapped to each identified risk" in controls_text and len(controls_text) < 200:
                # This is just a placeholder, we need to generate controls from risks
                return []  # Return empty array to trigger fallback controls
            
            # Standard pattern for control entries
            control_patterns = [
                # Format: ### C-123: R-123
                re.compile(r'###\s*(C-\d+(?:-\d+)?):\s*(R-\d+)\s*\n\*\*Description\*\*:\s*(.*?)\n\*\*Type\*\*:\s*(.*?)\n\*\*Source\*\*:\s*(.*?)\n\*\*Implementation Considerations\*\*:\s*(.*?)(?:\n\n|\Z)', re.DOTALL),
                
                # Format: #### C-123: R-123 (used in the report)
                re.compile(r'####\s*(C-\d+(?:-\d+)?):\s*(R-\d+)\s*\n\*\*Description\*\*:\s*(.*?)\n\*\*Implementation Considerations\*\*:\s*(.*?)\n\*\*Source\*\*:\s*(.*?)(?:\n\n|\Z)', re.DOTALL),
                
                # Format: ## Preventive Controls\n\n### C-1: R-1
                re.compile(r'##\s*([A-Za-z]+)\s*Controls\s*\n\n(.*?)(?=##|\Z)', re.DOTALL)
            ]
            
            # Try the specific control entry patterns first
            matched = False
            for pattern_idx, pattern in enumerate(control_patterns[:2]):  # The first two patterns
                matches = list(pattern.finditer(controls_text))
                if matches:
                    matched = True
                    for match in matches:
                        if pattern_idx == 0:  # Format: ### C-123: R-123
                            control_id = match.group(1).strip()
                            risk_id = match.group(2).strip()
                            description = match.group(3).strip()
                            control_type = match.group(4).strip()
                            reference = match.group(5).strip()
                            implementation = match.group(6).strip()
                        else:  # Format: #### C-123: R-123
                            control_id = match.group(1).strip()
                            risk_id = match.group(2).strip()
                            description = match.group(3).strip()
                            implementation = match.group(4).strip()
                            reference = match.group(5).strip()
                            
                            # Try to infer control type from description
                            if "prevent" in description.lower():
                                control_type = "Preventive"
                            elif "detect" in description.lower():
                                control_type = "Detective"
                            elif "correct" in description.lower() or "remediat" in description.lower():
                                control_type = "Corrective"
                            else:
                                control_type = "Preventive"  # Default
                        
                        parsed.append({
                            "id": control_id,
                            "risk_id": risk_id,
                            "description": description,
                            "type": control_type,
                            "implementation": implementation,
                            "reference": reference
                        })
            
            # If no matches found, try the section pattern
            if not matched and not parsed:
                match = control_patterns[2].search(controls_text)
                if match:
                    control_type = match.group(1).strip()
                    section_content = match.group(2)
                    
                    # Find controls within this section
                    control_entry_pattern = re.compile(r'###\s*(C-\d+(?:-\d+)?):\s*(R-\d+)\s*\n\*\*Description\*\*:\s*(.*?)\n\*\*Source\*\*:\s*(.*?)\n\*\*Implementation Considerations\*\*:\s*(.*?)(?:\n\n|\Z)', re.DOTALL)
                    
                    for entry_match in control_entry_pattern.finditer(section_content):
                        control_id = entry_match.group(1).strip()
                        risk_id = entry_match.group(2).strip()
                        description = entry_match.group(3).strip()
                        reference = entry_match.group(4).strip()
                        implementation = entry_match.group(5).strip()
                        
                        parsed.append({
                            "id": control_id,
                            "risk_id": risk_id,
                            "description": description,
                            "type": control_type,
                            "implementation": implementation,
                            "reference": reference
                        })
            
            # Try other parsing approach if nothing found
            if not parsed:
                # Try to parse by sections
                section_pattern = re.compile(r'## ([A-Za-z]+) Controls\s*\n\n(.*?)(?=##|\Z)', re.DOTALL)
                control_pattern = re.compile(r'###\s+(C-\d+(?:-\d+)?):\s+(R-\d+)\s*\n(.*?)(?=###|\Z)', re.DOTALL)
                
                for section_match in section_pattern.finditer(controls_text):
                    control_type = section_match.group(1)
                    section_content = section_match.group(2)
                    
                    for control_match in control_pattern.finditer(section_content):
                        control_id = control_match.group(1).strip()
                        risk_id = control_match.group(2).strip()
                        details = control_match.group(3)
                        
                        # Extract description, implementation, and source
                        desc_match = re.search(r'\*\*Description\*\*:\s*(.*?)(?=\*\*|\Z)', details, re.DOTALL)
                        impl_match = re.search(r'\*\*Implementation Considerations\*\*:\s*(.*?)(?=\*\*|\Z)', details, re.DOTALL)
                        source_match = re.search(r'\*\*Source\*\*:\s*(.*?)(?=\*\*|\Z)', details, re.DOTALL)
                        
                        description = desc_match.group(1).strip() if desc_match else f"Control for {risk_id}"
                        implementation = impl_match.group(1).strip() if impl_match else "Regular monitoring and verification required."
                        reference = source_match.group(1).strip() if source_match else "Unknown"
                        
                        parsed.append({
                            "id": control_id,
                            "risk_id": risk_id,
                            "description": description,
                            "type": control_type,
                            "implementation": implementation,
                            "reference": reference
                        })
        except Exception as e:
            logger.error(f"Error parsing controls: {str(e)}")
            # Return an empty array with at least one default entry
            parsed = [{
                "id": "C-1",
                "risk_id": "R-1",
                "description": "Failed to parse controls. Please check the input format.",
                "type": "Preventive",
                "implementation": "Regular monitoring and verification required.",
                "reference": "Error"
            }]
        
        return parsed
    
    @staticmethod
    def parse_tests(test_procedures_text: str) -> List[Dict[str, Any]]:
        """Parse test procedures into a standardized structure"""
        parsed = []
        
        try:
            # Check if content is very limited
            if len(test_procedures_text.strip()) < 200 or test_procedures_text.count("##") < 3:
                # This is just a placeholder, we need to generate tests
                return []  # Return empty array to trigger fallback tests
            
            # Standard pattern for test entries
            test_pattern = re.compile(r'##\s*(T-\d+(?:-[A-Z])?)\s*:\s*(C-\d+(?:-\d+)?)\s*\n\*\*Objective\*\*:\s*(.*?)\n\*\*Test Steps\*\*:\s*(.*?)\n\*\*Required Evidence\*\*:\s*(.*?)\n\*\*Source\*\*:\s*(.*?)(?:\n\n|\Z)', re.DOTALL)
            
            for match in test_pattern.finditer(test_procedures_text):
                test_id = match.group(1).strip()
                control_id = match.group(2).strip()
                objective = match.group(3).strip()
                steps_text = match.group(4).strip()
                evidence = match.group(5).strip()
                reference = match.group(6).strip()
                
                # Parse steps
                steps = []
                for line in steps_text.split("\n"):
                    line = line.strip()
                    if line and line.startswith('-'):
                        # Remove leading dash and whitespace
                        step = line[1:].strip()
                        steps.append(step)
                    elif line and (line[0].isdigit() or line[0].isalpha()):
                        steps.append(line)
                
                parsed.append({
                    "test_id": test_id,
                    "control_id": control_id,
                    "objective": objective,
                    "steps": steps,
                    "evidence": evidence,
                    "reference": reference
                })
            
            # If no matches, try alternate pattern
            if not parsed:
                section_pattern = re.compile(r'### ([A-Za-z]+) Priority Test Procedures\s*\n\n(.*?)(?=###|\Z)', re.DOTALL)
                test_pattern = re.compile(r'####\s+(T-\d+(?:-[A-Z])?)\s*:\s*(C-\d+(?:-\d+)?)\s*\n\*\*Objective\*\*:\s*(.*?)\n\*\*Test Steps\*\*:\s*(.*?)\n\*\*Required Evidence\*\*:\s*(.*?)\n\*\*Source\*\*:\s*(.*?)(?:\n\n|\Z)', re.DOTALL)
                
                for section_match in section_pattern.finditer(test_procedures_text):
                    priority = section_match.group(1)
                    section_content = section_match.group(2)
                    
                    for test_match in test_pattern.finditer(section_content):
                        test_id = test_match.group(1).strip()
                        control_id = test_match.group(2).strip()
                        objective = test_match.group(3).strip()
                        steps_text = test_match.group(4).strip()
                        evidence = test_match.group(5).strip()
                        reference = test_match.group(6).strip()
                        
                        # Parse steps
                        steps = []
                        for line in steps_text.split("\n"):
                            line = line.strip()
                            if line and line.startswith('-'):
                                # Remove leading dash and whitespace
                                step = line[1:].strip()
                                steps.append(step)
                            elif line and (line[0].isdigit() or line[0].isalpha()):
                                steps.append(line)
                        
                        parsed.append({
                            "test_id": test_id,
                            "control_id": control_id,
                            "objective": objective,
                            "steps": steps,
                            "priority": priority,
                            "evidence": evidence,
                            "reference": reference
                        })
        except Exception as e:
            logger.error(f"Error parsing test procedures: {str(e)}")
            # Return an empty array with at least one default entry
            parsed = [{
                "test_id": "T-1",
                "control_id": "C-1",
                "objective": "Failed to parse test procedures. Please check the input format.",
                "steps": ["Review control documentation", "Test control implementation"],
                "evidence": "Documentation",
                "reference": "Error"
            }]
        
        return parsed
    
    @staticmethod
    def format_controls(controls: List[Dict[str, Any]]) -> str:
        """Standard formatting for controls output"""
        output = "# Control Framework\n\n"
        
        # Group controls by type for better organization
        control_types = {}
        
        for control in controls:
            control_type = control.get('type', 'Preventive')
            
            if control_type not in control_types:
                control_types[control_type] = []
                
            control_types[control_type].append(control)
        
        # Output controls by type
        for control_type, type_controls in control_types.items():
            output += f"## {control_type} Controls\n\n"
            
            for control in type_controls:
                output += f"### {control.get('id', 'Unknown')}: {control.get('risk_id', 'Unknown')}\n"
                output += f"**Description**: {control.get('description', 'No description')}\n"
                output += f"**Type**: {control_type}\n"
                output += f"**Source**: {control.get('reference', 'Unknown')}\n"
                output += f"**Implementation Considerations**: {control.get('implementation', 'Regular monitoring and verification required.')}\n\n"
            
        return output
    
    @staticmethod
    def format_risks(risks: List[Dict[str, Any]]) -> str:
        """Standard formatting for risks output"""
        output = "# Risk Analysis Results\n\n"
        
        # Group risks by priority
        priorities = {
            "High": [],
            "Medium": [],
            "Low": []
        }
        
        for risk in risks:
            priority = risk.get('priority', 'Medium')
            priorities[priority].append(risk)
        
        # Output risks by priority (high to low)
        for priority in ["High", "Medium", "Low"]:
            priority_risks = priorities[priority]
            
            if priority_risks:
                output += f"## {priority} Priority Risks\n\n"
                
                for risk in priority_risks:
                    output += f"### {risk.get('id', 'Unknown')}\n"
                    output += f"**Description**: {risk.get('description', 'No description')}\n"
                    output += f"**Likelihood**: {risk.get('likelihood', 'Medium')}\n"
                    output += f"**Impact**: {risk.get('impact', 'Medium')}\n"
                    output += f"**Source**: {risk.get('reference', 'Unknown')}\n\n"
            
        return output
    
    @staticmethod
    def format_test_procedures(procedures: List[Dict[str, Any]]) -> str:
        """Standard formatting for test procedures output"""
        output = "# Audit Test Procedures\n\n"
        
        # Group tests by priority if available
        if any('priority' in proc for proc in procedures):
            priorities = {
                "High": [],
                "Medium": [],
                "Low": []
            }
            
            for proc in procedures:
                priority = proc.get('priority', 'Medium')
                priorities[priority].append(proc)
            
            # Output tests by priority (high to low)
            for priority in ["High", "Medium", "Low"]:
                priority_tests = priorities[priority]
                
                if priority_tests:
                    output += f"## {priority} Priority Test Procedures\n\n"
                    
                    for proc in priority_tests:
                        output += f"### {proc.get('test_id', 'Unknown')}: {proc.get('control_id', 'Unknown')}\n"
                        output += f"**Objective**: {proc.get('objective', 'Verify control effectiveness')}\n"
                        output += "**Test Steps**:\n"
                        for step in proc.get('steps', ['No steps defined']):
                            output += f"- {step}\n"
                        output += f"**Required Evidence**: {proc.get('evidence', 'Documentation')}\n"
                        output += f"**Source**: {proc.get('reference', 'Unknown')}\n\n"
        else:
            # Output all tests without priority grouping
            for proc in procedures:
                output += f"## {proc.get('test_id', 'Unknown')}: {proc.get('control_id', 'Unknown')}\n"
                output += f"**Objective**: {proc.get('objective', 'Verify control effectiveness')}\n"
                output += "**Test Steps**:\n"
                for step in proc.get('steps', ['No steps defined']):
                    output += f"- {step}\n"
                output += f"**Required Evidence**: {proc.get('evidence', 'Documentation')}\n"
                output += f"**Source**: {proc.get('reference', 'Unknown')}\n\n"
        
        return output