import streamlit as st

from bedrock_client import extract_role_facts, generate_recommendations
from storage import save_launch_record, save_needs_information_record
from workflow import (
    assess_readiness,
    build_clarification_questions,
    build_role_spec,
    validate_launch_pack,
)

st.set_page_config(page_title="Role Intake and Search Launch")
st.title("Role Intake and Search Launch")
st.write("Turn a rough hiring request into a structured search plan.")

brief = st.text_area("Describe the role", height=180)

if st.button("Start intake"):
    if not brief.strip():
        st.warning("Please describe the role first.")
    else:
        with st.spinner("Analyzing the role brief with Bedrock..."):
            facts = extract_role_facts(brief)

        decision = assess_readiness(facts)

        st.subheader("Extracted role facts")
        st.json(facts)

        st.subheader("Intake decision")
        if decision["status"] == "Ready to launch":
            with st.spinner("Creating the search launch pack..."):
                recommendations = generate_recommendations(facts)
                launch_pack = build_role_spec(facts) + "\n\n" + recommendations

            problems = validate_launch_pack(launch_pack)

            if problems:
                st.error("Search launch blocked: the pack did not pass validation.")
                for problem in problems:
                    st.write("- " + problem)
                st.subheader("Draft launch pack")
                st.markdown(launch_pack)
            else:
                run_dir = save_launch_record(brief, facts, launch_pack)
                st.success(f"Launched internally. Run ID: {run_dir.name}")
                st.caption("A search kickoff record was created; no candidates were contacted.")
                st.subheader("Search launch pack")
                st.markdown(launch_pack)
        else:
            questions = build_clarification_questions(
                decision["missing_information"]
            )
            run_dir = save_needs_information_record(brief, facts)

            st.warning("Needs information before search launch.")
            st.write("Missing:", ", ".join(decision["missing_information"]))
            st.subheader("Questions for the hiring manager")
            for question in questions:
                st.markdown(f"- {question}")
            st.caption(f"Clarification request saved. Run ID: {run_dir.name}")