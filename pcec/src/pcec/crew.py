# Modified tasks for crew.py
from crewai import Agent, Task, Crew, Process
from crewai import LLM
import os
from pathlib import Path
from dotenv import load_dotenv

# Import your custom tools here
from tools.PDFTool import PDFTool

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

# Define agents (unchanged)
policy_analyzer = Agent(
    role="Policy Analyzer",
    goal="Extract all policy compliance conditions, requirements, and obligations from preprocessed document chunks",
    backstory="You are an expert in policy analysis with experience in regulatory frameworks and compliance requirements extraction.",
    tools=[PDFTool()],
    llm=llm,
    verbose=True
)

risk_assessor = Agent(
    role="Risk Assessor",
    goal="Identify and categorize all potential risks associated with each compliance condition",
    backstory="You are a risk management professional who specializes in identifying compliance-related risks and their potential impacts.",
    tools=[PDFTool()],
    llm=llm,
    verbose=True
)

control_designer = Agent(
    role="Control Designer",
    goal="Design appropriate controls for mitigating each identified risk",
    backstory="You are a control framework specialist who develops robust control mechanisms to ensure policy compliance.",
    tools=[PDFTool()],
    llm=llm,
    verbose=True
)

audit_planner = Agent(
    role="Audit Planner",
    goal="Create comprehensive test procedures to verify compliance with all conditions",
    backstory="You are an experienced compliance auditor who develops thorough audit plans with specific test procedures.",
    tools=[PDFTool()],
    llm=llm,
    verbose=True
)

