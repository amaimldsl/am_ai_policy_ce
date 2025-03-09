from crewai import  LLM
from crew import pcec 


def main():

    # Run the crew
    result = pcec.kickoff()
    print(result)

if __name__ == "__main__":
    main()