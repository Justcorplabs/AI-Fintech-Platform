from typing import List


class InterviewGenerator:
    def generate(
        self,
        found_keywords: List[str],
        missing_keywords: List[str],
        job_title: str,
    ) -> List[str]:
        questions = [
            f"Tell us about your background and how it relates to {job_title}.",
            "Describe a task or project where accuracy and attention to detail were important.",
            "How do you organise your work when handling multiple responsibilities?",
        ]

        if "accounting" in found_keywords or "reconciliation" in found_keywords:
            questions.append("How would you approach reconciling financial records and identifying discrepancies?")

        if "claims" in found_keywords or "claims processing" in found_keywords:
            questions.append("How would you ensure claims are verified, processed accurately, and reported on time?")

        if "payroll" in found_keywords:
            questions.append("What controls would you use when handling payroll or confidential financial information?")

        if "monitoring" in found_keywords or "evaluation" in found_keywords or "mel" in found_keywords:
            questions.append("How would you support monitoring, evaluation, and learning activities?")

        if "customer service" in found_keywords or "sales" in found_keywords:
            questions.append("How would you handle a difficult customer or client interaction?")

        if "procurement" in found_keywords or "supplier management" in found_keywords:
            questions.append("How would you compare supplier quotations and ensure value for money?")

        meaningful_missing = [k for k in missing_keywords if len(k) > 3]

        if meaningful_missing:
            questions.append(f"This role mentions {meaningful_missing[0]}. What exposure do you have to this area?")

        questions.append(f"Which part of the {job_title} job description best matches your current strengths, and why?")

        return questions[:7]


interview_generator = InterviewGenerator()