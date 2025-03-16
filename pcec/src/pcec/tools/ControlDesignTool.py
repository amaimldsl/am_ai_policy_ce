# tools/ControlDesignTool.py
from typing import Optional
from crewai.tools import BaseTool
import re

class ControlDesignTool(BaseTool):
    name: str = "Control Design Tool"
    description: str = "Designs controls for mitigating identified risks."
    
    def _run(self,
             risks: str,
             action: str = "design",  # design, categorize
             framework: Optional[str] = None,
             **kwargs) -> str:
        
        if action == "design":
            # Parse the risks list
            parsed_risks = self._parse_risks(risks)
            
            # Design controls for each risk
            controls = []
            for risk in parsed_risks:
                # Generate control ID based on risk ID
                control_id = f"C-{risk['id'].replace('R-', '')}"
                
                # Design control based on risk
                control_desc = f"Control to mitigate {risk['id']}: Regular verification of compliance with {risk.get('condition_id', '')}"
                
                # Add to controls list
                controls.append({
                    "control_id": control_id,
                    "risk_id": risk["id"],
                    "description": control_desc,
                    "type": self._determine_control_type(risk.get("description", "")),
                    "reference": risk.get("reference", "")
                })
            
            # Format the output
            return self._format_controls(controls)
        
        return f"Invalid action: {action}"
    
    def _parse_risks(self, risks_text):
        """Parse the risks text into structured data"""
        parsed = []
        
        # Simple regex-based parsing - adapt to your actual format
        risk_pattern = re.compile(r'##\s*(R-\d+):\s*(C-\d+)\s*\n\*\*Description\*\*:\s*(.*?)\n\*\*Source\*\*:\s*(.*?)\n', re.DOTALL)
        
        for match in risk_pattern.finditer(risks_text):
            risk_id = match.group(1)
            condition_id = match.group(2)
            description = match.group(3).strip()
            reference = match.group(4).strip()
            
            parsed.append({
                "id": risk_id,
                "condition_id": condition_id,
                "description": description,
                "reference": reference
            })
            
        return parsed
    
    def _determine_control_type(self, risk_description):
        """Determine the most appropriate control type"""
        if "detect" in risk_description.lower():
            return "Detective"
        elif "prevent" in risk_description.lower():
            return "Preventive"
        else:
            return "Preventive"  # Default
    
    def _format_controls(self, controls):
        """Format controls as structured text"""
        output = "# Control Framework\n\n"
        
        for control in controls:
            output += f"## {control['control_id']}: {control['risk_id']}\n"
            output += f"**Description**: {control['description']}\n"
            output += f"**Type**: {control['type']}\n"
            output += f"**Source**: {control['reference']}\n"
            output += "**Implementation Considerations**: Regular monitoring and verification required.\n"
            output += "\n"
            
        return output