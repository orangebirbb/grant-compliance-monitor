import os
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"
os.environ["GOOGLE_CLOUD_PROJECT"] = "sruthi-agent-project"
os.environ["GOOGLE_CLOUD_LOCATION"] = "us-central1"

import asyncio
import fitz  # pymupdf
from google.adk.agents import Agent
from google.adk.agents.sequential_agent import SequentialAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from google.cloud import firestore
from datetime import datetime

# --- Firestore client ---
db = firestore.Client(project="sruthi-agent-project", database="grant-compliance-db")

# --- Agent 1: Intake Agent ---
intake_agent = Agent(
    name="intake_agent",
    model="gemini-2.5-flash",
    description="Reads and extracts all key information from a grant document.",
    instruction="""You are a grant document analyst.
    You will receive the full text of an awarded grant document.
    Extract and clearly list:
    - Grant title and funding agency
    - Total award amount
    - Project start and end dates
    - All reporting deadlines (monthly, quarterly, annual)
    - Key deliverables and milestones
    - Budget categories and restrictions
    - Compliance requirements
    - Any special conditions or obligations
    Be thorough and structured. This information will be used by other agents.""",
)

# --- Agent 2: Compliance Agent ---
compliance_agent = Agent(
    name="compliance_agent",
    model="gemini-2.5-flash",
    description="Checks compliance status and flags risks.",
    instruction="""You are a grant compliance officer.
    Based on the grant information extracted by the previous agent:
    - Identify the top 5 compliance risks
    - Flag any upcoming deadlines in the next 30, 60, and 90 days
    - Highlight budget compliance requirements
    - List any reporting obligations that may be at risk
    - Rate overall compliance risk as LOW, MEDIUM, or HIGH
    Be specific and actionable.""",
)

# --- Agent 3: Report Agent ---
report_agent = Agent(
    name="report_agent",
    model="gemini-2.5-flash",
    description="Drafts a compliance progress report.",
    instruction="""You are a grant reporting specialist.
    Based on the grant analysis and compliance review:
    - Write a professional progress report template
    - Include sections for: Executive Summary, Milestones Achieved, Budget Status, Upcoming Deadlines, Risks and Mitigation
    - Format it ready for submission to the funding agency
    - Keep it concise but comprehensive
    The report should be ready to fill in with actual progress data.""",
)

# --- Agent 4: Recommendation Agent ---
recommendation_agent = Agent(
    name="recommendation_agent",
    model="gemini-2.5-flash",
    description="Provides actionable next steps and recommendations.",
    instruction="""You are a grant management advisor.
    Based on all previous analysis:
    - Provide 5-7 specific, actionable recommendations
    - Prioritize by urgency (immediate, short-term, long-term)
    - Suggest risk mitigation strategies
    - Recommend best practices for maintaining compliance
    - Identify any quick wins the team can achieve immediately
    Be practical and specific to this grant's requirements.""",
)

# --- Chain them together ---
pipeline = SequentialAgent(
    name="grant_compliance_pipeline",
    sub_agents=[intake_agent, compliance_agent, report_agent, recommendation_agent]
)

# --- Session & Runner ---
session_service = InMemorySessionService()
runner = Runner(
    agent=pipeline,
    app_name="grant-compliance-monitor",
    session_service=session_service
)

# --- Extract text from PDF ---
def extract_pdf_text(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

# --- Save to Firestore ---
def save_to_firestore(grant_text, outputs):
    doc_ref = db.collection("grant_sessions").document()
    doc_ref.set({
        "timestamp": datetime.utcnow(),
        "grant_preview": grant_text[:500],
        "intake": outputs[0] if len(outputs) > 0 else "",
        "compliance": outputs[1] if len(outputs) > 1 else "",
        "report": outputs[2] if len(outputs) > 2 else "",
        "recommendations": outputs[3] if len(outputs) > 3 else "",
    })
    return doc_ref.id

# --- Run the pipeline ---
async def run_pipeline(grant_text):
    session = await session_service.create_session(
        app_name="grant-compliance-monitor",
        user_id="user1"
    )

    message = types.Content(
        role="user",
        parts=[types.Part(text=grant_text)]
    )

    outputs = []
    async for response in runner.run_async(
        user_id="user1",
        session_id=session.id,
        new_message=message
    ):
        if response.is_final_response():
            outputs.append(response.content.parts[0].text)

    # Save to Firestore
    session_id = save_to_firestore(grant_text, outputs)

    return {
        "session_id": session_id,
        "intake": outputs[0] if len(outputs) > 0 else "",
        "compliance": outputs[1] if len(outputs) > 1 else "",
        "report": outputs[2] if len(outputs) > 2 else "",
        "recommendations": outputs[3] if len(outputs) > 3 else "",
    }