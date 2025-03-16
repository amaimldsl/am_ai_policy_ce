# tools/parser_utils.py
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
            
            # If no matches found, try to extract from unstructured text
            if not parsed:
                # Look for lines with keywords that suggest requirements
                requirement_indicators = ['shall', 'must', 'should', 'required', 'obligated']
                lines = conditions_text.split('\n')
                
                for i, line in enumerate(lines):
                    for indicator in requirement_indicators:
                        if indicator in line.lower():
                            parsed.append({
                                "id": f"C-{len(parsed)+1}",
                                "description": line.strip(),
                                "reference": "Extracted from unstructured text"
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
                # Format: ## R-123: C-456
                re.compile(r'##\s*(R-\d+):\s*(C-\d+)\s*\n', re.DOTALL),
                
                # Format with description and source separate lines
                re.compile(r'##\s*(R-\d+).*?\n\*\*Description\*\*:\s*(.*?)\n\*\*Source\*\*:\s*(.*?)(?:\n|$)', re.DOTALL)
            ]
            
            # Try structured patterns first
            for pattern in risk_patterns:
                matches = list(pattern.finditer(risks_text))
                if matches:
                    for match in matches:
                        risk_id = match.group(1)
                        
                        if len(match.groups()) >= 3:
                            # This pattern has description and source
                            description = match.group(2).strip()
                            reference = match.group(3).strip()
                            # Infer condition ID from risk ID if possible
                            condition_id = f"C-{risk_id.replace('R-', '')}"
                        else:
                            # Pattern only has risk ID and condition ID
                            condition_id = match.group(2)
                            
                            # Look for description after the header
                            desc_match = re.search(rf'{re.escape(risk_id)}.*?\n\*\*Description\*\*:\s*(.*?)\n', risks_text, re.DOTALL)
                            source_match = re.search(rf'{re.escape(risk_id)}.*?\n\*\*Source\*\*:\s*(.*?)(?:\n|$)', risks_text, re.DOTALL)
                            
                            description = desc_match.group(1).strip() if desc_match else ""
                            reference = source_match.group(1).strip() if source_match else ""
                        
                        parsed.append({
                            "id": risk_id,
                            "condition_id": condition_id,
                            "description": description,
                            "reference": reference
                        })
                    break  # Stop if we found matches with this pattern
            
            # If no matches found with the standard pattern, try alternate format
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
                            "reference": "Risk Assessment Document"  # Default reference
                        })
                else:
                    # Last resort - create single entry from whole text
                    parsed.append({
                        "id": "R-Unknown",
                        "condition_id": "C-Unknown",
                        "description": risks_text.strip(),
                        "reference": "Unknown"
                    })
        except Exception as e:
            logger.error(f"Error parsing risks: {str(e)}")
            # Return an empty array with at least one default entry
            parsed = [{
                "id": "R-1",
                "condition_id": "C-1",
                "description": "Failed to parse risks. Please check the input format.",
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
            # Standard pattern for control entries
            control_pattern = re.compile(r'##\s*(C-\d+):\s*(R-\d+)\s*\n\*\*Description\*\*:\s*(.*?)\n\*\*Type\*\*:\s*(.*?)\n\*\*Source\*\*:\s*(.*?)\n', re.DOTALL)
            
            for match in control_pattern.finditer(controls_text):
                control_id = match.group(1)
                risk_id = match.group(2)
                description = match.group(3).strip()
                control_type = match.group(4).strip()
                reference = match.group(5).strip()
                
                parsed.append({
                    "id": control_id,
                    "risk_id": risk_id,
                    "description": description,
                    "type": control_type,
                    "reference": reference
                })
            
            # If no matches found, try to extract from unstructured text
            if not parsed:
                lines = controls_text.split('\n')
                current_control = {}
                
                for line in lines:
                    if line.startswith('##') and ':' in line:
                        # Save previous control if exists
                        if current_control and 'id' in current_control:
                            parsed.append(current_control)
                        
                        # Start new control
                        parts = line.replace('##', '').strip().split(':', 1)
                        ids = parts[0].strip().split(':', 1)
                        
                        if len(ids) > 1:
                            control_id = ids[0].strip()
                            risk_id = ids[1].strip()
                        else:
                            control_id = ids[0].strip()
                            risk_id = f"R-{control_id.replace('C-', '')}"  # Default mapping
                        
                        current_control = {
                            "id": control_id,
                            "risk_id": risk_id,
                            "description": "",
                            "type": "Preventive",  # Default
                            "reference": ""
                        }
                    elif '**Description**:' in line:
                        if current_control:
                            current_control["description"] = line.split(':', 1)[1].strip()
                    elif '**Type**:' in line:
                        if current_control:
                            current_control["type"] = line.split(':', 1)[1].strip()
                    elif '**Source**:' in line:
                        if current_control:
                            current_control["reference"] = line.split(':', 1)[1].strip()
                
                # Add the last control if exists
                if current_control and 'id' in current_control:
                    parsed.append(current_control)
        except Exception as e:
            logger.error(f"Error parsing controls: {str(e)}")
            # Return an empty array with at least one default entry
            parsed = [{
                "id": "C-1",
                "risk_id": "R-1",
                "description": "Failed to parse controls. Please check the input format.",
                "type": "Preventive",
                "reference": "Error"
            }]
        
        return parsed
    
    @staticmethod
    def format_controls(controls: List[Dict[str, Any]]) -> str:
        """Standard formatting for controls output"""
        output = "# Control Framework\n\n"
        
        for control in controls:
            output += f"## {control.get('id', 'Unknown')}: {control.get('risk_id', 'Unknown')}\n"
            output += f"**Description**: {control.get('description', 'No description')}\n"
            output += f"**Type**: {control.get('type', 'Preventive')}\n"
            output += f"**Source**: {control.get('reference', 'Unknown')}\n"
            output += "**Implementation Considerations**: Regular monitoring and verification required.\n"
            output += "\n"
            
        return output
    
    @staticmethod
    def format_risks(risks: List[Dict[str, Any]]) -> str:
        """Standard formatting for risks output"""
        output = "# Risk Analysis Results\n\n"
        
        for risk in risks:
            output += f"## {risk.get('id', 'Unknown')}: {risk.get('condition_id', 'Unknown')}\n"
            output += f"**Description**: {risk.get('description', 'No description')}\n"
            output += f"**Source**: {risk.get('reference', 'Unknown')}\n"
            output += "**Likelihood**: Medium\n"  # Default values
            output += "**Impact**: Medium\n"
            output += "\n"
            
        return output
    
    @staticmethod
    def format_test_procedures(procedures: List[Dict[str, Any]]) -> str:
        """Standard formatting for test procedures output"""
        output = "# Audit Test Procedures\n\n"
        
        for proc in procedures:
            output += f"## {proc.get('test_id', 'Unknown')}: {proc.get('control_id', 'Unknown')}\n"
            output += f"**Objective**: {proc.get('objective', 'Verify control effectiveness')}\n"
            output += "**Test Steps**:\n"
            for step in proc.get('steps', ['No steps defined']):
                output += f"- {step}\n"
            output += f"**Required Evidence**: {proc.get('evidence', 'Documentation')}\n"
            output += f"**Source**: {proc.get('reference', 'Unknown')}\n"
            output += "\n"
            
        return output