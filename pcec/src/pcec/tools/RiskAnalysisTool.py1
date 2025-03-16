# tools/RiskAnalysisTool.py
from typing import Optional
from crewai.tools import BaseTool
import re

class RiskAnalysisTool(BaseTool):
    name: str = "Risk Analysis Tool"
    description: str = "Analyzes compliance conditions to identify and categorize risks."
    
    def _run(self, 
             conditions: str,
             action: str = "analyze",  # analyze, categorize, prioritize
             criteria: Optional[str] = None,
             **kwargs) -> str:
        
        if action == "analyze":
            # Parse the conditions list
            parsed_conditions = self._parse_conditions(conditions)
            
            # Analyze risks for each condition
            risk_analysis = []
            for condition in parsed_conditions:
                # Generate risk ID based on condition ID
                risk_id = f"R-{condition['id'].replace('C-', '')}"
                
                # Generate risk description
                risk_desc = f"Risk of non-compliance with {condition['id']}: {condition['description']}"
                
                # Add to analysis results
                risk_analysis.append({
                    "risk_id": risk_id,
                    "condition_id": condition["id"],
                    "description": risk_desc,
                    "reference": condition.get("reference", "")
                })
            
            # Format the output
            return self._format_risk_analysis(risk_analysis)
            
        elif action == "categorize":
            # Logic for categorizing risks
            return "Risk categorization functionality"
            
        elif action == "prioritize":
            # Logic for prioritizing risks
            return "Risk prioritization functionality"
            
        return f"Invalid action: {action}"
    
    def _parse_conditions(self, conditions_text):
        """Parse the conditions text into structured data"""
        parsed = []
        
        # Simple regex-based parsing - adapt to your actual format
        condition_pattern = re.compile(r'(C-\d+):\s*(.*?)(?:\s*\[([^]]+)\])?$', re.MULTILINE)
        
        for match in condition_pattern.finditer(conditions_text):
            condition_id = match.group(1)
            description = match.group(2).strip()
            reference = match.group(3) if match.group(3) else ""
            
            parsed.append({
                "id": condition_id,
                "description": description,
                "reference": reference
            })
            
        return parsed
    
    def _format_risk_analysis(self, risk_analysis):
        """Format risk analysis results as structured text"""
        output = "# Risk Analysis Results\n\n"
        
        for risk in risk_analysis:
            output += f"## {risk['risk_id']}: {risk['condition_id']}\n"
            output += f"**Description**: {risk['description']}\n"
            output += f"**Source**: {risk['reference']}\n"
            output += "**Likelihood**: Medium\n"  # Default values
            output += "**Impact**: Medium\n"
            output += "\n"
            
        return output