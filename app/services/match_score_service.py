from app.schemas.job_analysis import JobAnalysis
from app.schemas.job_match import JobMatchAnalysis


class MatchScoreService:

    REQUIRED_WEIGHT = 0.75
    PREFERRED_WEIGHT = 0.25

    def calculate(
        self,
        job: JobAnalysis,
        match: JobMatchAnalysis
    ) -> int:

        required_total = len(job.required_skills)
        preferred_total = len(job.preferred_skills)

        required_matched = len(
            match.matched_required_skills
        )

        preferred_matched = len(
            match.matched_preferred_skills
        )

        required_score = (
            required_matched / required_total
            if required_total
            else 1.0
        )

        preferred_score = (
            preferred_matched / preferred_total
            if preferred_total
            else 1.0
        )

        # If the job has both types of requirements
        if required_total and preferred_total:

            score = (
                required_score * self.REQUIRED_WEIGHT
                +
                preferred_score * self.PREFERRED_WEIGHT
            )

        # Only required skills exist
        elif required_total:

            score = required_score

        # Only preferred skills exist
        elif preferred_total:

            score = preferred_score

        else:
            score = 0

        return round(score * 100)


match_score_service = MatchScoreService()