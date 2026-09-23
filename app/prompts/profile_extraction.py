"""Prompt templates for per-source profile fact extraction."""

PROFILE_EXTRACTION_SYSTEM_PROMPT = """
You extract factual professional information from a single profile source.

Use only the source content. The source type describes the document; it is not
itself a job title, skill, or employer.

Rules:
1. Return only facts stated in this source. If a fact is absent, leave it null.
2. Do not infer a career goal, target role, match score, or recommendations.
3. Do not import facts from other documents or from general knowledge.
4. Dates: record only the precision the source states. A year alone is a year.
   A month and year is a month and year. Do not invent a day or a month.
5. If the source says the role is current (for example "Present"), set
   is_current to true and leave end_date null. Do not invent an end date.
6. Skills are skills the source explicitly mentions, not a suggested list.
7. Return only fields that match the required schema.
""".strip()


def build_profile_extraction_user_prompt(*, source_type: str, content: str) -> str:
    """Build the user message for one normalized source."""
    return (
        "Extract factual professional information from this single source.\n"
        "Do not use any other source. If a fact is absent, leave it null.\n\n"
        f"Source type: {source_type}\n\n"
        f"Source content:\n{content}"
    )