# Define list chunks task
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
        """,
        expected_output=f"A list of policy compliance conditions extracted from chunk {chunk_index}.",
        agent=policy_analyzer,
        context=[list_chunks_task],
        output_file=str(output_dir / f"1_conditions_chunk_{chunk_index}.md")
    )

# Create initial chunk tasks
initial_chunk_tasks = [create_chunk_processing_task(i) for i in range(15)]  # Process first 15 chunks

# Create consolidation task
consolidate_conditions_task = Task(
    description="""
    Consolidate all the conditions extracted from ALL individual chunks into a single comprehensive list.
    Ensure to process EVERY chunk output from 0 to the highest chunk number.
    Ensure consistent formatting and resolve any duplicates or overlapping conditions.
    Each condition should include a reference to its source document and page.
    """,
    expected_output="A consolidated list of all policy compliance conditions from all analyzed chunks.",
    agent=policy_analyzer,
    context=initial_chunk_tasks,  # Pass the chunk tasks as context
    output_file=str(output_dir / "2_consolidated_conditions.md")
)

# Split the consolidated conditions into groups for distributed risk assessment
split_conditions_task = Task(
    description="""
    Split the consolidated list of conditions into three equal groups for distributed risk assessment.
    Create three separate documents with approximately equal numbers of conditions from the consolidated list.
    Each group should maintain the original condition IDs and all relevant information.
    Ensure that each condition appears in exactly one group.
    """,
    expected_output="Three separate lists of conditions for distributed risk assessment.",
    agent=policy_analyzer,
    context=[consolidate_conditions_task],
    output_file=str(output_dir / "2a_split_conditions.md")
)

# Create three separate risk assessment tasks for each group of conditions
risk_assessment_group1_task = Task(
    description="""
    Analyze ONLY the first group of conditions from the split conditions task.
    For each condition in GROUP 1:
    1. Assess the likelihood of non-compliance (Low, Medium, High)
    2. Assess the potential impact of non-compliance (Low, Medium, High)
    3. Provide a brief description of the risk scenario
    
    Format the output as a structured list with risk ID, related condition ID, risk description, likelihood, and impact.
    Include references to the source document and page for each risk as provided in the original condition list.
    """,
    expected_output="Risk assessment for the first group of compliance conditions.",
    agent=risk_assessor,
    context=[split_conditions_task],
    output_file=str(output_dir / "3a_risk_assessment_group1.md")
)

risk_assessment_group2_task = Task(
    description="""
    Analyze ONLY the second group of conditions from the split conditions task.
    For each condition in GROUP 2:
    1. Assess the likelihood of non-compliance (Low, Medium, High)
    2. Assess the potential impact of non-compliance (Low, Medium, High)
    3. Provide a brief description of the risk scenario
    
    Format the output as a structured list with risk ID, related condition ID, risk description, likelihood, and impact.
    Include references to the source document and page for each risk as provided in the original condition list.
    """,
    expected_output="Risk assessment for the second group of compliance conditions.",
    agent=risk_assessor,
    context=[split_conditions_task],
    output_file=str(output_dir / "3b_risk_assessment_group2.md")
)

risk_assessment_group3_task = Task(
    description="""
    Analyze ONLY the third group of conditions from the split conditions task.
    For each condition in GROUP 3:
    1. Assess the likelihood of non-compliance (Low, Medium, High)
    2. Assess the potential impact of non-compliance (Low, Medium, High)
    3. Provide a brief description of the risk scenario
    
    Format the output as a structured list with risk ID, related condition ID, risk description, likelihood, and impact.
    Include references to the source document and page for each risk as provided in the original condition list.
    """,
    expected_output="Risk assessment for the third group of compliance conditions.",
    agent=risk_assessor,
    context=[split_conditions_task],
    output_file=str(output_dir / "3c_risk_assessment_group3.md")
)

# Consolidate the separate risk assessments
consolidate_risks_task = Task(
    description="""
    Consolidate the risk assessments from all three groups into a comprehensive risk register.
    Ensure consistent formatting and resolve any duplicates.
    Maintain all risk information including risk ID, related condition ID, risk description, likelihood, impact, and references.
    Ensure that the consolidated risk register is complete and covers all conditions from the consolidated list.
    """,
    expected_output="A consolidated risk register covering all compliance conditions.",
    agent=risk_assessor,
    context=[risk_assessment_group1_task, risk_assessment_group2_task, risk_assessment_group3_task],
    output_file=str(output_dir / "3d_consolidated_risk_register.md")
)

# Similarly split the control design process
split_risks_task = Task(
    description="""
    Split the consolidated risk register into two equal groups for distributed control design.
    Create two separate documents with approximately equal numbers of risks.
    Each group should maintain the original risk IDs and all relevant information.
    Ensure that each risk appears in exactly one group.
    """,
    expected_output="Two separate lists of risks for distributed control design.",
    agent=risk_assessor,
    context=[consolidate_risks_task],
    output_file=str(output_dir / "4a_split_risks.md")
)

design_controls_group1_task = Task(
    description="""
    For each risk in GROUP 1 of the split risks, design appropriate controls to mitigate the risk and ensure compliance.
    Specify whether each control is preventive, detective, or corrective.
    Format the output as a structured list with control ID, related risk ID, control description, control type, and implementation considerations.
    Include references to the original policy condition's document source and page.
    """,
    expected_output="Control framework for the first group of risks.",
    agent=control_designer,
    context=[split_risks_task],
    output_file=str(output_dir / "4b_control_framework_group1.md")
)

design_controls_group2_task = Task(
    description="""
    For each risk in GROUP 2 of the split risks, design appropriate controls to mitigate the risk and ensure compliance.
    Specify whether each control is preventive, detective, or corrective.
    Format the output as a structured list with control ID, related risk ID, control description, control type, and implementation considerations.
    Include references to the original policy condition's document source and page.
    """,
    expected_output="Control framework for the second group of risks.",
    agent=control_designer,
    context=[split_risks_task],
    output_file=str(output_dir / "4c_control_framework_group2.md")
)

consolidate_controls_task = Task(
    description="""
    Consolidate the control frameworks from both groups into a comprehensive control framework.
    Ensure consistent formatting and resolve any duplicates.
    Maintain all control information including control ID, related risk ID, control description, control type, implementation considerations, and references.
    Ensure that the consolidated control framework is complete and covers all risks from the consolidated risk register.
    """,
    expected_output="A consolidated control framework covering all identified risks.",
    agent=control_designer,
    context=[design_controls_group1_task, design_controls_group2_task],
    output_file=str(output_dir / "4d_consolidated_control_framework.md")
)

# Similarly split the test procedure development
split_controls_task = Task(
    description="""
    Split the consolidated control framework into two equal groups for distributed test procedure development.
    Create two separate documents with approximately equal numbers of controls.
    Each group should maintain the original control IDs and all relevant information.
    Ensure that each control appears in exactly one group.
    """,
    expected_output="Two separate lists of controls for distributed test procedure development.",
    agent=control_designer,
    context=[consolidate_controls_task],
    output_file=str(output_dir / "5a_split_controls.md")
)

develop_tests_group1_task = Task(
    description="""
    For each control in GROUP 1 of the split controls, develop detailed test procedures to verify implementation and effectiveness.
    Include specific steps, expected results, and evidence requirements for each test.
    Format the output as a structured audit program with test ID, related control ID, test objective, detailed test steps, and evidence requirements.
    Maintain traceability to the original source documents by including references to document names and page numbers.
    """,
    expected_output="Test procedures for the first group of controls.",
    agent=audit_planner,
    context=[split_controls_task],
    output_file=str(output_dir / "5b_audit_test_procedures_group1.md")
)

develop_tests_group2_task = Task(
    description="""
    For each control in GROUP 2 of the split controls, develop detailed test procedures to verify implementation and effectiveness.
    Include specific steps, expected results, and evidence requirements for each test.
    Format the output as a structured audit program with test ID, related control ID, test objective, detailed test steps, and evidence requirements.
    Maintain traceability to the original source documents by including references to document names and page numbers.
    """,
    expected_output="Test procedures for the second group of controls.",
    agent=audit_planner,
    context=[split_controls_task],
    output_file=str(output_dir / "5c_audit_test_procedures_group2.md")
)

consolidate_tests_task = Task(
    description="""
    Consolidate the test procedures from both groups into a comprehensive audit program.
    Ensure consistent formatting and resolve any duplicates.
    Maintain all test information including test ID, related control ID, test objective, detailed test steps, evidence requirements, and references.
    Ensure that the consolidated audit program is complete and covers all controls from the consolidated control framework.
    """,
    expected_output="A consolidated audit program covering all controls.",
    agent=audit_planner,
    context=[develop_tests_group1_task, develop_tests_group2_task],
    output_file=str(output_dir / "5d_consolidated_audit_program.md")
)

# Final report generation
generate_report_task = Task(
    description="""
    Compile all findings into a comprehensive report that includes:
    1. Executive summary of the policy analysis
    2. Complete listing of all compliance conditions with document sources
    3. Risk assessment results
    4. Control framework
    5. Audit test procedures
    6. Traceability matrix showing relationships between conditions, risks, controls, and tests, including document sources
    Format the report in a professional, well-structured manner suitable for executive review.
    Ensure full traceability to source documents by including document names and page numbers in all references.
    """,
    expected_output="A comprehensive compliance analysis report with all components and a traceability matrix that includes source document references.",
    agent=policy_analyzer,
    context=[consolidate_conditions_task, consolidate_risks_task, consolidate_controls_task, consolidate_tests_task],
    output_file=str(output_dir / "6_final_compliance_report.md")
)

# Create the crew with the tasks in the correct order
chunk_processing_crew = Crew(
    agents=[policy_analyzer, risk_assessor, control_designer, audit_planner],
    tasks=[
        list_chunks_task,
        *initial_chunk_tasks,
        consolidate_conditions_task,
        # Distributed risk assessment
        split_conditions_task,
        risk_assessment_group1_task,
        risk_assessment_group2_task,
        risk_assessment_group3_task,
        consolidate_risks_task,
        # Distributed control design
        split_risks_task,
        design_controls_group1_task,
        design_controls_group2_task,
        consolidate_controls_task,
        # Distributed test procedure development
        split_controls_task,
        develop_tests_group1_task,
        develop_tests_group2_task,
        consolidate_tests_task,
        # Final report
        generate_report_task
    ],
    process=Process.sequential,
    verbose=True,
)

# Make crew
pcec = chunk_processing_crew