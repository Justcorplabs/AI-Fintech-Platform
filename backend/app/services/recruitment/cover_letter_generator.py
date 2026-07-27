from typing import List


class CoverLetterGenerator:
    def professional_summary(
        self,
        found_keywords: List[str],
        education_score: int,
        experience_score: int,
        job_title: str,
    ) -> str:
        skills = ", ".join(found_keywords[:6]) if found_keywords else "role-relevant technical, administrative, and analytical skills"

        level = "qualified"
        if education_score >= 90:
            level = "highly qualified"

        if experience_score >= 75:
            experience_phrase = "with practical experience relevant to"
        else:
            experience_phrase = "with growing practical experience and transferable skills for"

        return (
            f"{level.title()} professional {experience_phrase} {job_title}. "
            f"Skilled in {skills}, with the ability to support organisational goals, "
            f"produce accurate work, communicate clearly, and contribute to effective operations."
        )

    def cover_letter(
        self,
        professional_summary: str,
        found_keywords: List[str],
        job_title: str,
        organisation: str,
    ) -> str:
        skills = ", ".join(found_keywords[:5]) if found_keywords else "role-relevant skills, accuracy, communication, and problem-solving"

        return (
            "Dear Hiring Team,\n\n"
            f"I am excited to express my interest in {job_title} at {organisation}. "
            f"{professional_summary}\n\n"
            f"I bring practical strengths in {skills}. I am confident in my ability to learn quickly, "
            "work accurately, support team objectives, and contribute positively to organisational performance.\n\n"
            f"I would welcome the opportunity to discuss how my background and skills align with {job_title} "
            f"and how I can contribute to {organisation}.\n\n"
            "Yours faithfully,\n"
            "Candidate"
        )


cover_letter_generator = CoverLetterGenerator()