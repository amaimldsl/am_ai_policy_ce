# tools/ControlDesignTool.py - Enhanced version
from typing import Optional, List, Dict, Any
from crewai.tools import BaseTool
import logging
import re
from tools.Parser_Utils import ParserUtils

logger = logging.getLogger(__name__)

class ControlDesignTool(BaseTool):
    name: str = "Control Design Tool"
    description: str = "Designs controls for mitigating identified risks."
    
    def _run(self,
             risks: str,
             action: str = "design",  # design, categorize, evaluate
             framework: Optional[str] = None,
             **kwargs) -> str:
        try:
            if action == "design":
                # Parse the risks using centralized parser
                parsed_risks = ParserUtils.parse_risks(risks)
                
                # Design controls for each risk
                controls = self._design_controls(parsed_risks, framework)
                
                # Format using standard formatter
                return ParserUtils.format_controls(controls)
                
            elif action == "categorize":
                return self._categorize_controls(risks)
                
            elif action == "evaluate":
                return self._evaluate_controls(risks)
                
            return f"Invalid action: {action}. Supported actions: design, categorize, evaluate."
            
        except Exception as e:
            logger.error(f"Error in ControlDesignTool: {str(e)}", exc_info=True)
            return f"Error designing controls: {str(e)}"
    
    def _determine_control_type(self, risk_description: str, available_types: List[str]) -> str:
        """Determine the most appropriate control type based on risk description"""
        # Default to the first available type
        default_type = available_types[0] if available_types else "Preventive"
        
        # Check for keywords that suggest specific control types
        if "detect" in risk_description.lower() and "Detective" in available_types:
            return "Detective"
        elif "prevent" in risk_description.lower() and "Preventive" in available_types:
            return "Preventive"
        elif "correct" in risk_description.lower() and "Corrective" in available_types:
            return "Corrective"
        elif "technical" in risk_description.lower() and "Technical" in available_types:
            return "Technical"
        elif "physical" in risk_description.lower() and "Physical" in available_types:
            return "Physical"
        elif "compensat" in risk_description.lower() and "Compensating" in available_types:
            return "Compensating"
        
        return default_type
    
    def _generate_control_description(self, risk_description: str, control_type: str) -> str:
        """Generate a control description based on risk and control type"""
        # Extract key elements from risk description
        import re
        
        # Try to identify key requirements from risk description
        requirement_match = re.search(r'compliance with (.+?)(?:$|\.)', risk_description)
        requirement = requirement_match.group(1) if requirement_match else "requirements"
        
        # Generate appropriate description based on control type
        if control_type == "Preventive":
            return f"Implement preventive measures to ensure {requirement} prior to processing or execution."
        elif control_type == "Detective":
            return f"Establish monitoring system to detect non-compliance with {requirement} during operation."
        elif control_type == "Corrective":
            return f"Develop remediation procedures to address instances of non-compliance with {requirement}."
        elif control_type == "Compensating":
            return f"Implement alternative controls to achieve equivalent protection when direct compliance with {requirement} is not feasible."
        elif control_type == "Technical":
            return f"Deploy technical safeguards to enforce compliance with {requirement}."
        elif control_type == "Physical":
            return f"Establish physical barriers and safeguards to ensure {requirement}."
        elif control_type == "Administrative":
            return f"Develop policies and procedures to govern compliance with {requirement}."
        
        # Default generic description
        return f"Implement controls to ensure compliance with {requirement}."
    
    def _generate_implementation_guidance(self, control_type: str, risk_description: str) -> str:
        """Generate implementation guidance based on control type"""
        if control_type == "Preventive":
            return "Implement upfront verification steps, automatic validations, and input constraints."
        elif control_type == "Detective":
            return "Establish monitoring, logging, reviews, and periodic compliance audits."
        elif control_type == "Corrective":
            return "Develop incident response procedures, remediation plans, and correction workflows."
        elif control_type == "Technical":
            return "Deploy automated systems, software controls, and technical safeguards."
        elif control_type == "Physical":
            return "Implement physical barriers, access controls, and environmental protections."
        elif control_type == "Administrative":
            return "Establish policies, procedures, training, and documentation."
        
        return "Regular monitoring and verification required."
    
    def _design_controls(self, risks: List[Dict[str, Any]], framework: Optional[str]) -> List[Dict[str, Any]]:
        """Design controls for each risk"""
        controls = []
        
        # Use different control frameworks based on specified framework
        control_types = {
            "NIST": ["Preventive", "Detective", "Corrective", "Compensating"],
            "ISO27001": ["Administrative", "Technical", "Physical"],
            "Default": ["Preventive", "Detective", "Corrective"]
        }
        
        # Select framework control types
        selected_framework = framework if framework in control_types else "Default"
        available_types = control_types[selected_framework]
        
        for risk in risks:
            # Generate control ID based on risk ID
            risk_id = risk.get('id', '')
            # Handle cases where ID might not be in expected format
            if risk_id.startswith('R-'):
                control_id = f"C-{risk_id.replace('R-', '')}"
            else:
                # Try to extract numeric part or use a counter
                import re
                num_match = re.search(r'\d+', risk_id)
                if num_match:
                    control_id = f"C-{num_match.group(0)}"
                else:
                    control_id = f"C-{len(controls)+1}"
            
            # Get the risk description and condition ID
            risk_desc = risk.get('description', '')
            condition_id = risk.get('condition_id', 'Unknown')
            
            # Determine appropriate control type based on risk content
            control_type = self._determine_control_type(risk_desc, available_types)
            
            # Design specific control based on the risk and control type
            control_desc = self._generate_control_description(risk_desc, control_type)
            
            # Add implementation considerations based on control type
            implementation = self._generate_implementation_guidance(control_type, risk_desc)
            
            # Add to controls list
            controls.append({
                "id": control_id,
                "risk_id": risk["id"],
                "description": control_desc,
                "type": control_type,
                "implementation": implementation,
                "reference": risk.get("reference", "")
            })
        
        return controls
    
    def _categorize_controls(self, controls_text: str) -> str:
        """Categorize controls by type"""
        try:
            parsed_controls = ParserUtils.parse_controls(controls_text)
            
            # Group controls by type
            categories = {}
            for control in parsed_controls:
                control_type = control.get('type', 'Undefined')
                
                if control_type not in categories:
                    categories[control_type] = []
                    
                categories[control_type].append(control)
            
            # Format the output
            output = "# Controls Categorized by Type\n\n"
            
            for category, controls in categories.items():
                output += f"## {category} Controls\n"
                
                for control in controls:
                    output += f"- {control.get('id', 'Unknown')}: {control.get('description', 'No description')}\n"
                
                output += "\n"
                
            return output
            
        except Exception as e:
            logger.error(f"Error categorizing controls: {str(e)}", exc_info=True)
            return f"Error categorizing controls: {str(e)}"
    
    def _evaluate_controls(self, controls_text: str) -> str:
        """Evaluate controls for completeness and effectiveness"""
        try:
            parsed_controls = ParserUtils.parse_controls(controls_text)
            
            evaluation_results = []
            
            for control in parsed_controls:
                control_id = control.get('id', 'Unknown')
                description = control.get('description', '')
                control_type = control.get('type', 'Unknown')
                
                # Evaluate description completeness
                description_score = len(description) / 50  # Simple heuristic
                description_score = min(5, description_score)  # Cap at 5
                
                # Evaluate specificity
                specificity_score = 3  # Default medium
                if len(description.split()) > 15:
                    specificity_score = 4
                if len(description.split()) > 30:
                    specificity_score = 5
                
                # Evaluate implementation guidance
                implementation = control.get('implementation', '')
                implementation_score = 2  # Default low
                if implementation and len(implementation) > 20:
                    implementation_score = 4
                if implementation and len(implementation) > 50:
                    implementation_score = 5
                
                # Calculate overall score
                overall_score = (description_score + specificity_score + implementation_score) / 3
                
                # Determine rating
                if overall_score >= 4.5:
                    rating = "Excellent"
                elif overall_score >= 3.5:
                    rating = "Good"
                elif overall_score >= 2.5:
                    rating = "Adequate"
                else:
                    rating = "Needs Improvement"
                
                evaluation_results.append({
                    "control_id": control_id,
                    "description_score": description_score,
                    "specificity_score": specificity_score,
                    "implementation_score": implementation_score,
                    "overall_score": overall_score,
                    "rating": rating
                })
            
            # Format the evaluation results
            output = "# Control Evaluation Results\n\n"
            
            for result in evaluation_results:
                output += f"## {result['control_id']}\n"
                output += f"**Description Score**: {result['description_score']:.1f}/5\n"
                output += f"**Specificity Score**: {result['specificity_score']}/5\n"
                output += f"**Implementation Score**: {result['implementation_score']}/5\n"
                output += f"**Overall Score**: {result['overall_score']:.1f}/5\n"
                output += f"**Rating**: {result['rating']}\n\n"
            
            return output
            
        except Exception as e:
            logger.error(f"Error evaluating controls: {str(e)}", exc_info=True)
            return f"Error evaluating controls: {str(e)}"