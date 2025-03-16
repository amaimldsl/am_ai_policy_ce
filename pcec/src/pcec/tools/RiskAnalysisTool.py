# tools/RiskAnalysisTool.py - Enhanced version
from typing import Optional, List, Dict, Any
from crewai.tools import BaseTool
import logging

from tools.Parser_Utils import ParserUtils

logger = logging.getLogger(__name__)

class RiskAnalysisTool(BaseTool):
    name: str = "Risk Analysis Tool"
    description: str = "Analyzes compliance conditions to identify and categorize risks."
    
    def _run(self, 
             conditions: str,
             action: str = "analyze",  # analyze, categorize, prioritize
             criteria: Optional[str] = None,
             **kwargs) -> str:
        try:
            if action == "analyze":
                # Parse the conditions list using centralized parser
                parsed_conditions = ParserUtils.parse_conditions(conditions)
                
                # Generate risk analysis
                risk_analysis = self._analyze_risks(parsed_conditions)
                
                # Format using standard formatter
                return ParserUtils.format_risks(risk_analysis)
                
            elif action == "categorize":
                return self._categorize_risks(conditions, criteria)
                
            elif action == "prioritize":
                return self._prioritize_risks(conditions, criteria)
                
            return f"Invalid action: {action}. Supported actions: analyze, categorize, prioritize."
            
        except Exception as e:
            logger.error(f"Error in RiskAnalysisTool: {str(e)}", exc_info=True)
            return f"Error analyzing risks: {str(e)}"
    
    def _analyze_risks(self, conditions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate risk analysis from conditions"""
        risk_analysis = []
        
        for condition in conditions:
            # Generate risk ID based on condition ID
            condition_id = condition['id']
            risk_id = f"R-{condition_id.replace('C-', '')}"
            
            # Generate risk description based on condition
            condition_desc = condition.get('description', '')
            
            # Analyze the type of risk based on condition text
            risk_type, likelihood, impact = self._determine_risk_factors(condition_desc)
            
            # Generate comprehensive risk description
            risk_desc = f"Risk of non-compliance with {condition_id}: {condition_desc}"
            
            # Add to analysis results
            risk_analysis.append({
                "id": risk_id,
                "condition_id": condition_id,
                "description": risk_desc,
                "type": risk_type,
                "likelihood": likelihood,
                "impact": impact,
                "reference": condition.get("reference", "")
            })
        
        return risk_analysis
    
    def _determine_risk_factors(self, condition_text: str) -> tuple:
        """Analyze condition text to determine risk type, likelihood and impact"""
        # Default values
        risk_type = "Compliance"
        likelihood = "Medium"
        impact = "Medium"
        
        # Keywords that might indicate higher likelihood
        high_likelihood_indicators = ['always', 'must', 'shall', 'all', 'every', 'critical']
        
        # Keywords that might indicate higher impact
        high_impact_indicators = ['severe', 'significant', 'major', 'critical', 'essential', 
                                  'safety', 'security', 'legal', 'regulatory', 'penalty', 'fine']
        
        # Check for high likelihood indicators
        if any(indicator in condition_text.lower() for indicator in high_likelihood_indicators):
            likelihood = "High"
            
        # Check for high impact indicators
        if any(indicator in condition_text.lower() for indicator in high_impact_indicators):
            impact = "High"
            
        # Determine risk type
        if 'financial' in condition_text.lower() or 'cost' in condition_text.lower():
            risk_type = "Financial"
        elif 'reputation' in condition_text.lower():
            risk_type = "Reputational"
        elif 'legal' in condition_text.lower() or 'law' in condition_text.lower():
            risk_type = "Legal"
        elif 'security' in condition_text.lower():
            risk_type = "Security"
        elif 'safety' in condition_text.lower():
            risk_type = "Safety"
            
        return risk_type, likelihood, impact
    
    def _categorize_risks(self, risks_text: str, criteria: Optional[str]) -> str:
        """Categorize risks based on specified criteria"""
        try:
            parsed_risks = ParserUtils.parse_risks(risks_text)
            
            if not criteria:
                criteria = "type"  # Default categorization
                
            categories = {}
            
            # Group risks by the specified criteria
            for risk in parsed_risks:
                category_value = risk.get(criteria, "Unknown")
                
                if category_value not in categories:
                    categories[category_value] = []
                    
                categories[category_value].append(risk)
            
            # Format the output
            output = f"# Risk Categorization by {criteria.capitalize()}\n\n"
            
            for category, risks in categories.items():
                output += f"## {category}\n"
                
                for risk in risks:
                    output += f"- {risk.get('id', 'Unknown')}: {risk.get('description', 'No description')}\n"
                
                output += "\n"
                
            return output
            
        except Exception as e:
            logger.error(f"Error categorizing risks: {str(e)}", exc_info=True)
            return f"Error categorizing risks: {str(e)}"
    
    def _prioritize_risks(self, risks_text: str, criteria: Optional[str]) -> str:
        """Prioritize risks based on specified criteria"""
        try:
            parsed_risks = ParserUtils.parse_risks(risks_text)
            
            # Default prioritization uses both likelihood and impact
            priority_mapping = {
                "High": 3,
                "Medium": 2,
                "Low": 1
            }
            
            # Calculate priority score for each risk
            for risk in parsed_risks:
                likelihood_score = priority_mapping.get(risk.get('likelihood', 'Medium'), 2)
                impact_score = priority_mapping.get(risk.get('impact', 'Medium'), 2)
                
                # Priority score formula
                risk['priority_score'] = likelihood_score * impact_score
                
                # Priority category
                if risk['priority_score'] >= 6:
                    risk['priority'] = "High"
                elif risk['priority_score'] >= 3:
                    risk['priority'] = "Medium"
                else:
                    risk['priority'] = "Low"
            
            # Sort risks by priority score (highest first)
            sorted_risks = sorted(parsed_risks, key=lambda x: x.get('priority_score', 0), reverse=True)
            
            # Format the output
            output = "# Prioritized Risk Register\n\n"
            
            for risk in sorted_risks:
                output += f"## {risk.get('id', 'Unknown')} - Priority: {risk.get('priority', 'Unknown')}\n"
                output += f"**Description**: {risk.get('description', 'No description')}\n"
                output += f"**Likelihood**: {risk.get('likelihood', 'Medium')}\n"
                output += f"**Impact**: {risk.get('impact', 'Medium')}\n"
                output += f"**Priority Score**: {risk.get('priority_score', 0)}\n"
                output += f"**Reference**: {risk.get('reference', 'Unknown')}\n\n"
                
            return output
            
        except Exception as e:
            logger.error(f"Error prioritizing risks: {str(e)}", exc_info=True)
            return f"Error prioritizing risks: {str(e)}"