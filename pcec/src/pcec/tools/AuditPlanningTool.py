# tools/AuditPlanningTool.py - Enhanced version
from typing import Optional, List, Dict, Any
from crewai.tools import BaseTool
import logging
import re
from tools.Parser_Utils import ParserUtils

logger = logging.getLogger(__name__)

class AuditPlanningTool(BaseTool):
    name: str = "Audit Planning Tool"
    description: str = "Develops test procedures for verifying control effectiveness."
    
    def _run(self,
             controls: str,
             action: str = "develop",  # develop, format, prioritize
             methodology: Optional[str] = None,
             **kwargs) -> str:
        try:
            if action == "develop":
                # Parse the controls using centralized parser
                parsed_controls = ParserUtils.parse_controls(controls)
                
                # Develop test procedures for each control
                test_procedures = self._develop_test_procedures(parsed_controls, methodology)
                
                # Format using standard formatter
                return ParserUtils.format_test_procedures(test_procedures)
                
            elif action == "format":
                return self._format_audit_program(controls)
                
            elif action == "prioritize":
                return self._prioritize_tests(controls)
                
            return f"Invalid action: {action}. Supported actions: develop, format, prioritize."
            
        except Exception as e:
            logger.error(f"Error in AuditPlanningTool: {str(e)}", exc_info=True)
            return f"Error developing test procedures: {str(e)}"
    
    def _develop_test_procedures(self, controls: List[Dict[str, Any]], methodology: Optional[str]) -> List[Dict[str, Any]]:
        """Develop test procedures for each control"""
        test_procedures = []
        
        # Different methodologies can have different testing approaches
        testing_approaches = {
            "Risk-based": self._generate_risk_based_steps,
            "Compliance": self._generate_compliance_steps,
            "Substantive": self._generate_substantive_steps,
            "Default": self._generate_default_steps
        }
        
        # Select testing approach based on methodology
        selected_approach = testing_approaches.get(methodology, testing_approaches["Default"])
        
        for control in controls:
            # Generate test ID based on control ID
            control_id = control.get('id', '')
            test_id = f"T-{control_id.replace('C-', '')}"
            
            # Design test procedure based on control
            test_objective = f"Verify implementation and effectiveness of {control_id}"
            
            # Generate test steps based on control type and selected approach
            control_type = control.get('type', 'Preventive')
            control_desc = control.get('description', '')
            test_steps = selected_approach(control_type, control_desc)
            
            # Determine appropriate evidence requirements
            evidence = self._determine_evidence_requirements(control_type, control_desc)
            
            # Add to test procedures list
            test_procedures.append({
                "test_id": test_id,
                "control_id": control_id,
                "objective": test_objective,
                "steps": test_steps,
                "evidence": evidence,
                "reference": control.get("reference", "")
            })
        
        return test_procedures
    
    def _generate_default_steps(self, control_type: str, control_desc: str) -> List[str]:
        """Generate appropriate test steps based on control type and description"""
        if control_type.lower() == "detective":
            return [
                "1. Review detection mechanism documentation",
                "2. Test detection capabilities with sample scenarios",
                "3. Verify alert/notification process",
                "4. Validate response procedures"
            ]
        elif control_type.lower() == "preventive":
            return [
                "1. Review control implementation documentation",
                "2. Test preventive measure with sample data",
                "3. Attempt to bypass control (negative testing)",
                "4. Verify logging of attempted violations"
            ]
        elif control_type.lower() == "corrective":
            return [
                "1. Review correction procedures documentation",
                "2. Validate correction workflow with sample scenarios",
                "3. Verify timeliness of corrective actions",
                "4. Confirm documentation of corrections"
            ]
        else:
            return [
                "1. Review control documentation",
                "2. Interview responsible personnel",
                "3. Test control using sample data",
                "4. Verify effectiveness against requirements"
            ]
    
    def _generate_risk_based_steps(self, control_type: str, control_desc: str) -> List[str]:
        """Generate risk-based testing steps"""
        base_steps = [
            "1. Identify key risk scenarios related to the control",
            "2. Develop test cases for each risk scenario"
        ]
        
        if control_type.lower() == "detective":
            base_steps.extend([
                "3. Execute test cases to validate detection capabilities",
                "4. Evaluate detection effectiveness for each risk scenario",
                "5. Assess response procedures for detected issues"
            ])
        elif control_type.lower() == "preventive":
            base_steps.extend([
                "3. Execute test cases to attempt to bypass preventive measures",
                "4. Evaluate prevention effectiveness for each risk scenario",
                "5. Assess logging and monitoring of prevention failures"
            ])
        else:
            base_steps.extend([
                "3. Execute test cases to validate control effectiveness",
                "4. Evaluate control performance for each risk scenario",
                "5. Assess overall risk mitigation provided by the control"
            ])
        
        return base_steps
    
    def _generate_compliance_steps(self, control_type: str, control_desc: str) -> List[str]:
        """Generate compliance-focused testing steps"""
        return [
            "1. Review regulatory/policy requirements addressed by the control",
            "2. Verify control design meets compliance requirements",
            "3. Test control implementation against compliance criteria",
            "4. Sample transactions/activities to verify consistent application",
            "5. Document compliance evidence for regulatory reporting"
        ]
    
    def _generate_substantive_steps(self, control_type: str, control_desc: str) -> List[str]:
        """Generate substantive testing steps"""
        return [
            "1. Define population of items subject to the control",
            "2. Select statistically valid sample from population",
            "3. For each sample item, perform detailed testing of control application",
            "4. Document exceptions and deviations",
            "5. Evaluate statistical significance of findings"
        ]
    
    def _determine_evidence_requirements(self, control_type: str, control_desc: str) -> str:
        """Determine appropriate evidence requirements based on control type"""
        evidence_items = ["Documentation"]
        
        # Add evidence types based on control type
        if control_type.lower() == "technical" or "system" in control_desc.lower():
            evidence_items.extend(["System logs", "Configuration screenshots", "Access records"])
        
        if control_type.lower() == "detective" or "monitor" in control_desc.lower():
            evidence_items.extend(["Alert records", "Monitoring reports", "Incident documentation"])
        
        if control_type.lower() == "administrative" or "policy" in control_desc.lower():
            evidence_items.extend(["Policy documents", "Training records", "Signed acknowledgements"])
        
        if control_type.lower() == "physical":
            evidence_items.extend(["Physical inspection records", "Access logs", "Photographs"])
        
        # Add general evidence types
        evidence_items.append("Interview notes")
        
        return ", ".join(evidence_items)
    
    def _format_audit_program(self, test_procedures_text: str) -> str:
        """Format audit program in a structured way"""
        try:
            # Extract test procedures using regex
            import re
            
            test_pattern = re.compile(r'##\s*(T-\d+):\s*(C-\d+)\s*\n\*\*Objective\*\*:\s*(.*?)\n\*\*Test Steps\*\*:\s*(.*?)\n\*\*Required Evidence\*\*:\s*(.*?)\n\*\*Source\*\*:\s*(.*?)(?:\n\n|\Z)', re.DOTALL)
            
            matches = test_pattern.findall(test_procedures_text)
            
            if not matches:
                return "Unable to parse test procedures. Please check the format."
            
            # Create formatted audit program
            output = "# Comprehensive Audit Program\n\n"
            output += "## Program Overview\n"
            output += f"This audit program consists of {len(matches)} test procedures designed to verify the effectiveness of controls.\n\n"
            
            output += "## Test Procedures Summary\n"
            for i, (test_id, control_id, objective, _, _, _) in enumerate(matches, 1):
                output += f"{i}. {test_id}: {objective}\n"
            
            output += "\n## Detailed Test Procedures\n\n"
            
            for test_id, control_id, objective, steps, evidence, source in matches:
                output += f"### {test_id}: {control_id}\n"
                output += f"**Objective**: {objective}\n"
                output += "**Test Steps**:\n"
                
                # Parse steps from the bullet points
                step_lines = steps.strip().split('\n')
                for step in step_lines:
                    if step.strip().startswith('-'):
                        output += f"{step}\n"
                    else:
                        output += f"- {step.strip()}\n"
                
                output += f"**Required Evidence**: {evidence}\n"
                output += f"**Source**: {source}\n\n"
            
            return output
            
        except Exception as e:
            logger.error(f"Error formatting audit program: {str(e)}", exc_info=True)
            return f"Error formatting audit program: {str(e)}"
    
    def _prioritize_tests(self, test_procedures_text: str) -> str:
        """Prioritize test procedures based on risk factors"""
        try:
            # Extract test procedures using regex
            import re
            
            test_pattern = re.compile(r'##\s*(T-\d+):\s*(C-\d+)\s*\n\*\*Objective\*\*:\s*(.*?)\n\*\*Test Steps\*\*:\s*(.*?)\n\*\*Required Evidence\*\*:\s*(.*?)\n\*\*Source\*\*:\s*(.*?)(?:\n\n|\Z)', re.DOTALL)
            
            matches = test_pattern.findall(test_procedures_text)
            
            if not matches:
                return "Unable to parse test procedures. Please check the format."
            
            # Assess priority for each test
            prioritized_tests = []
            
            for test_id, control_id, objective, steps, evidence, source in matches:
                # Count steps as a complexity factor
                step_count = len([s for s in steps.split('\n') if s.strip()])
                
                # Assess priority based on keywords in objective
                priority = "Medium"  # Default
                priority_score = 2
                
                high_priority_keywords = ["critical", "high risk", "security", "compliance", "regulatory", "key"]
                low_priority_keywords = ["ancillary", "supplementary", "additional", "optional"]
                
                if any(keyword in objective.lower() for keyword in high_priority_keywords):
                    priority = "High"
                    priority_score = 3
                elif any(keyword in objective.lower() for keyword in low_priority_keywords):
                    priority = "Low"
                    priority_score = 1
                
                # Adjust priority based on step complexity
                if step_count > 5 and priority != "High":
                    priority = "High"
                    priority_score = 3
                elif step_count < 3 and priority != "Low":
                    priority = "Low"
                    priority_score = 1
                
                prioritized_tests.append({
                    "test_id": test_id,
                    "control_id": control_id,
                    "objective": objective,
                    "steps": steps,
                    "evidence": evidence,
                    "source": source,
                    "priority": priority,
                    "priority_score": priority_score
                })
            
            # Sort by priority score (highest first)
            prioritized_tests.sort(key=lambda x: x["priority_score"], reverse=True)
            
            # Format the output
            output = "# Prioritized Audit Program\n\n"
            
            # Group by priority
            for priority_level in ["High", "Medium", "Low"]:
                priority_tests = [t for t in prioritized_tests if t["priority"] == priority_level]
                
                if priority_tests:
                    output += f"## {priority_level} Priority Tests\n\n"
                    
                    for test in priority_tests:
                        output += f"### {test['test_id']}: {test['control_id']}\n"
                        output += f"**Objective**: {test['objective']}\n"
                        output += f"**Priority**: {test['priority']}\n"
                        output += "**Test Steps**:\n"
                        
                        # Parse steps from the bullet points
                        step_lines = test['steps'].strip().split('\n')
                        for step in step_lines:
                            if step.strip().startswith('-'):
                                output += f"{step}\n"
                            else:
                                output += f"- {step.strip()}\n"
                        
                        output += f"**Required Evidence**: {test['evidence']}\n"
                        output += f"**Source**: {test['source']}\n\n"
            
            return output
            
        except Exception as e:
            logger.error(f"Error prioritizing test procedures: {str(e)}", exc_info=True)
            return f"Error prioritizing test procedures: {str(e)}"