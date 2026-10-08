import re

REQUIRED_TEXT_FIELDS = {
    "job_title": "job title",
    "location": "location",
    "reports_to": "reporting line",
    "compensation_range": "compensation range",
    "required_experience": "required experience",
}

CLARIFICATION_QUESTIONS = {
    "job title": "What is the exact title of this role?",
    "location": "Where will this role be based?",
    "reporting line": "Who will this role report to?",
    "compensation range": "What compensation range is proposed?",
    "required experience": "What experience is required?",
    "approved compensation": "Has the compensation range been approved?",
    "business objectives": "What business outcome should this role deliver?",
}


def assess_readiness(facts: dict) -> dict:
    missing = []

    for field, label in REQUIRED_TEXT_FIELDS.items():
        value = facts.get(field)
        if not isinstance(value, str) or not value.strip():
            missing.append(label)

    if facts.get("compensation_approved") is not True:
        missing.append("approved compensation")

    objectives = facts.get("business_objectives")
    if not isinstance(objectives, list) or not any(
        isinstance(item, str) and item.strip() for item in objectives
    ):
        missing.append("business objectives")

    return {
        "status": "Ready to launch" if not missing else "Needs information",
        "missing_information": missing,
    }

def build_clarification_questions(missing: list[str]) -> list[str]:
    return [
        CLARIFICATION_QUESTIONS.get(item, f"Please provide {item}.")
        for item in missing
    ]


def build_role_spec(facts: dict) -> str:
    lines = [
        "## Role specification",
        "",
        f"- **Title:** {facts['job_title']}",
        f"- **Location:** {facts['location']}",
        f"- **Reports to:** {facts['reports_to']}",
        f"- **Approved compensation:** {facts['compensation_range']}",
        f"- **Required experience:** {facts['required_experience']}",
        "",
        "**Business objectives:**",
    ]

    for objective in facts["business_objectives"]:
        lines.append(f"- {objective}")

    return "\n".join(lines)

def validate_launch_pack(pack: str) -> list[str]:
    problems = []
    section_names = [
        "Role specification",
        "Search strategy",
        "Interview scorecard",
    ]
    matches = [
        re.search(
            rf"^##[ \t]+{re.escape(name)}[ \t]*$",
            pack,
            flags=re.IGNORECASE | re.MULTILINE,
        )
        for name in section_names
    ]

    if any(match is None for match in matches):
        problems.append("A required launch-pack section is missing")
    else:
        positions = [match.start() for match in matches]
        if positions != sorted(positions):
            problems.append("Launch-pack sections are out of order")

    scorecard_match = matches[2]
    if scorecard_match is not None:
        scorecard = pack[scorecard_match.end():]
        weights = [
            int(value)
            for value in re.findall(
                r"(?m)^[ \t]*\d+\.[ \t]+[^\n]*\((\d+)%\)",
                scorecard,
            )
        ]
        if len(weights) != 4 or sum(weights) != 100:
            problems.append("Scorecard needs four weights totaling 100%")

    return problems

if __name__ == "__main__":
    complete = {
        "job_title": "Head of Customer Success",
        "location": "Sydney",
        "reports_to": "COO",
        "compensation_approved": True,
        "compensation_range": "AUD 180,000–220,000",
        "required_experience": "B2B SaaS leadership",
        "business_objectives": ["Improve enterprise renewals"],
    }

    incomplete = {
        **complete,
        "location": None,
        "compensation_range": None,
        "compensation_approved": False,
    }

    print("Complete brief:", assess_readiness(complete))
    print("Incomplete brief:", assess_readiness(incomplete))

    missing = assess_readiness(incomplete)["missing_information"]
    print("Clarification questions:")
    for question in build_clarification_questions(missing):
        print("-", question)

    print("\n--- FACTUAL ROLE SPECIFICATION ---\n")
    print(build_role_spec(complete))

    example_pack = build_role_spec(complete) + (
        "\n\n## Search strategy\nRecommended search approach"
        "\n\n## Interview scorecard\n"
        "1. Leadership (30%)\n"
        "2. Experience (25%)\n"
        "3. Operations (25%)\n"
        "4. Stakeholders (20%)"
    )
    print("Valid pack problems:", validate_launch_pack(example_pack))
    print(
        "Invalid pack problems:",
        validate_launch_pack(example_pack.replace("(20%)", "(10%)")),
    )
    print(
        "Capitalized heading problems:",
        validate_launch_pack(
            example_pack.replace("## Interview scorecard", "## Interview Scorecard")
        ),
    )