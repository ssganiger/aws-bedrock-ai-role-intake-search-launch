import json

import boto3

MODEL_ID = "global.amazon.nova-2-lite-v1:0"


def extract_role_facts(brief: str) -> dict:
    session = boto3.Session(region_name="ap-southeast-2")
    client = session.client("bedrock-runtime")

    instructions = (
        "Extract facts from this hiring request. Return only a valid JSON "
        "object with exactly these keys: job_title, location, reports_to, "
        "compensation_approved, compensation_range, required_experience, "
        "business_objectives. Use strings for text fields, a boolean for "
        "compensation_approved, and an array of strings for business_objectives. "
        "Use null for missing text, and an empty array for missing objectives. "
        "Set compensation_approved to true only when approval is explicitly "
        "stated. Do not invent facts. Do not use Markdown fences.\n\n"
        "Hiring request:\n"
    )

    response = client.converse(
        modelId=MODEL_ID,
        messages=[
            {
                "role": "user",
                "content": [{"text": instructions + brief}],
            }
        ],
        inferenceConfig={"maxTokens": 400},
    )

    raw_answer = response["output"]["message"]["content"][0]["text"]
    lines = raw_answer.strip().splitlines()

    if len(lines) >= 2 and lines[0].startswith("```") and lines[-1] == "```":
        raw_answer = "\n".join(lines[1:-1])

    return json.loads(raw_answer)


def generate_recommendations(facts: dict) -> str:
    session = boto3.Session(region_name="ap-southeast-2")
    client = session.client("bedrock-runtime")

    instructions = (
        "Create proposed executive search materials in Markdown from the "
        "role facts below. These are recommendations, not new facts or "
        "requirements. Do not add business objectives or claim unknown "
        "details about the role. Do not invent candidates or target companies.\n\n"
        "Use only these two headings:\n"
        "## Search strategy\n"
        "Recommend three candidate backgrounds, five search keywords, and "
        "two sourcing channels. Label them as recommendations.\n"
        "## Interview scorecard\n"
        "Recommend four criteria with weights totaling 100%, evidence to "
        "look for, and one question for each. This is an interview guide, "
        "not a hiring decision. Avoid generic 'To confirm' text.\n\n"
        "Role facts:\n"
    )

    response = client.converse(
        modelId=MODEL_ID,
        messages=[
            {
                "role": "user",
                "content": [
                    {"text": instructions + json.dumps(facts, ensure_ascii=False)}
                ],
            }
        ],
        inferenceConfig={"maxTokens": 1200, "temperature": 0.2},
    )

    blocks = response["output"]["message"]["content"]
    recommendations = "".join(
        block["text"] for block in blocks if "text" in block
    )

    if not recommendations.strip():
        raise ValueError("Bedrock returned empty search recommendations")

    return recommendations.strip()



if __name__ == "__main__":
    sample_brief = (
        "Our SaaS company needs a Head of Customer Success based in Sydney. "
        "They will lead a 12-person team, improve enterprise renewals, and "
        "report to the COO. We require experience scaling B2B SaaS customer "
        "success teams. The approved compensation range is AUD 180,000–220,000."
    )
    facts = extract_role_facts(sample_brief)
    print(json.dumps(facts, indent=2))
    print("\n--- LAUNCH PACK ---\n")
    print(generate_recommendations(facts))