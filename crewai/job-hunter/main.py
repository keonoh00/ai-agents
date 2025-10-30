import dotenv

dotenv.load_dotenv()

from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource
from crewai.project import CrewBase, agent, crew, task
from models import ChosenJob, JobList, RankedJobList
from tools import web_search_tool

from crewai import Agent, Crew, Task

resume_knowledge_for_job_matching_agent = TextFileKnowledgeSource(
    file_paths=["resume.txt"], collection_name="resume_for_job_matching_agent"
)
resume_knowledge_for_company_research_agent = TextFileKnowledgeSource(
    file_paths=["resume.txt"], collection_name="resume_for_company_research_agent"
)
interview_prep_knowledge_for_interview_prep_agent = TextFileKnowledgeSource(
    file_paths=["resume.txt"], collection_name="resume_for_interview_prep_agent"
)
resume_knowledge_for_resume_optimization_agent = TextFileKnowledgeSource(
    file_paths=["resume.txt"], collection_name="resume_for_resume_optimization_agent"
)


@CrewBase
class JobHunterCrew:

    @agent
    def job_search_agent(self):
        return Agent(
            config=self.agents_config["job_search_agent"],
            tools=[web_search_tool],
        )

    @agent
    def job_matching_agent(self):
        return Agent(
            config=self.agents_config["job_matching_agent"],
            knowledge_sources=[resume_knowledge_for_job_matching_agent],
        )

    @agent
    def resume_optimization_agent(self):
        return Agent(
            config=self.agents_config["resume_optimization_agent"],
            knowledge_sources=[resume_knowledge_for_resume_optimization_agent],
        )

    @agent
    def company_research_agent(self):
        return Agent(
            config=self.agents_config["company_research_agent"],
            tools=[web_search_tool],
            knowledge_sources=[resume_knowledge_for_company_research_agent],
        )

    @agent
    def interview_prep_agent(self):
        return Agent(
            config=self.agents_config["interview_prep_agent"],
            knowledge_sources=[interview_prep_knowledge_for_interview_prep_agent],
        )

    @task
    def job_extraction_task(self):
        return Task(
            config=self.tasks_config["job_extraction_task"],
            output_pydantic=JobList,
        )

    @task
    def job_matching_task(self):
        return Task(
            config=self.tasks_config["job_matching_task"],
            output_pydantic=RankedJobList,
        )

    @task
    def job_selection_task(self):
        return Task(
            config=self.tasks_config["job_selection_task"],
            output_pydantic=ChosenJob,
        )

    @task
    def resume_rewriting_task(self):
        return Task(
            config=self.tasks_config["resume_rewriting_task"],
            context=[
                self.job_selection_task(),
            ],
        )

    @task
    def company_research_task(self):
        return Task(
            config=self.tasks_config["company_research_task"],
            context=[
                self.job_selection_task(),
            ],
        )

    @task
    def interview_prep_task(self):
        return Task(
            config=self.tasks_config["interview_prep_task"],
            context=[
                self.job_selection_task(),
                self.resume_rewriting_task(),
                self.company_research_task(),
            ],
        )

    @crew
    def crew(self):
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            verbose=True,
        )


JobHunterCrew().crew().kickoff(
    inputs={
        "level": "IC2 or Similar",
        "position": "Software Engineer with tech stack of react native/react/python. With fully asynchronous culture and remote friendly.",
        "location": "Remote",
    },
)
