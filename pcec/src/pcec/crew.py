from crewai import Agent, Task, Crew, Process, LLM

# Import your custom tools here
from tools.PDFTool import PDFTool

# Use the same LLM as in the original code
llm = LLM("ollama/deepseek-r1")

# Define enhanced agents with more specific roles and goals
policy_analyzer = Agent(
    role="Policy Analyzer",
    goal="Extract all policy compliance conditions, requirements, and obligations from the PDF",
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

# Define enhanced tasks with clearer objectives and outputs
extract_conditions_task = Task(
    description="""
    Thoroughly analyze the PDF document and extract ALL policy compliance conditions and requirements.
    Ensure completeness by reviewing each section of the document.
    Format the output as a structured list with condition ID, description, and reference (page/section).
    """,
    expected_output="A comprehensive, structured list of all policy compliance conditions with unique IDs, descriptions, and source references.",
    agent=policy_analyzer,
    llm=llm,
)

identify_risks_task = Task(
    description="""
    For each extracted compliance condition, identify and analyze potential risks of non-compliance.
    Assess the likelihood and potential impact of each risk.
    Format the output as a structured list with risk ID, related condition ID, risk description, likelihood, and impact.
    """,
    expected_output="A detailed risk register mapping risks to compliance conditions with assessment of likelihood and impact.",
    agent=risk_assessor,
    llm=llm,
    context=[extract_conditions_task]
)

design_controls_task = Task(
    description="""
    For each identified risk, design appropriate controls to mitigate the risk and ensure compliance.
    Specify whether each control is preventive, detective, or corrective.
    Format the output as a structured list with control ID, related risk ID, control description, control type, and implementation considerations.
    """,
    expected_output="A comprehensive control framework with specific controls mapped to each identified risk.",
    agent=control_designer,
    llm=llm,
    context=[identify_risks_task]
)

develop_tests_task = Task(
    description="""
    For each control, develop detailed test procedures to verify implementation and effectiveness.
    Include specific steps, expected results, and evidence requirements for each test.
    Format the output as a structured audit program with test ID, related control ID, test objective, detailed test steps, and evidence requirements.
    """,
    expected_output="A detailed audit program with specific test procedures for each control to verify compliance with policy requirements.",
    agent=audit_planner,
    llm=llm,
    context=[design_controls_task]
)

generate_report_task = Task(
    description="""
    Compile all findings into a comprehensive report that includes:
    1. Executive summary of the policy analysis
    2. Complete listing of all compliance conditions
    3. Risk assessment results
    4. Control framework
    5. Audit test procedures
    6. Traceability matrix showing relationships between conditions, risks, controls, and tests
    Format the report in a professional, well-structured manner suitable for executive review.
    """,
    expected_output="A comprehensive compliance analysis report with all components and a traceability matrix.",
    agent=policy_analyzer,
    llm=llm,
    context=[extract_conditions_task, identify_risks_task, design_controls_task, develop_tests_task]
)

# Create enhanced crew with sequential process
enhanced_crew = Crew(
    agents=[policy_analyzer, risk_assessor, control_designer, audit_planner],
    tasks=[extract_conditions_task, identify_risks_task, design_controls_task, develop_tests_task, generate_report_task],
    process=Process.sequential,
    verbose=True,
    llm=llm,
)

# Make crew available for import
pcec = enhanced_crew