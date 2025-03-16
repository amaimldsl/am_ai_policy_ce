# tools/AuditPlanningTool.py
from typing import Optional
from crewai.tools import BaseTool
import re

class AuditPlanningTool(BaseTool):
    name: str = "Audit Planning Tool"
    description: str = "Develops test procedures for verifying control effectiveness."
    
    def _run(self,
             controls: str,
             action: str = "develop",  # develop, format
             methodology: Optional[str] = None,
             **kwargs) -> str:
        
        if action == "develop":
            # Parse the controls
            parsed_controls = self._parse_controls(controls)
            
            # Develop test procedures for each control
            test_procedures = []
            for control in parsed_controls:
                # Generate test ID based on control ID
                test_id = f"T-{control['id'].replace('C-', '')}"
                
                # Design test procedure based on control
                test_objective = f"Verify implementation and effectiveness of {control['id']}"
                test_steps = self._generate_test_steps(control)
                
                # Add to test procedures list
                test_procedures.append({
                    "test_id": test_id,
                    "control_id": control["id"],
                    "objective": test_objective,
                    "steps": test_steps,
                    "evidence": "Documentation, screenshots, system logs",
                    "reference": control.get("reference", "")
                })
            
            # Format the output
            return self._format_test_procedures(test_procedures)
        
        return f"Invalid action: {action}"
    
    def _parse_controls(self, controls_text):
        """Parse the controls text into structured data"""
        parsed = []
        
        # Simple regex-based parsing - adapt to your actual format
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
            
        return parsed
    
    def _generate_test_steps(self, control):
        """Generate appropriate test steps based on control type and description"""
        if control.get("type", "").lower() == "detective":
            return [
                "1. Review detection mechanism documentation",
                "2. Test detection capabilities with sample scenarios",
                "3. Verify alert/notification process",
                "4. Validate response procedures"
            ]
        elif control.get("type", "").lower() == "preventive":
            return [
                "1. Review control implementation documentation",
                "2. Test preventive measure with sample data",
                "3. Attempt to bypass control (negative testing)",
                "4. Verify logging of attempted violations"
            ]
        else:
            return [
                "1. Review control documentation",
                "2. Interview responsible personnel",
                "3. Test control using sample data",
                "4. Verify effectiveness against requirements"
            ]
    
    def _format_test_procedures(self, procedures):
        """Format test procedures as structured text"""
        output = "# Audit Test Procedures\n\n"
        
        for proc in procedures:
            output += f"## {proc['test_id']}: {proc['control_id']}\n"
            output += f"**Objective**: {proc['objective']}\n"
            output += "**Test Steps**:\n"
            for step in proc['steps']:
                output += f"- {step}\n"
            output += f"**Required Evidence**: {proc['evidence']}\n"
            output += f"**Source**: {proc['reference']}\n"
            output += "\n"
            
        return output