from crewai import Agent, Task, Crew, Process,LLM

# Import your custom tools here
from tools.PDFTool import PDFTool


#llm = LLM("ollama/deepseek-r1:14b")

llm = LLM("ollama/deepseek-r1")


# Define your agents
researcher = Agent(
    role="Policy Researcher",
    goal="Extract all policy compliance conditions from the PDF",
    backstory="You are an expert in policy analysis and compliance extraction.",
    tools=[PDFTool()],
    llm= llm,
    verbose=True
)

auditor = Agent(
    role="Compliance Auditor",
    goal="Formulate audit steps for each compliance condition",
    backstory="You are an experienced auditor who creates thorough audit plans.",
    tools=[PDFTool()],
    llm= llm,
    verbose=True
)

# Define your tasks
extract_task = Task(
    description="Extract ALL policy compliance conditions from the PDF. Ensure completeness.",
    expected_output="A comprehensive list of all policy compliance conditions from the PDF document.",
    agent=researcher,
    llm= llm,
)

audit_task = Task(
    description="For each extracted condition, create detailed audit steps that test compliance against current practices.",
    expected_output="A detailed audit plan with specific steps to verify compliance for each condition.",
    agent=auditor,
    llm= llm,
)

# Create your crew
crew = Crew(
    agents=[researcher, auditor],
    tasks=[extract_task, audit_task],
    process=Process.sequential,
    verbose=True,
    llm= llm,
)

# Make crew available for import
pcec = crew