import os
import json
import logging
from typing import Optional, Tuple
from sqlalchemy.orm import Session
import google.generativeai as genai

from app.core.config import settings
from app.models.application import Application, ResumeTailoring
from app.models.user import User
from app.services.ai_engine import AIEngineService

logger = logging.getLogger(__name__)

DEFAULT_BASE_RESUME = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Jayanth Kumar Pillajetti - Resume</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: Arial, Helvetica, sans-serif; font-size: 11.5px; line-height: 1.45; color: #000000; background: #ffffff; width: 816px; margin: 0 auto; padding: 36px 48px 36px 48px; }
  .header-name { font-size: 20px; font-weight: bold; text-align: center; letter-spacing: 0.5px; margin-bottom: 3px; }
  .header-title { font-size: 11px; text-align: center; color: #333333; margin-bottom: 5px; }
  .header-contact { font-size: 10.5px; text-align: center; color: #000000; margin-bottom: 2px; }
  .header-contact a { color: #000000; text-decoration: none; }
  hr { border: none; border-top: 1.5px solid #000000; margin: 7px 0 5px 0; }
  .section { margin-bottom: 8px; }
  .section-title { font-size: 11.5px; font-weight: bold; text-transform: uppercase; letter-spacing: 0.8px; border-bottom: 1px solid #000000; padding-bottom: 1px; margin-bottom: 5px; color: #000000; }
  .entry { margin-bottom: 6px; }
  .title-row { display: flex; justify-content: space-between; align-items: baseline; font-weight: bold; font-size: 11.5px; }
  .subtitle-row { display: flex; justify-content: space-between; align-items: baseline; font-size: 10.5px; color: #222222; margin-bottom: 3px; font-style: italic; }
  ul { margin: 2px 0 0 16px; padding: 0; }
  li { margin-bottom: 2px; font-size: 11px; line-height: 1.42; }
  .summary-text { font-size: 11px; line-height: 1.5; text-align: justify; }
  .skills-row { font-size: 11px; margin-bottom: 2px; line-height: 1.4; }
  .skills-row b { font-weight: bold; }
  @media print { body { padding: 28px 44px; width: 100%; } @page { margin: 0; size: A4; } }
</style>
</head>
<body>

<div class="header-name">JAYANTH KUMAR PILLAJETTI</div>
<div class="header-title">AI Agent Engineer | LLM Systems | Multi-Agent Orchestration | RAG Pipelines</div>
<div class="header-contact">Mumbai, India &nbsp;|&nbsp; +91 91339 85109 &nbsp;|&nbsp; pillajettijayanth@gmail.com &nbsp;|&nbsp; linkedin.com/in/jayanth-kumar &nbsp;|&nbsp; github.com/jayanth-kumar</div>

<hr>

<div class="section">
  <div class="section-title">Summary</div>
  <p class="summary-text">AI Systems Engineer with 1.5+ years of experience specializing in building agentic workflows and LLM orchestration. Designed and scaled production AI automation solutions with LangGraph, n8n, and Retrieval-Augmented Generation (RAG) to drive business efficiency.</p>
</div>

<div class="section">
  <div class="section-title">Technical Skills</div>
  <div class="skills-row"><b>Languages &amp; Tools:</b> Python, SQL, PL/SQL, REST APIs, Git, Docker</div>
  <div class="skills-row"><b>LLM &amp; AI Frameworks:</b> LangChain, LangGraph, Hugging Face Transformers, Prompt Engineering, Multi-Agent Orchestration, RAG, Agentic AI Workflows</div>
  <div class="skills-row"><b>AI APIs &amp; Platforms:</b> OpenAI API, Google Gemini API, WhatsApp Business API (Meta), FAISS, n8n Automation, Apify</div>
  <div class="skills-row"><b>Machine Learning:</b> Scikit-learn, NumPy, Pandas, Supervised Learning, Feature Engineering, NLP</div>
  <div class="skills-row"><b>Deployment &amp; Cloud:</b> Azure, Docker, CI/CD Fundamentals</div>
</div>

<div class="section">
  <div class="section-title">Experience</div>
  <div class="entry">
    <div class="title-row"><span>Associate System Engineer — AI &amp; Intelligent Systems</span><span>Apr 2024 – Present</span></div>
    <div class="subtitle-row"><span>Tata Consultancy Services (TCS)</span><span>Mumbai, India</span></div>
    <ul>
      <li>Engineered and deployed multi-agent LLM workflows to automate business operations, reducing processing times by 40%.</li>
      <li>Designed enterprise-grade Retrieval-Augmented Generation (RAG) pipelines for semantic document search.</li>
      <li>Integrated REST APIs and external databases to synchronize CRM records and message flows.</li>
      <li>Optimized prompts and system instructions across Gemini and OpenAI models for high-accuracy outputs.</li>
    </ul>
  </div>
</div>

<div class="section">
  <div class="section-title">Projects</div>
  <div class="entry">
    <div class="title-row"><span>Autonomous AI Job Hunter — Multi-Agent LLM Pipeline</span><span></span></div>
    <div class="subtitle-row"><span>Python, LangGraph, LangChain, RAG, FAISS, n8n, Google Gemini API, Apify</span></div>
    <ul>
      <li>Built a multi-agent AI pipeline in LangGraph to autonomously scrape, analyze, and apply to job matches.</li>
      <li>Implemented FAISS vector search database to parse resumes against target job descriptions.</li>
      <li>Automated data aggregation pipelines using Apify and n8n to sync workflow states.</li>
    </ul>
  </div>
  <div class="entry">
    <div class="title-row"><span>AI-Powered WhatsApp Doctor Appointment System</span><span></span></div>
    <div class="subtitle-row"><span>n8n, WhatsApp Business API (Meta), LLM, Google Sheets</span></div>
    <ul>
      <li>Designed a conversational AI assistant on WhatsApp for end-to-end medical scheduling.</li>
      <li>Constructed finite state machine (FSM) control logic to manage stateful slot-filling exchanges.</li>
      <li>Connected Meta Cloud API with Google Sheets backend to log schedules dynamically.</li>
    </ul>
  </div>
</div>

<div class="section">
  <div class="section-title">Achievements</div>
  <ul>
    <li><b>Published Patent:</b> Filed AI system patent focused on autonomous multi-agent systems optimization.</li>
    <li><b>Spot Award — TCS:</b> Recognized for outstanding contributions in automating legacy workflow processes.</li>
  </ul>
</div>

<div class="section">
  <div class="section-title">Education</div>
  <div class="entry">
    <div class="title-row"><span>B.Tech in Computer Science — AI &amp; Machine Learning Specialisation</span><span>Aug 2019 – May 2023</span></div>
    <div class="subtitle-row"><span>SRM University Andhra Pradesh</span><span>GPA: 8.2 / 10</span></div>
  </div>
</div>

</body>
</html>"""

class ResumeTailorService:

    @classmethod
    def relevance_check(cls, job_description: str) -> bool:
        """
        Uses Gemini to check if the job description is relevant to AI/GenAI/Workflows/Engineering roles.
        """
        prompt = f"""You are a strict rule-based job classifier.
Return ONLY one word:
true
or
false

No explanation. No punctuation. No extra text.

---

STEP 1 — EXPERIENCE FILTER (HIGHEST PRIORITY)
If the job description mentions:
* more than 3 years experience
→ return false immediately

---

STEP 2 — ROLE TYPE CHECK (PRIMARY DECISION)
Check what the job is MAINLY about.
Return true ONLY if the role is primarily (more than 50%):
* AI Engineer
* LLM Engineer
* Generative AI Developer
* Agentic AI / AI Agents
* RAG / vector database / embeddings
* Chatbot / Conversational AI
* AI automation (n8n, workflows, agents)

---

STEP 3 — HARD REJECTION RULES (OVERRIDE EVERYTHING)
Return false if the role is mainly:
* Backend / API / Microservices (without strong AI focus)
* DevOps / MLOps / Infrastructure / Kubernetes
* Data Engineering / ETL / Spark
* Data Analyst / BI / dashboards
* Banking systems / ERP / SAP / Salesforce
* Mobile / Frontend / Full Stack (without AI focus)

IMPORTANT:
If AI/GenAI is mentioned but NOT the core responsibility → return false

---

STEP 4 — SIMPLE FINAL CHECK
Ask yourself:
"Is this job mostly about building LLM or AI systems?"
YES → true
NO → false

---

JOB DESCRIPTION:
{job_description}
"""
        try:
            model = AIEngineService.get_model(model_name="models/gemini-2.5-flash")
            response = model.generate_content(prompt, generation_config=genai.GenerationConfig(temperature=0.0))
            ans = response.text.strip().lower()
            return "true" in ans
        except Exception as e:
            logger.error(f"Relevance check failed: {str(e)}")
            # Default to true so we don't block applications on model failure
            return True

    @classmethod
    def analyze_jd(cls, job_description: str, base_resume: str) -> Tuple[Optional[dict], str]:
        """
        Runs the JD Analyst Agent prompts to extract keyword guidelines, mirror titles, and generate summary hooks.
        """
        prompt = f"""You are a precision ATS analyst. Your output is consumed by an automated resume writer. Every field you produce will be used directly. Accuracy is critical.

Return ONLY a valid JSON object. No explanation. No markdown. No backticks. No text before or after the JSON.

---

CANDIDATE CONTEXT — calibrate all outputs against this profile:
{base_resume}

---

EXTRACT THIS EXACT JSON STRUCTURE:

{{
  "role_title": "exact job title from JD, no paraphrasing",
  "role_type": "pick exactly one: agentic_ai | llm_engineering | ai_automation | applied_ai | ai_adjacent_backend | data_science | other",
  "experience_required": "exact text from JD e.g. '2-4 years' — write not_specified if absent",
  "seniority_level": "junior | mid | senior | not_specified",
  "must_have_keywords": [
    "list of 8-12 skills and tools the JD explicitly requires",
    "copy the exact spelling and casing from the JD — ATS does exact string matching",
    "include both full names and abbreviations if JD uses both e.g. Retrieval-Augmented Generation and RAG"
  ],
  "nice_to_have_keywords": [
    "3-5 preferred or bonus skills stated in JD — exact JD phrasing"
  ],
  "candidate_has": [
    "must_have_keywords the candidate ALREADY HAS based on the stack listed above",
    "be strict — only list genuine matches, not adjacent skills"
  ],
  "candidate_needs_to_inject": [
    "must_have_keywords the candidate does NOT clearly have but could honestly claim based on adjacent experience",
    "these are the keywords the resume writer must weave in without fabricating"
  ],
  "candidate_cannot_claim": [
    "must_have_keywords the candidate genuinely lacks — resume writer must NOT use these"
  ],
  "responsibility_phrases": [
    "10 action phrases copied closely from the JD responsibilities section",
    "these will be embedded verbatim into resume bullets",
    "start each with the verb used in the JD e.g. Design, Build, Deploy, Optimize, Integrate"
  ],
  "ats_title_mirror": "the exact job title or closest variant the resume header should reflect — used to mirror title in summary line",
  "summary_hook": "one crisp sentence for line 1 of the resume summary — MUST name the role title AND reference one of: multi-agent pipeline / n8n automation / WhatsApp AI system / LLM orchestration — no generic filler",
  "summary_supporting_line": "one sentence for line 2 — mention 1.5 years experience, 2-3 must_have_keywords from candidate_has, and one concrete outcome from his projects",
  "keyword_placement_priority": "one sentence: which resume section needs the most keyword injection for this JD — be specific e.g. 'inject LangGraph and agent orchestration into TCS experience bullets'"
}}

---

JD:
{job_description}
"""
        try:
            model = AIEngineService.get_model(model_name="models/gemini-2.5-flash")
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )
            text = response.text.strip()
            
            # Robust JSON extracting in case the response still wraps with backticks
            start_idx = text.find('{')
            end_idx = text.rfind('}')
            if start_idx != -1 and end_idx != -1:
                json_str = text[start_idx:end_idx + 1]
            else:
                json_str = text
                
            data = json.loads(json_str)
            return data, json_str
        except Exception as e:
            logger.error(f"JD analysis failed: {str(e)}")
            return None, "{}"

    @classmethod
    def write_tailored_resume(cls, base_resume: str, analysis: dict) -> str:
        """
        Runs the Resume Writer Agent to customize the resume HTML with ATS keyword guidelines.
        """
        prompt = f"""You are a precision ATS resume engineer. Your job is keyword injection, impact framing, and value alignment — without fabricating a single fact.

You will receive two inputs:
1. CANDIDATE RESUME — the source of truth. Never invent facts not present here.
2. JD ANALYSIS — a JSON object from the JD Analyst. Every field in it is a direct instruction to you.

---

INPUTS:

CANDIDATE RESUME (source of truth — facts here cannot be changed):
{base_resume}

JD ANALYSIS (your operating instructions — parse every field before writing anything):
{json.dumps(analysis, indent=2)}

---

BEFORE YOU WRITE A SINGLE LINE OF HTML — complete this internal analysis:

STEP A — Parse the JD Analysis JSON. Extract these fields and hold them in working memory:
- role_title → used in header subtitle and summary line 1
- ats_title_mirror → the exact title string to mirror in the summary
- must_have_keywords → full list
- candidate_has → keywords already present in resume (these must appear verbatim in final resume)
- candidate_needs_to_inject → keywords to weave in honestly (these must appear at least once each)
- candidate_cannot_claim → do NOT use these anywhere
- responsibility_phrases → embed these into bullets
- summary_hook → line 1 of Summary section verbatim
- summary_supporting_line → line 2 of Summary section verbatim
- keyword_placement_priority → tells you which section to focus injection effort

STEP B — Keyword Injection Map. Before writing, mentally assign each keyword from candidate_needs_to_inject to a specific bullet or section where it fits naturally. If a keyword cannot fit honestly anywhere, skip it — never force it.

STEP C — ATS Exact-Match Rule. Keywords must appear with the exact spelling and casing from must_have_keywords. If the JD says "Retrieval-Augmented Generation" write that, not "RAG-based". If the JD says "LangChain" not "Langchain". Exact match beats paraphrase every time.

---

SECTION-BY-SECTION RULES:

HEADER SUBTITLE (div.header-title)
- Update the pipe-separated title line to mirror ats_title_mirror as the first item
- Keep remaining items relevant to the role type
- Example format: AI Agent Engineer | LLM Systems | Multi-Agent Orchestration | RAG Pipelines

SUMMARY (2-3 lines max, most critical section for ATS and recruiter)
- Line 1: Use summary_hook from JD Analysis verbatim
- Line 2: Use summary_supporting_line from JD Analysis verbatim  
- Line 3 (optional): One sentence — a specific measurable outcome or unique credential (patent, certification) relevant to this role
- Must contain at least 5 keywords from must_have_keywords
- Zero filler phrases: no "passionate about", "results-driven", "dynamic", "leveraging"

TECHNICAL SKILLS
- Keep every skill the candidate genuinely has
- Add keywords from candidate_needs_to_inject that are tools or technologies — place them in the most relevant existing category
- Do NOT add keywords from candidate_cannot_claim
- Do NOT create new skill categories — use the existing ones
- List keywords exactly as they appear in must_have_keywords for ATS matching

EXPERIENCE BULLETS (TCS role — 4 bullets)
- Every bullet format: [Strong past-tense verb] + [what was built/done, name the technology] + [measurable outcome or scale]
- Weave responsibility_phrases from JD Analysis into bullets where the underlying work actually matches
- Inject candidate_needs_to_inject keywords here if keyword_placement_priority points to experience
- Do NOT change the company name, job title, dates, or location
- Do NOT fabricate metrics — if a number exists in the source resume, use it; if not, describe scope or scale instead (e.g. "across 3 enterprise clients", "processing 500+ daily transactions")

PROJECT BULLETS (3 bullets per project, keep both projects)
- Same bullet format as experience
- Project 1 (AI Job Hunter): emphasise multi-agent architecture, LLM orchestration, RAG pipeline
- Project 2 (WhatsApp Doctor System): emphasise conversational AI, FSM design, API integration, production automation
- Inject remaining candidate_needs_to_inject keywords here
- Update the tech stack line under each project title to include relevant must_have_keywords the candidate has

ACHIEVEMENTS
- Patent: frame it using language from the JD domain
- Spot Award: frame it around a deliverable that mirrors a responsibility_phrase from the JD

EDUCATION
- Keep exactly as-is, no changes

---

ATS LOOPHOLES TO EXPLOIT (these are legitimate and widely used):
1. TITLE MIRRORING — if the JD title is "AI Agent Engineer", your summary line 1 and header subtitle must contain "AI Agent Engineer" exactly.
2. KEYWORD DENSITY RULE — each must_have_keyword should appear 1-2 times across the full resume. Once in skills, once in a bullet. Never 3+ times.
3. VERB-KEYWORD FUSION — combine JD responsibility verbs with the candidate's actual work: "Designed and deployed multi-agent LLM workflows" scores higher than "Built AI systems".
4. SKILLS SECTION AS KEYWORD RESERVOIR — ATS parsers weight the skills section heavily.
5. CONTEXT WRAPPING — when injecting a keyword the candidate needs to add, wrap it in a credible context.
6. RECENCY SIGNAL — bullets describing the most recent work (TCS role) carry more ATS weight.

---

ONE PAGE ENFORCEMENT:
- Target: content must render within 816px width, approximately 1050px total height
- If over length: tighten bullets by removing filler words
- Never go below 10px font
- Do NOT use ** for bold anywhere — the template CSS handles all formatting

---

OUTPUT RULES — non-negotiable:
- Output begins exactly with <!DOCTYPE html> — no characters before it
- Output ends with </html> — no characters after it
- No markdown, no backticks, no explanation, no commentary
- Do NOT modify any CSS, class names, IDs, or HTML structure
- Do NOT use ** anywhere — CSS handles all bold formatting
"""
        try:
            model = AIEngineService.get_model(model_name="models/gemini-2.5-flash")
            response = model.generate_content(prompt, generation_config=genai.GenerationConfig(temperature=0.1))
            text = response.text.strip()
            
            # Robust HTML extraction
            start_idx = text.find('<!DOCTYPE html>')
            if start_idx == -1:
                start_idx = text.find('<html')
            
            end_idx = text.rfind('</html>')
            
            if start_idx != -1 and end_idx != -1:
                html_out = text[start_idx:end_idx + 7]
            else:
                html_out = text
                
            return html_out
        except Exception as e:
            logger.error(f"Tailoring resume HTML failed: {str(e)}")
            # Fallback to base resume HTML
            return base_resume

    @classmethod
    def tailor_application(
        cls,
        db: Session,
        user_id: str,
        job_title: str,
        company_name: str,
        job_description: str,
        job_url: Optional[str] = None
    ) -> Application:
        """
        Orchestrates the entire single-job tailoring workflow:
        1. Fetches base resume from user profile (falls back to DEFAULT_BASE_RESUME)
        2. Conducts JD Analysis
        3. Generates tailored HTML resume
        4. Saves the HTML static file
        5. Logs the Application in state 'TAILORED' (new state)
        """
        # Fetch user
        user = db.query(User).filter(User.id == user_id).first()
        base_resume = user.base_resume if (user and user.base_resume) else DEFAULT_BASE_RESUME
        
        # Analyze JD
        analysis, analysis_json = cls.analyze_jd(job_description, base_resume)
        
        # Write resume
        tailored_html = cls.write_tailored_resume(base_resume, analysis or {})
        
        # Create static resumes folder
        static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../static/resumes"))
        os.makedirs(static_dir, exist_ok=True)
        
        # Create Application record
        # Infer location, salary range from JD analysis if available
        location = "N/A"
        salary = "N/A"
        if analysis:
            location = analysis.get("location") or "N/A"
            salary = analysis.get("salary") or "N/A"
            
        app = Application(
            user_id=user_id,
            company_name=company_name,
            job_title=job_title,
            status="TAILORED",  # New status: tailored but not yet applied
            location=location if location != "N/A" else None,
            salary_range=salary if salary != "N/A" else None,
            application_url=job_url,
            job_description=job_description,
            ats_match_details=analysis_json,
            source="LinkedIn" if "linkedin.com" in (job_url or "").lower() else "Direct"
        )
        db.add(app)
        db.commit()
        db.refresh(app)
        
        # Save HTML file locally named: {user_id}_{app_id}.html
        file_name = f"{user_id}_{app.id}.html"
        file_path = os.path.join(static_dir, file_name)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(tailored_html)
            
        # Update application with public tailored resume link
        app.tailored_resume_url = f"/static/resumes/{file_name}"
        db.commit()
        db.refresh(app)
        
        return app
