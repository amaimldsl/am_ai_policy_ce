# Modified crew.py
from crewai import Agent, Task, Crew, Process
from crewai import LLM
import os
from pathlib import Path
from dotenv import load_dotenv

# Import your custom tools here
from tools.PDFTool import PDFTool
from tools.FileIOTool import FileIOTool
from tools.RiskAnalysisTool import RiskAnalysisTool
from tools.ControlDesignTool import ControlDesignTool
from tools.AuditPlanningTool import AuditPlanningTool

# Load environment variables
load_dotenv()

# Create output directory if it doesn't exist
output_dir = Path(__file__).parent / "output"
output_dir.mkdir(exist_ok=True)

# Get DeepSeek API credentials
deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
deepseek_api_base = os.getenv("DEEPSEEK_API_BASE")
deepseek_model = os.getenv("DEEPSEEK_MODEL", "deepseek/deepseek-chat")

# Initialize the DeepSeek LLM with reduced max_tokens
llm = LLM(
    model=deepseek_model,
    api_key=deepseek_api_key,
    api_base=deepseek_api_base,
    temperature=0.2,
    max_tokens=2048,  # Reduced for better handling of long outputs
    streaming=True
)

# Define agents with appropriate tools for each role
policy_analyzer = Agent(
    role="Policy Analyzer",
    goal="Extract all policy compliance conditions, requirements, and obligations from preprocessed document chunks",
    backstory="You are an expert in policy analysis with experience in regulatory frameworks and compliance requirements extraction.",
    tools=[PDFTool(), FileIOTool()],  # Added FileIOTool
    llm=llm,
    verbose=True
)

risk_assessor = Agent(
    role="Risk Assessor",
    goal="Identify and categorize all potential risks associated with each compliance condition",
    backstory="You are a risk management professional who specializes in identifying compliance-related risks and their potential impacts.",
    tools=[FileIOTool(), RiskAnalysisTool()],  # Specialized tools instead of PDFTool
    llm=llm,
    verbose=True
)

control_designer = Agent(
    role="Control Designer",
    goal="Design appropriate controls for mitigating each identified risk",
    backstory="You are a control framework specialist who develops robust control mechanisms to ensure policy compliance.",
    tools=[FileIOTool(), ControlDesignTool()],  # Specialized tools instead of PDFTool
    llm=llm,
    verbose=True
)

audit_planner = Agent(
    role="Audit Planner",
    goal="Create comprehensive test procedures to verify compliance with all conditions",
    backstory="You are an experienced compliance auditor who develops thorough audit plans with specific test procedures.",
    tools=[FileIOTool(), AuditPlanningTool()],  # Specialized tools instead of PDFTool
    llm=llm,
    verbose=True
)

# The rest of your task definitions remain similar, but use the new tools
# For example:

list_chunks_task = Task(
    description="""
    List all available preprocessed document chunks.
    Use the PDFTool with the following parameters:
    - chunk_path: "" (empty string)
    - chunk_index: null
    - query: "" (empty string)
    
    This will return a list of all preprocessed chunks available for analysis.
    """,
    expected_output="A list of all preprocessed document chunks available for analysis.",
    agent=policy_analyzer,
    output_file=str(output_dir / "0_chunk_list.md")
)

# Function to create a task for processing a specific chunk
def create_chunk_processing_task(chunk_index):
    return Task(
        description=f"""
        Analyze document chunk with index {chunk_index}.
        Use the PDFTool with the following parameters:
        - chunk_path: "" (empty string)
        - chunk_index: {chunk_index}
        - query: "" (empty string)
        
        Extract all policy compliance conditions and requirements from this chunk.
        Identify requirements using keywords like 'shall', 'must', 'should', 'required', 'obligated', etc.
        Format the output as a structured list with condition ID, description, and reference (document name, page/section).
        Include the source document name in each reference.
        
        Save the results using the FileIOTool with:
        - action: "write"
        - filepath: "1_conditions_chunk_{chunk_index}.md"
        """,
        expected_output=f"A list of policy compliance conditions extracted from chunk {chunk_index}.",
        agent=policy_analyzer,
        context=[list_chunks_task],
        output_file=str(output_dir / f"1_conditions_chunk_{chunk_index}.md")
    )

# Create initial chunk tasks
initial_chunk_tasks = [create_chunk_processing_task(i) for i in range(15)]  # Process first 15 chunks

