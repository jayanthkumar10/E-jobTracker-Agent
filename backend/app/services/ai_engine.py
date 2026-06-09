import google.generativeai as genai
from pydantic import BaseModel, Field
from typing import Optional, List
import json
import logging
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# Configure Google GenAI SDK (as fallback or for embeddings)
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)

class JobExtractionSchema(BaseModel):
    company_name: str = Field(description="The name of the hiring company. Correct spelling and casing.")
    job_title: str = Field(description="The official job role title. E.g., 'Backend Engineer'.")
    recruiter_name: Optional[str] = Field(None, description="The name of the recruiter or sender if mentioned, otherwise null.")
    recruiter_email: Optional[str] = Field(None, description="The email address of the recruiter or sender, otherwise null.")
    status: str = Field(description="Must be exactly one of: 'APPLIED', 'SCREENING', 'INTERVIEWING', 'OFFERED', 'REJECTED', 'WITHDRAWN'.")
    stage: Optional[str] = Field(None, description="Specific interview stage if mentioned.")
    salary: Optional[str] = Field(None, description="Salary or compensation figures if mentioned.")
    location: Optional[str] = Field(None, description="Location of the job.")
    work_mode: Optional[str] = Field(None, description="Must be exactly one of: 'REMOTE', 'HYBRID', 'ONSITE', or null.")
    next_action: Optional[str] = Field(None, description="Suggested next action for the candidate.")
    source: Optional[str] = Field(None, description="The source platform where the application was submitted. E.g. 'LinkedIn', 'Indeed', 'Naukri', 'Direct' or name of company website.")
    is_actual_submission_confirmation: bool = Field(False, description="True ONLY if the email explicitly confirms that the application was submitted or received. False if it is just a job search recommendations alert, outreach, or advertisement.")


class AIEngineService:
    @staticmethod
    def get_model(model_name: str = "models/gemma-4-31b-it", system_instruction: Optional[str] = None):
        """Instantiates the Gemma model via Google AI Studio."""
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY environment variable is not configured.")
        return genai.GenerativeModel(model_name, system_instruction=system_instruction)

    @classmethod
    def extract_job_details(cls, email_body: str, subject: str, sender_email: str = "") -> Optional[JobExtractionSchema]:
        """
        Extracts structured job application details using cloud Gemma 4.
        """
        prompt = f"""
        Analyze the following email subject line and body to extract job application tracking info.
        Return raw JSON matching this schema:
        {{
            "company_name": "...",
            "job_title": "...",
            "recruiter_name": "..." or null,
            "recruiter_email": "..." or null,
            "status": "APPLIED" or "SCREENING" or "INTERVIEWING" or "OFFERED" or "REJECTED" or "WITHDRAWN",
            "stage": "..." or null,
            "salary": "..." or null,
            "location": "..." or null,
            "work_mode": "REMOTE" or "HYBRID" or "ONSITE" or null,
            "next_action": "..." or null,
            "source": "LinkedIn" or "Indeed" or "Naukri" or "Direct" or other specific portal,
            "is_actual_submission_confirmation": true or false
        }}

        Guidelines for "is_actual_submission_confirmation":
        - Set to true ONLY if the email is a direct confirmation that an application has been submitted, received, or processed.
        - Set to false if this is just a general job alert recommendation, marketing pitch, newsletter, or premium advertisement.

        Email Subject: {subject}
        Email Body:
        {email_body}
        """

        try:
            model = cls.get_model()
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                )
            )
            
            text_content = ""
            try:
                if response.candidates and len(response.candidates) > 0:
                    candidate = response.candidates[0]
                    if candidate.content and candidate.content.parts:
                        text_content = "".join([part.text for part in candidate.content.parts if part.text]).strip()
            except Exception:
                pass
                
            if not text_content:
                try:
                    text_content = response.text.strip()
                except Exception:
                    pass
                
            # Robust JSON extraction using JSONDecoder to ignore preambles and trailing content
            start_idx = text_content.find('{')
            if start_idx != -1:
                data, _ = json.JSONDecoder().raw_decode(text_content[start_idx:])
            else:
                data = json.loads(text_content)
                
            # Heuristics to override or infer source from sender_email, subject, or body
            sender_lower = (sender_email or "").lower()
            subject_lower = (subject or "").lower()
            body_lower = (email_body or "").lower()
            
            inferred_source = data.get("source") or "Direct"
            if "linkedin" in sender_lower or "linkedin" in subject_lower or "linkedin" in body_lower:
                inferred_source = "LinkedIn"
            elif "indeed" in sender_lower or "indeed" in subject_lower or "indeed" in body_lower:
                inferred_source = "Indeed"
            elif "naukri" in sender_lower or "naukri" in subject_lower or "naukri" in body_lower:
                inferred_source = "Naukri"
            elif "smartrecruiters" in sender_lower or "smartrecruiters" in subject_lower:
                inferred_source = "SmartRecruiters"
            elif "glassdoor" in sender_lower or "glassdoor" in subject_lower or "glassdoor" in body_lower:
                inferred_source = "Glassdoor"
                
            data["source"] = inferred_source
            
            return JobExtractionSchema(**data)
        except Exception as e:
            logger.error(f"Error parsing email with cloud Gemma 4 API: {str(e)}")
            return None

    @classmethod
    def generate_embedding(cls, text: str) -> Optional[List[float]]:
        """
        Generates 768-dimensional vector embedding for semantic search.
        Uses Google's gemini-embedding-001 model with 768-dim output.
        """
        if not text:
            return None
        try:
            result = genai.embed_content(
                model="models/gemini-embedding-001",
                content=text,
                task_type="retrieval_document",
                output_dimensionality=768
            )
            return result.get("embedding", [])
        except Exception as e:
            logger.error(f"Error generating text embedding: {str(e)}")
            return None

