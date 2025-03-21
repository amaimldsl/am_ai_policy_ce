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
    
    def _verify_test_procedure_completeness(self, procedures: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Verify and enhance test procedures to ensure descriptions and steps are complete.
        
        Args:
            procedures (List[Dict[str, Any]]): The list of test procedure dictionaries
            
        Returns:
            List[Dict[str, Any]]: The enhanced procedures with complete descriptions
        """
        
        
        for procedure in procedures:
            # Check and enhance the objective
            objective = procedure.get('objective', '')
            if objective and not any(objective.endswith(c) for c in ['.', '!', '?']):
                procedure['objective'] = ParserUtils.complete_truncated_sentence(objective)
            
            # Check and enhance each step
            steps = procedure.get('steps', [])
            for i, step in enumerate(steps):
                step_text = step.strip()
                
                # Remove step numbers if present for processing
                step_match = re.match(r'^(\d+\.\s*)(.*)', step_text)
                if step_match:
                    step_num = step_match.group(1)
                    step_content = step_match.group(2)
                    
                    # Check if the step content is incomplete
                    if not any(step_content.endswith(c) for c in ['.', '!', '?']):
                        steps[i] = step_num + ParserUtils.complete_truncated_sentence(step_content)
                # Handle steps without numbers
                elif not any(step_text.endswith(c) for c in ['.', '!', '?']):
                    steps[i] = ParserUtils.complete_truncated_sentence(step_text)
            
            # Check and enhance evidence requirements
            evidence = procedure.get('evidence', '')
            if evidence and not evidence.endswith('.'):
                procedure['evidence'] = evidence + '.'
        
        return procedures
    
    
    
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
        """Develop test procedures for each control - ENHANCED VERSION"""
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
        
        # Track control types to ensure coverage of all control aspects
        control_types_covered = {}
        
        for control in controls:
            # Generate test ID based on control ID
            control_id = control.get('id', '')
            
            # Handle cases where ID might not be in expected format
            if '-' in control_id:
                base_id = control_id.split('-')[0].replace('C-', '')
                test_id = f"T-{base_id}"
                
                # Add suffix if we've already created a test for this base ID
                if test_id in control_types_covered:
                    control_types_covered[test_id] += 1
                    test_id = f"{test_id}.{control_types_covered[test_id]}"
                else:
                    control_types_covered[test_id] = 1
            else:
                test_id = f"T-{control_id.replace('C-', '')}"
            
            # Get control details
            control_type = control.get('type', 'Preventive')
            control_desc = control.get('description', '')
            
            # Generate a more specific test objective based on the control
            test_objective = self._generate_specific_test_objective(control_id, control_type, control_desc)
            
            # Generate test steps based on control type and selected approach
            test_steps = selected_approach(control_type, control_desc)
            
            # Add control-specific test steps
            additional_steps = self._generate_control_specific_steps(control_desc, control_type)
            if additional_steps:
                test_steps.extend(additional_steps)
            
            # Determine appropriate evidence requirements
            evidence = self._determine_comprehensive_evidence(control_type, control_desc)
            
            # Add to test procedures list
            test_procedures.append({
                "test_id": test_id,
                "control_id": control_id,
                "objective": test_objective,
                "steps": test_steps,
                "evidence": evidence,
                "reference": control.get("reference", "")
            })
            
            # For complex controls, add a secondary test procedure focusing on another aspect
            if len(control_desc) > 100 or 'and' in control_desc.lower() or ';' in control_desc:
                secondary_aspect = self._identify_secondary_aspect(control_desc)
                if secondary_aspect:
                    secondary_test_id = f"{test_id}-B"
                    secondary_objective = f"Verify specific aspect of {control_id}: {secondary_aspect}"
                    secondary_steps = self._generate_focused_test_steps(secondary_aspect, control_type)
                    
                    test_procedures.append({
                        "test_id": secondary_test_id,
                        "control_id": control_id,
                        "objective": secondary_objective,
                        "steps": secondary_steps,
                        "evidence": evidence,
                        "reference": control.get("reference", "")
                    })
        
        test_procedures = self._verify_test_procedure_completeness(test_procedures)
        
        return test_procedures
    
    def _generate_specific_test_objective(self, control_id: str, control_type: str, control_desc: str) -> str:
        """Generate a more specific test objective based on control details"""
        # Extract the key objectives from the control description
        key_objective = control_desc[:100] + ('...' if len(control_desc) > 100 else '')
        
        if control_type == "Preventive":
            return f"Verify that preventive control {control_id} effectively prevents non-compliance by validating that {key_objective}"
        elif control_type == "Detective":
            return f"Verify that detective control {control_id} effectively identifies non-compliance by confirming that {key_objective}"
        elif control_type == "Corrective":
            return f"Verify that corrective control {control_id} effectively resolves non-compliance by ensuring that {key_objective}"
        else:
            return f"Verify implementation and effectiveness of control {control_id} by testing that {key_objective}"

    def _identify_secondary_aspect(self, control_desc: str) -> str:
        """Identify a secondary aspect of a control to test separately"""
        # Check for multiple requirements separated by conjunctions or punctuation
        segments = re.split(r'(?:and|or|;|,\s*but|,\s*as well as)', control_desc, 1)
        
        if len(segments) > 1:
            return segments[1].strip()
        
        # Check for different components that might be tested separately
        if 'monitor' in control_desc.lower() and 'report' in control_desc.lower():
            return "reporting capabilities and accuracy"
        elif 'verify' in control_desc.lower() and 'document' in control_desc.lower():
            return "documentation completeness and retention"
        elif 'approve' in control_desc.lower() and 'review' in control_desc.lower():
            return "review and approval process effectiveness"
        
        return ""

    def _generate_focused_test_steps(self, aspect: str, control_type: str) -> List[str]:
        """Generate test steps focused on a specific aspect of a control"""
        aspect_lower = aspect.lower()
        
        if 'report' in aspect_lower:
            return [
                "1. Identify all reporting requirements specified in the control",
                "2. Sample recent reports to verify completeness and accuracy",
                "3. Verify timely distribution to appropriate stakeholders",
                "4. Confirm that report content meets regulatory requirements",
                "5. Test the reporting mechanism for reliability and consistency"
            ]
        elif 'document' in aspect_lower:
            return [
                "1. Identify all documentation requirements in the control",
                "2. Verify that documentation templates are properly defined",
                "3. Sample documentation to verify completeness and accuracy",
                "4. Confirm retention periods are defined and followed",
                "5. Verify accessibility of documentation when needed"
            ]
        elif 'approv' in aspect_lower:
            return [
                "1. Review the approval workflow process documentation",
                "2. Verify appropriate segregation of duties in the approval process",
                "3. Sample transactions to confirm proper approval was obtained",
                "4. Test scenarios requiring escalated approvals",
                "5. Verify that approvals are properly documented and retained"
            ]
        elif 'monitor' in aspect_lower:
            return [
                "1. Review monitoring procedures and frequency",
                "2. Verify that monitoring covers all required elements",
                "3. Test alert mechanisms for proper functioning",
                "4. Confirm that monitoring results are properly reviewed",
                "5. Verify that issues identified through monitoring are addressed"
            ]
        else:
            return [
                f"1. Identify specific requirements related to: {aspect}",
                "2. Develop specific test criteria for this aspect",
                "3. Sample transactions or processes to verify compliance",
                "4. Review documentation specific to this aspect",
                "5. Verify effectiveness through observation and testing"
            ]

    def _generate_control_specific_steps(self, control_desc: str, control_type: str) -> List[str]:
        """Generate additional steps specific to the control content"""
        additional_steps = []
        
        # Add specific steps based on control description content
        if 'training' in control_desc.lower():
            additional_steps.append("Verify training materials are comprehensive and up-to-date")
            additional_steps.append("Confirm training completion records are maintained")
        
        if 'report' in control_desc.lower():
            additional_steps.append("Verify reports contain all required elements")
            additional_steps.append("Test report generation process for accuracy")
        
        if 'review' in control_desc.lower():
            additional_steps.append("Verify evidence of reviews is documented")
            additional_steps.append("Test that review findings are acted upon")
        
        if 'document' in control_desc.lower():
            additional_steps.append("Verify document retention policies are followed")
            additional_steps.append("Test document retrieval process")
        
        # Prefix with step numbers if needed
        if additional_steps:
            start_num = 6  # Assuming there are already 5 steps
            for i in range(len(additional_steps)):
                additional_steps[i] = f"{start_num + i}. {additional_steps[i]}"
        
        return additional_steps

    def _determine_comprehensive_evidence(self, control_type: str, control_desc: str) -> str:
        """Determine comprehensive evidence requirements based on control characteristics"""
        evidence_items = ["Documentation"]
        
        # Basic evidence types based on control type
        if control_type.lower() == "technical" or "system" in control_desc.lower():
            evidence_items.extend(["System logs", "Configuration screenshots", "Access records", "System audit trails"])
        
        if control_type.lower() == "detective" or "monitor" in control_desc.lower():
            evidence_items.extend(["Alert records", "Monitoring reports", "Exception logs", "Review documentation", "Issue tracking records"])
        
        if control_type.lower() == "preventive" or "prevent" in control_desc.lower():
            evidence_items.extend(["Access control lists", "Validation rules documentation", "Restriction evidence", "Configuration settings", "Approval workflows"])
        
        if control_type.lower() == "corrective" or "correct" in control_desc.lower():
            evidence_items.extend(["Incident records", "Remediation documentation", "Corrective action plans", "Follow-up verification", "Resolution evidence"])
        
        if control_type.lower() == "administrative" or "policy" in control_desc.lower():
            evidence_items.extend(["Policy documents", "Training records", "Signed acknowledgements", "Governance documentation", "Meeting minutes"])
        
        if control_type.lower() == "physical":
            evidence_items.extend(["Physical inspection records", "Access logs", "Photographs", "Security assessments", "Visitor logs"])
        
        # Add evidence types based on specific keywords in the control description
        keywords_to_evidence = {
            "train": ["Training materials", "Attendance records", "Comprehension assessments"],
            "report": ["Report samples", "Distribution lists", "Reporting schedules"],
            "review": ["Review documentation", "Reviewer qualifications", "Review findings"],
            "approve": ["Approval signatures", "Approval workflows", "Delegation of authority documentation"],
            "document": ["Document templates", "Completed documentation", "Documentation metadata"],
            "record": ["Record samples", "Record retention schedules", "Record management procedures"],
            "audit": ["Audit reports", "Audit working papers", "Auditor qualifications"],
            "test": ["Test plans", "Test results", "Test coverage analysis"],
            "monitor": ["Monitoring logs", "Monitoring procedures", "Alert configurations"]
        }
        
        # Add relevant evidence types based on keywords in the control description
        for keyword, evidence_types in keywords_to_evidence.items():
            if keyword in control_desc.lower():
                evidence_items.extend(evidence_types)
        
        # Add general evidence types
        evidence_items.append("Interview notes")
        
        # Deduplicate evidence items
        unique_evidence = list(dict.fromkeys(evidence_items))
        
        return ", ".join(unique_evidence)
    
    def _generate_default_steps(self, control_type: str, control_desc: str) -> List[str]:
        """Generate appropriate test steps based on control type and description"""
        if control_type.lower() == "detective":
            return [
                "1. Review detection mechanism documentation",
                "2. Test detection capabilities with sample scenarios",
                "3. Verify alert/notification process",
                "4. Validate response procedures",
                "5. Confirm detection effectiveness through simulated violations"
            ]
        elif control_type.lower() == "preventive":
            return [
                "1. Review control implementation documentation",
                "2. Test preventive measure with sample data",
                "3. Attempt to bypass control (negative testing)",
                "4. Verify logging of attempted violations",
                "5. Confirm the control consistently prevents non-compliant actions"
            ]
        elif control_type.lower() == "corrective":
            return [
                "1. Review correction procedures documentation",
                "2. Validate correction workflow with sample scenarios",
                "3. Verify timeliness of corrective actions",
                "4. Confirm documentation of corrections",
                "5. Test correction effectiveness through follow-up verification"
            ]
        else:
            return [
                "1. Review control documentation",
                "2. Interview responsible personnel",
                "3. Test control using sample data",
                "4. Verify effectiveness against requirements",
                "5. Validate ongoing monitoring and maintenance processes"
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