# Create consolidation task with FileIOTool
consolidate_conditions_task = Task(
    description="""
    Consolidate all the conditions extracted from ALL individual chunks into a single comprehensive list.
    Use the FileIOTool with action "read" to read each chunk output file from "1_conditions_chunk_0.md" through "1_conditions_chunk_14.md".
    Ensure consistent formatting and resolve any duplicates or overlapping conditions.
    Each condition should include a reference to its source document and page.
    
    Save the consolidated list using the FileIOTool with:
    - action: "write"
    - filepath: "2_consolidated_conditions.md"
    """,
    expected_output="A consolidated list of all policy compliance conditions from all analyzed chunks.",
    agent=policy_analyzer,
    context=initial_chunk_tasks,
    output_file=str(output_dir / "2_consolidated_conditions.md")
)

# Modified risk assessment tasks using the new tools
risk_assessment_task = Task(
    description="""
    Perform risk assessment on the consolidated conditions list.
    
    1. Use the FileIOTool to read the consolidated conditions from "2_consolidated_conditions.md"
    2. Use the RiskAnalysisTool with action "analyze" to identify risks for each condition
    3. Assess the likelihood of non-compliance (Low, Medium, High)
    4. Assess the potential impact of non-compliance (Low, Medium, High)
    5. Provide a brief description of the risk scenario
    
    Save the risk assessment results using the FileIOTool with:
    - action: "write"
    - filepath: "3_risk_assessment.md"
    """,
    expected_output="A comprehensive risk assessment for all compliance conditions.",
    agent=risk_assessor,
    context=[consolidate_conditions_task],
    output_file=str(output_dir / "3_risk_assessment.md")
)

# Modified control design task using the new tools
design_controls_task = Task(
    description="""
    Design appropriate controls for each identified risk.
    
    1. Use the FileIOTool to read the risk assessment from "3_risk_assessment.md"
    2. Use the ControlDesignTool with action "design" to create control measures for each risk
    3. Specify whether each control is preventive, detective, or corrective
    4. Provide implementation considerations for each control
    
    Save the control framework using the FileIOTool with:
    - action: "write"
    - filepath: "4_control_framework.md"
    """,
    expected_output="A comprehensive control framework for mitigating all identified risks.",
    agent=control_designer,
    context=[risk_assessment_task],
    output_file=str(output_dir / "4_control_framework.md")
)

# Modified audit planning task using the new tools
develop_tests_task = Task(
    description="""
    Develop test procedures for verifying each control.
    
    1. Use the FileIOTool to read the control framework from "4_control_framework.md"
    2. Use the AuditPlanningTool with action "develop" to create test procedures for each control
    3. Include specific steps, expected results, and evidence requirements for each test
    
    Save the audit program using the FileIOTool with:
    - action: "write"
    - filepath: "5_audit_program.md"
    """,
    expected_output="A comprehensive audit program for verifying all controls.",
    agent=audit_planner,
    context=[design_controls_task],
    output_file=str(output_dir / "5_audit_program.md")
)

# Final report generation
generate_report_task = Task(
    description="""
    Compile all findings into a comprehensive report.
    
    Use the FileIOTool to read the following files:
    - "2_consolidated_conditions.md" (compliance conditions)
    - "3_risk_assessment.md" (risk assessment)
    - "4_control_framework.md" (control framework)
    - "5_audit_program.md" (audit program)
    
    Create a professional report that includes:
    1. Executive summary
    2. Compliance conditions list
    3. Risk assessment summary
    4. Control framework
    5. Audit test procedures
    6. Traceability matrix showing relationships between conditions, risks, controls, and tests
    
    Save the final report using the FileIOTool with:
    - action: "write"
    - filepath: "6_final_compliance_report.md"
    """,
    expected_output="A comprehensive compliance analysis report with all components.",
    agent=policy_analyzer,
    context=[consolidate_conditions_task, risk_assessment_task, design_controls_task, develop_tests_task],
    output_file=str(output_dir / "6_final_compliance_report.md")
)

# Create the crew with the streamlined tasks
compliance_analysis_crew = Crew(
    agents=[policy_analyzer, risk_assessor, control_designer, audit_planner],
    tasks=[
        list_chunks_task,
        *initial_chunk_tasks,
        consolidate_conditions_task,
        risk_assessment_task,      # Single task instead of multiple group tasks
        design_controls_task,      # Single task instead of multiple group tasks
        develop_tests_task,        # Single task instead of multiple group tasks
        generate_report_task
    ],
    process=Process.sequential,
    verbose=True,
)

# Make crew
pcec = compliance_analysis_crew