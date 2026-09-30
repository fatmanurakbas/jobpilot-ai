"""Job analysis agent."""
from app.schemas.job_analysis import JobAnalysis
from app.services.llm_service import llm_service


SYSTEM_PROMPT = """
You are the Job Analyzer Agent of an AI job application system.

Your task is to extract structured information from job advertisements.

Rules:

1. Only extract information supported by the advertisement.
2. Never invent requirements.
3. Never invent company information.
4. Distinguish required skills from preferred skills.
5. If information is unavailable, use null or an empty list.
6. Keep technology names concise and standardized.
7. Do not treat generic responsibilities as technical skills.
8. Preserve important education and language requirements.
9. Determine work model only when supported by the advertisement.
10. Determine employment type only when supported by the advertisement.

Your output will later be used to compare the job against a candidate's CV,
so factual accuracy is more important than filling every field.
"""


class JobAnalyzerAgent:

    def analyze(self, job_description: str) -> JobAnalysis:

        user_prompt = f"""
Analyze the following job advertisement.

JOB ADVERTISEMENT:

{job_description}
"""

        analysis = llm_service.parse(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=JobAnalysis
        )

        return analysis


job_analyzer = JobAnalyzerAgent()