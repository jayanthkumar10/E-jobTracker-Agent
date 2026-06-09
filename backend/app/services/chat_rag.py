from sqlalchemy.orm import Session
from datetime import datetime
import logging
from typing import List

from app.models.application import Application, Interview
from app.models.email import Email
from app.services.ai_engine import AIEngineService
import google.generativeai as genai

logger = logging.getLogger(__name__)

class ChatRAGService:
    @classmethod
    def answer_query(cls, db: Session, user_id: str, question: str) -> dict:
        """
        Processes a user question by assembling relational database stats
        and searching semantic email records, then queries Gemini for the final answer.
        """
        # 1. Fetch all structured applications context (perfect for count, rejections, lists)
        apps = db.query(Application).filter(Application.user_id == user_id).all()
        
        apps_context = []
        for app in apps:
            apps_context.append(
                f"- **Company**: {app.company_name} | **Role**: {app.job_title} | **Status**: {app.status} | "
                f"**Salary**: {app.salary_range or 'N/A'} | **Location**: {app.location or 'N/A'} | "
                f"**Recruiter**: {app.recruiter_name or 'N/A'} ({app.recruiter_email or 'N/A'})"
            )
        
        # Fetch upcoming interviews
        interviews = db.query(Interview).join(Application).filter(
            Application.user_id == user_id,
            Interview.scheduled_at >= datetime.utcnow()
        ).order_by(Interview.scheduled_at.asc()).all()
        
        interviews_context = []
        for iv in interviews:
            interviews_context.append(
                f"- **Interview**: {iv.stage_name} with {iv.application.company_name} on {iv.scheduled_at.strftime('%Y-%m-%d %H:%M')}"
            )
            
        # 2. Perform Vector Search over email history for semantic questions (e.g. "why was I rejected?")
        emails_context = []
        referenced_emails = []
        
        # Generate query embedding
        query_embedding = AIEngineService.generate_embedding(question)
        if query_embedding:
            try:
                # Retrieve top 5 semantically matching emails using cosine distance
                matching_emails = db.query(Email).filter(
                    Email.user_id == user_id
                ).order_by(
                    Email.embedding.cosine_distance(query_embedding)
                ).limit(5).all()
                
                for email in matching_emails:
                    emails_context.append(
                        f"Subject: {email.subject}\n"
                        f"From: {email.sender_email} | Date: {email.received_at.strftime('%Y-%m-%d')}\n"
                        f"Content: {email.body_text[:1000]}...\n"
                        f"---"
                    )
                    # Track references for API response debugging/highlights
                    referenced_emails.append({
                        "id": str(email.id),
                        "subject": email.subject,
                        "company_name": email.application.company_name if email.application else "Unknown"
                    })
            except Exception as e:
                logger.error(f"Failed to query semantic email embeddings: {str(e)}")

        system_prompt = """You are CareerOS AI, a helpful, precise job application CRM assistant.
Answer the user's question directly, conversationally, and naturally using the provided context.

CRITICAL INSTRUCTION:
- You MUST wrap your final conversational reply to the user inside <reply> and </reply> XML wrappers.
- Do NOT include backticks, markdown code blocks, or the word 'tags' in your output. E.g., <reply>Hello! How can I help you today?</reply>
- Keep your tone friendly, helpful, conversational, and direct.
"""

        user_content = f"""[CONTEXT]
Job Application History:
{chr(10).join(apps_context) if apps_context else "No applications logged yet."}

Upcoming Scheduled Interviews:
{chr(10).join(interviews_context) if interviews_context else "No upcoming interviews scheduled."}

Relevant Email Conversations:
{chr(10).join(emails_context) if emails_context else "No relevant email transcripts found."}

[QUERY]
{question}
"""

        try:
            # Use Gemma 4 API with system instruction isolated from user query context
            model = AIEngineService.get_model(system_instruction=system_prompt)
            response = model.generate_content(
                user_content,
                generation_config=genai.GenerationConfig(
                    temperature=0.1
                )
            )
            
            text_response = ""
            try:
                if response.candidates and len(response.candidates) > 0:
                    candidate = response.candidates[0]
                    if candidate.content and candidate.content.parts:
                        text_response = "".join([part.text for part in candidate.content.parts if part.text]).strip()
            except Exception:
                pass
                
            if not text_response:
                try:
                    text_response = response.text.strip()
                except Exception:
                    text_response = "I received a blocked or empty response from the Gemma 4 API. Please try a different query."

            # Robust XML tag extraction: extract everything inside/after the last <reply> or <response> tag
            text_response = text_response.strip()
            
            if "<reply>" in text_response:
                text_response = text_response.rsplit("<reply>", 1)[1]
                if "</reply>" in text_response:
                    text_response = text_response.split("</reply>", 1)[0]
            elif "<response>" in text_response:
                text_response = text_response.rsplit("<response>", 1)[1]
                if "</response>" in text_response:
                    text_response = text_response.split("</response>", 1)[0]
            
            # Post-parsing cleanup: remove leftover backticks, tags prefixes, or rule lists
            text_response = text_response.replace("`tags.", "").replace("`tags", "")
            text_response = text_response.replace("tags.", "").replace("tags:", "")
            text_response = text_response.replace("`", "").strip()
            
            # If the response starts with bullet lists about rules, strip them
            if text_response.startswith("*") or text_response.startswith("-"):
                # Clean up any leftover list-item notes in the beginning
                lines = text_response.split("\n")
                filtered_lines = [l for l in lines if not any(x in l.lower() for x in ["markdown", "backtick", "xml wrapper", "reply tag"])]
                text_response = "\n".join(filtered_lines).strip()

            return {
                "response": text_response,
                "referenced_emails": referenced_emails
            }
        except Exception as e:
            logger.error(f"Failed to generate RAG response: {str(e)}")
            return {
                "response": "I'm sorry, I encountered an issue accessing my AI engine to answer your query. Please check your API key configurations.",
                "referenced_emails": []
            }
