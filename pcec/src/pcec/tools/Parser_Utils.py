# tools/Parser_Utils.py - Enhanced version
import re
from typing import List, Dict, Any, Set
import logging
import functools

logger = logging.getLogger(__name__)

class ParserUtils:
    """
    Centralized parsing utilities to standardize data extraction and formatting
    across different tools and eliminate redundancy.
    """
    
    @staticmethod
    def natural_sort_key(s):
        """
        Natural sorting key function that handles numeric parts correctly
        This ensures that C-1, C-2, C-10 sort properly instead of C-1, C-10, C-2
        """
        return [int(text) if text.isdigit() else text.lower() 
                for text in re.split(r'(\d+)', str(s))]
    
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
            
            # Sort the conditions by ID using natural sort
            parsed.sort(key=lambda x: ParserUtils.natural_sort_key(x.get('id', '')))
            
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
            
            # Track condition mapping for many-to-many relationships
            condition_mapping = {}
            
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
                                
                                # Infer condition ID from risk ID or from description
                                condition_ids = []
                                cond_matches = re.findall(r'C-\d+', description)
                                if cond_matches:
                                    condition_ids = cond_matches
                                else:
                                    condition_ids = [f"C-{risk_id.replace('R-', '')}"]
                                
                                # Use the first one as primary but track all
                                condition_id = condition_ids[0] if condition_ids else f"C-{risk_id.replace('R-', '')}"
                                
                                # Store mapping for many-to-many relationship
                                condition_mapping[risk_id] = condition_ids
                        elif len(match.groups()) >= 3 and "Description" in match.group(0) and "Source" in match.group(0):  # Pattern 3
                            risk_id = match.group(1).strip()
                            description = match.group(2).strip()
                            reference = match.group(3).strip()
                            
                            # Set default values for likelihood and impact
                            likelihood = "Medium"
                            impact = "Medium"
                            
                            # Extract condition IDs from description
                            condition_ids = re.findall(r'C-\d+', description)
                            condition_id = condition_ids[0] if condition_ids else f"C-{risk_id.replace('R-', '')}"
                            
                            # Store mapping for many-to-many relationship
                            condition_mapping[risk_id] = condition_ids if condition_ids else [condition_id]
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
                            
                            # Check for additional condition IDs in description
                            additional_conditions = re.findall(r'C-\d+', description)
                            all_conditions = [condition_id]
                            if additional_conditions:
                                all_conditions.extend([c for c in additional_conditions if c != condition_id])
                            
                            # Store mapping for many-to-many relationship
                            condition_mapping[risk_id] = all_conditions
                        
                        # Determine priority based on likelihood and impact
                        priority = "Medium"  # Default
                        if likelihood == "High" and impact == "High":
                            priority = "High"
                        elif likelihood == "Low" and impact == "Low":
                            priority = "Low"
                        
                        parsed.append({
                            "id": risk_id,
                            "condition_id": condition_id,
                            "condition_ids": condition_mapping.get(risk_id, [condition_id]),
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
                        
                        # Extract condition IDs from description
                        condition_ids = re.findall(r'C-\d+', description)
                        if not condition_ids:
                            condition_ids = [f"C-{risk_id.replace('R-', '')}"]
                        
                        condition_id = condition_ids[0]  # Primary condition
                        
                        parsed.append({
                            "id": risk_id,
                            "condition_id": condition_id,
                            "condition_ids": condition_ids,
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
                        condition_id = f"C-{match.group(1)}"
                        description = match.group(2).strip()
                        
                        risk_id = f"R-{match.group(1)}"
                        
                        parsed.append({
                            "id": risk_id,
                            "condition_id": condition_id,
                            "condition_ids": [condition_id],
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
                        "condition_ids": ["C-Unknown"],
                        "description": risks_text.strip(),
                        "likelihood": "Medium",
                        "impact": "Medium",
                        "priority": "Medium",
                        "reference": "Unknown"
                    })
            
            # Sort the risks by ID using natural sort
            parsed.sort(key=lambda x: ParserUtils.natural_sort_key(x.get('id', '')))
            
        except Exception as e:
            logger.error(f"Error parsing risks: {str(e)}")
            # Return an empty array with at least one default entry
            parsed = [{
                "id": "R-1",
                "condition_id": "C-1",
                "condition_ids": ["C-1"],
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
            
            # Track risk mapping for many-to-many relationships
            risk_mapping = {}
            
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
                        
                        # Check for additional risk IDs in description
                        additional_risks = re.findall(r'R-\d+', description)
                        all_risks = [risk_id]
                        if additional_risks:
                            all_risks.extend([r for r in additional_risks if r != risk_id])
                        
                        # Store mapping for many-to-many relationship
                        risk_mapping[control_id] = all_risks
                        
                        parsed.append({
                            "id": control_id,
                            "risk_id": risk_id,
                            "risk_ids": all_risks,
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
                        
                        # Check for additional risk IDs in description
                        additional_risks = re.findall(r'R-\d+', description)
                        all_risks = [risk_id]
                        if additional_risks:
                            all_risks.extend([r for r in additional_risks if r != risk_id])
                        
                        # Store mapping for many-to-many relationship
                        risk_mapping[control_id] = all_risks
                        
                        parsed.append({
                            "id": control_id,
                            "risk_id": risk_id,
                            "risk_ids": all_risks,
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
                        
                        # Check for additional risk IDs in description
                        additional_risks = re.findall(r'R-\d+', description)
                        all_risks = [risk_id]
                        if additional_risks:
                            all_risks.extend([r for r in additional_risks if r != risk_id])
                        
                        # Store mapping for many-to-many relationship
                        risk_mapping[control_id] = all_risks
                        
                        parsed.append({
                            "id": control_id,
                            "risk_id": risk_id,
                            "risk_ids": all_risks,
                            "description": description,
                            "type": control_type,
                            "implementation": implementation,
                            "reference": reference
                        })
            
            # Sort the controls by ID using natural sort
            parsed.sort(key=lambda x: ParserUtils.natural_sort_key(x.get('id', '')))
            
        except Exception as e:
            logger.error(f"Error parsing controls: {str(e)}")
            # Return an empty array with at least one default entry
            parsed = [{
                "id": "C-1",
                "risk_id": "R-1",
                "risk_ids": ["R-1"],
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
            
            # Track control mapping for many-to-many relationships
            control_mapping = {}
            
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
                
                # Check for additional control IDs in objective
                additional_controls = re.findall(r'C-\d+(?:-\d+)?', objective)
                all_controls = [control_id]
                if additional_controls:
                    all_controls.extend([c for c in additional_controls if c != control_id])
                
                # Store mapping for many-to-many relationship
                control_mapping[test_id] = all_controls
                
                parsed.append({
                    "test_id": test_id,
                    "control_id": control_id,
                    "control_ids": all_controls,
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
                        
                        # Check for additional control IDs in objective
                        additional_controls = re.findall(r'C-\d+(?:-\d+)?', objective)
                        all_controls = [control_id]
                        if additional_controls:
                            all_controls.extend([c for c in additional_controls if c != control_id])
                        
                        # Store mapping for many-to-many relationship
                        control_mapping[test_id] = all_controls
                        
                        parsed.append({
                            "test_id": test_id,
                            "control_id": control_id,
                            "control_ids": all_controls,
                            "objective": objective,
                            "steps": steps,
                            "priority": priority,
                            "evidence": evidence,
                            "reference": reference
                        })
            
            # Sort the tests by ID using natural sort
            parsed.sort(key=lambda x: ParserUtils.natural_sort_key(x.get('test_id', '')))
            
        except Exception as e:
            logger.error(f"Error parsing test procedures: {str(e)}")
            # Return an empty array with at least one default entry
            parsed = [{
                "test_id": "T-1",
                "control_id": "C-1",
                "control_ids": ["C-1"],
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
            
            # Sort controls by ID within each type
            sorted_controls = sorted(type_controls, key=lambda x: ParserUtils.natural_sort_key(x.get('id', '')))
            
            for control in sorted_controls:
                # List all risks this control addresses
                risk_ids = control.get('risk_ids', [control.get('risk_id', 'Unknown')])
                risk_text = ', '.join(risk_ids) if len(risk_ids) > 1 else risk_ids[0]
                
                output += f"### {control.get('id', 'Unknown')}: {risk_text}\n"
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
                # Sort risks by ID within each priority level
                sorted_risks = sorted(priority_risks, key=lambda x: ParserUtils.natural_sort_key(x.get('id', '')))
                
                output += f"## {priority} Priority Risks\n\n"
                
                for risk in sorted_risks:
                    # List all conditions this risk addresses
                    condition_ids = risk.get('condition_ids', [risk.get('condition_id', 'Unknown')])
                    condition_text = ', '.join(condition_ids) if len(condition_ids) > 1 else condition_ids[0]
                    
                    output += f"### {risk.get('id', 'Unknown')}\n"
                    output += f"**Related Conditions**: {condition_text}\n"
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
                    # Sort tests by ID within each priority level
                    sorted_tests = sorted(priority_tests, key=lambda x: ParserUtils.natural_sort_key(x.get('test_id', '')))
                    
                    output += f"## {priority} Priority Test Procedures\n\n"
                    
                    for proc in sorted_tests:
                        # List all controls this test addresses
                        control_ids = proc.get('control_ids', [proc.get('control_id', 'Unknown')])
                        control_text = ', '.join(control_ids) if len(control_ids) > 1 else control_ids[0]
                        
                        output += f"### {proc.get('test_id', 'Unknown')}: {control_text}\n"
                        output += f"**Objective**: {proc.get('objective', 'Verify control effectiveness')}\n"
                        output += "**Test Steps**:\n"
                        for step in proc.get('steps', ['No steps defined']):
                            output += f"- {step}\n"
                        output += f"**Required Evidence**: {proc.get('evidence', 'Documentation')}\n"
                        output += f"**Source**: {proc.get('reference', 'Unknown')}\n\n"
        else:
            # Output all tests without priority grouping, sorted by ID
            sorted_tests = sorted(procedures, key=lambda x: ParserUtils.natural_sort_key(x.get('test_id', '')))
            
            for proc in sorted_tests:
                # List all controls this test addresses
                control_ids = proc.get('control_ids', [proc.get('control_id', 'Unknown')])
                control_text = ', '.join(control_ids) if len(control_ids) > 1 else control_ids[0]
                
                output += f"## {proc.get('test_id', 'Unknown')}: {control_text}\n"
                output += f"**Objective**: {proc.get('objective', 'Verify control effectiveness')}\n"
                output += "**Test Steps**:\n"
                for step in proc.get('steps', ['No steps defined']):
                    output += f"- {step}\n"
                output += f"**Required Evidence**: {proc.get('evidence', 'Documentation')}\n"
                output += f"**Source**: {proc.get('reference', 'Unknown')}\n\n"
        
        return output
    
    @staticmethod
    def create_relationship_matrix(conditions: List[Dict[str, Any]], 
                                  risks: List[Dict[str, Any]],
                                  controls: List[Dict[str, Any]],
                                  tests: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Create a comprehensive relationship matrix showing the mapping between 
        conditions, risks, controls and tests with full many-to-many relationships.
        """
        # Create mappings for faster lookups
        condition_map = {c.get('id', ''): c for c in conditions}
        risk_map = {r.get('id', ''): r for r in risks}
        control_map = {c.get('id', ''): c for c in controls}
        test_map = {t.get('test_id', ''): t for t in tests}
        
        # Track all relationships
        relationships = {}
        
        # Process conditions first
        for condition in conditions:
            condition_id = condition.get('id', '')
            if condition_id:
                relationships[condition_id] = []
        
        # Process risks and link to conditions
        for risk in risks:
            risk_id = risk.get('id', '')
            if not risk_id:
                continue
                
            # Find all related conditions
            condition_ids = risk.get('condition_ids', [risk.get('condition_id', '')])
            
            # For each condition this risk relates to
            for condition_id in condition_ids:
                if condition_id in relationships:
                    # Add risk to the condition's relationships
                    relationships[condition_id].append({
                        'risk_id': risk_id,
                        'description': risk.get('description', ''),
                        'priority': risk.get('priority', 'Medium')
                    })
        
        # Process controls and link to risks
        for control in controls:
            control_id = control.get('id', '')
            if not control_id:
                continue
                
            # Find all related risks
            risk_ids = control.get('risk_ids', [control.get('risk_id', '')])
            
            # For each risk this control relates to
            for risk_id in risk_ids:
                # Find all conditions related to this risk
                for condition_id, rels in relationships.items():
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
        
        # Process tests and link to controls
        for test in tests:
            test_id = test.get('test_id', '')
            if not test_id:
                continue
                
            # Find all related controls
            control_ids = test.get('control_ids', [test.get('control_id', '')])
            
            # For each control this test relates to
            for control_id in control_ids:
                # Find all relationships containing this control
                for condition_id, rels in relationships.items():
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
        
        return relationships
    
    @staticmethod
    def generate_traceability_table(relationships: Dict[str, List[Dict[str, Any]]]) -> str:
        """Generate a traceability table from relationship data"""
        rows = []
        
        # Process all relationships into flattened rows for the table
        for condition_id, rels in relationships.items():
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
            ParserUtils.natural_sort_key(x['condition_id']),
            ParserUtils.natural_sort_key(x['risk_id']),
            ParserUtils.natural_sort_key(x['control_id']),
            ParserUtils.natural_sort_key(x['test_id'])
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