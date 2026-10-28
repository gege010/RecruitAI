"""
Resume Parser — PDF → structured candidate profile.

Pipeline:
  1. pdfplumber  → extract text (with layout preservation)
  2. PyMuPDF     → fallback text extraction
  3. pytesseract → OCR fallback for image-only PDFs
  4. Groq LLM   → parse structured JSON from raw text
  5. Pydantic    → validate & normalise the output schema
"""
from __future__ import annotations

import json
import re
from typing import Any

import pdfplumber
import io

try:
    import fitz  # PyMuPDF
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

try:
    import base64
    from PIL import Image as _PILImage
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

from groq import Groq
from loguru import logger
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import GROQ_API_KEY, GROQ_MODEL, GROQ_VISION_MODEL


# ── Output Schema ─────────────────────────────────────────────────────────────

class EducationEntry(BaseModel):
    degree: str = ""
    field: str = ""
    institution: str = ""
    gpa: float | None = None
    graduation_year: int | None = None


class ExperienceEntry(BaseModel):
    title: str = ""
    company: str = ""
    duration_months: int = 0
    description: str = ""
    is_current: bool = False


class CandidateProfile(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    education: list[EducationEntry] = Field(default_factory=list)
    experience: list[ExperienceEntry] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    summary: str = ""


# ── PDF Text Extraction ───────────────────────────────────────────────────────

def _extract_with_pdfplumber(pdf_bytes: bytes) -> str:
    """Primary extraction: pdfplumber with layout-aware text."""
    text_parts = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            # Try words-based extraction first (better layout)
            words = page.extract_words(x_tolerance=3, y_tolerance=3, keep_blank_chars=False)
            if words:
                # Reconstruct text preserving line breaks
                lines: dict[float, list[str]] = {}
                for w in words:
                    y_key = round(w["top"], 0)
                    lines.setdefault(y_key, []).append(w["text"])
                for y in sorted(lines.keys()):
                    text_parts.append(" ".join(lines[y]))
            else:
                # Fallback to simple text
                t = page.extract_text()
                if t:
                    text_parts.append(t)
    return "\n".join(text_parts).strip()


def _extract_with_pymupdf(pdf_bytes: bytes) -> str:
    """Fallback extraction using PyMuPDF (better for complex layouts)."""
    if not HAS_FITZ:
        return ""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text_parts = []
    for page in doc:
        text = page.get_text("text")  # type: ignore
        if text.strip():
            text_parts.append(text)
    doc.close()
    return "\n".join(text_parts).strip()


def _extract_with_groq_vision(pdf_bytes: bytes) -> str:
    """
    OCR fallback using Groq Vision API.
    Renders each PDF page as a PNG image and sends to Groq vision model.
    Works for scanned/image-based PDFs without any external binary.
    """
    if not HAS_FITZ:
        logger.warning("PyMuPDF not available for Groq Vision OCR")
        return ""

    import base64

    try:
        client = Groq(api_key=GROQ_API_KEY)
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        all_text_parts = []

        # Process max 4 pages to stay within token limits
        max_pages = min(len(doc), 4)

        for page_num in range(max_pages):
            page = doc[page_num]
            # Render at 200 DPI (balance quality vs size)
            mat = fitz.Matrix(200 / 72, 200 / 72)
            pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
            img_bytes = pix.tobytes("png")
            img_b64 = base64.b64encode(img_bytes).decode("utf-8")

            resp = client.chat.completions.create(
                model=GROQ_VISION_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{img_b64}"},
                            },
                            {
                                "type": "text",
                                "text": (
                                    "This is page of a resume/CV. "
                                    "Extract ALL text exactly as it appears. "
                                    "Preserve names, dates, job titles, skills, education, contact info. "
                                    "Output only the extracted text, nothing else."
                                ),
                            },
                        ],
                    }
                ],
                max_tokens=2048,
                temperature=0.0,
            )
            page_text = resp.choices[0].message.content or ""
            if page_text.strip():
                all_text_parts.append(page_text.strip())

        doc.close()
        return "\n\n".join(all_text_parts)

    except Exception as exc:
        logger.error("Groq Vision OCR failed: {}", exc)
        return ""


def extract_text_from_pdf(pdf_bytes: bytes) -> tuple[str, str]:
    """
    Multi-strategy PDF text extraction.

    Returns:
        (extracted_text, method_used)
    """
    # Strategy 1: pdfplumber (best for text-based PDFs)
    text = _extract_with_pdfplumber(pdf_bytes)
    if text and len(text) > 100:
        logger.debug("PDF extracted via pdfplumber ({} chars)", len(text))
        return text, "pdfplumber"

    # Strategy 2: PyMuPDF (better for complex layouts / mixed content)
    text = _extract_with_pymupdf(pdf_bytes)
    if text and len(text) > 100:
        logger.debug("PDF extracted via PyMuPDF ({} chars)", len(text))
        return text, "pymupdf"

    # Strategy 3: Groq Vision OCR (for scanned / image-based PDFs)
    logger.warning("Text extraction yielded minimal text — attempting Groq Vision OCR...")
    text = _extract_with_groq_vision(pdf_bytes)
    if text and len(text) > 50:
        logger.info("PDF extracted via Groq Vision OCR ({} chars)", len(text))
        return text, "groq_vision"

    return text or "", "failed"


# ── LLM Extraction ────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """You are an expert resume parser for Indonesian and international candidates.
Your job is to carefully read the resume text and extract ALL information accurately.

Return ONLY a valid JSON object with NO additional text, following this exact schema:
{
  "name": "full name of candidate",
  "email": "email address",
  "phone": "phone number",
  "location": "city, country",
  "summary": "professional summary or objective (2-3 sentences)",
  "education": [
    {
      "degree": "e.g. Bachelor, S1, S2, Master, PhD, D3",
      "field": "e.g. Computer Science, Teknik Informatika",
      "institution": "university name",
      "gpa": null or float like 3.75,
      "graduation_year": null or integer year
    }
  ],
  "experience": [
    {
      "title": "job title",
      "company": "company name",
      "duration_months": integer (estimate from date range, e.g. Jan 2022 - Dec 2023 = 24),
      "description": "key responsibilities and achievements",
      "is_current": true or false
    }
  ],
  "skills": ["skill1", "skill2", ...],
  "certifications": ["cert1", "cert2", ...],
  "languages": ["Indonesian", "English", ...]
}

IMPORTANT RULES:
- Extract EVERY skill mentioned anywhere in the resume (technical skills, soft skills, tools, frameworks)
- For duration_months: if date range given, calculate accurately. If "2 years" mentioned, use 24.
- For Indonesian resumes: S1=Bachelor, S2=Master, S3=PhD, D3=Diploma
- Extract ALL certifications and training courses
- Skills should be individual items (not sentences)
- If information not found, use empty string "" or empty list []
- Return ONLY the JSON object, absolutely nothing else"""


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _call_groq(raw_text: str) -> str:
    client = Groq(api_key=GROQ_API_KEY)

    # Truncate intelligently: keep first 8000 chars (covers most resumes)
    text_to_send = raw_text[:8000] if len(raw_text) > 8000 else raw_text

    resp = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": f"Parse this resume carefully and extract ALL information:\n\n{text_to_send}"},
        ],
        temperature=0.05,   # Very low temperature for deterministic extraction
        max_tokens=4096,    # Larger output for detailed profiles
    )
    return resp.choices[0].message.content


def _clean_json_response(raw: str) -> str:
    """Strip markdown code fences and extract JSON block."""
    raw = raw.strip()
    # Remove ```json ... ``` or ``` ... ```
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    # If there's extra text before {, find the JSON object
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        raw = match.group(0)
    return raw.strip()


def _postprocess_profile(profile: CandidateProfile) -> CandidateProfile:
    """Clean up and normalise extracted profile data."""
    # Deduplicate skills
    seen = set()
    clean_skills = []
    for s in profile.skills:
        s_clean = s.strip()
        if s_clean and s_clean.lower() not in seen and len(s_clean) > 1:
            seen.add(s_clean.lower())
            clean_skills.append(s_clean)
    profile.skills = clean_skills

    # Clean certifications
    profile.certifications = [c.strip() for c in profile.certifications if c.strip() and len(c.strip()) > 2]

    # Normalise languages
    profile.languages = [l.strip().title() for l in profile.languages if l.strip()]

    # Ensure reasonable duration_months (cap at 480 months = 40 years)
    for exp in profile.experience:
        if exp.duration_months > 480:
            exp.duration_months = 480
        if exp.duration_months < 0:
            exp.duration_months = 0

    return profile


# ── Public API ────────────────────────────────────────────────────────────────

def parse_resume(pdf_bytes: bytes, filename: str = "resume.pdf") -> tuple[str, CandidateProfile, str]:
    """
    Full resume parsing pipeline.

    Returns:
        (raw_text, CandidateProfile, extraction_method)
    """
    logger.info("Parsing resume: {}", filename)

    # Step 1: Extract text using best available strategy
    raw_text, method = extract_text_from_pdf(pdf_bytes)

    if not raw_text or len(raw_text) < 30:
        logger.warning("Insufficient text extracted from {} (method: {})", filename, method)
        return raw_text or "", CandidateProfile(), method

    logger.debug("Extracted {} chars from {} via {}", len(raw_text), filename, method)

    # Step 2: LLM structured extraction
    try:
        llm_output = _call_groq(raw_text)
        json_str = _clean_json_response(llm_output)
        data: dict[str, Any] = json.loads(json_str)
    except json.JSONDecodeError as exc:
        logger.error("JSON parse error for {}: {} | raw: {}", filename, exc, llm_output[:300])
        return raw_text, CandidateProfile(), method
    except Exception as exc:
        logger.error("LLM call failed for {}: {}", filename, exc)
        return raw_text, CandidateProfile(), method

    # Step 3: Validate schema
    try:
        profile = CandidateProfile(**data)
        profile = _postprocess_profile(profile)
    except Exception as exc:
        logger.warning("Profile validation warning for {}: {}", filename, exc)
        # Try partial construction
        try:
            safe_data = {k: v for k, v in data.items() if k in CandidateProfile.model_fields}
            profile = CandidateProfile(**safe_data)
        except Exception:
            profile = CandidateProfile()

    logger.info(
        "Parsed '{}' [{}] — name={}, skills={}, exp_entries={}, edu_entries={}",
        filename, method,
        profile.name or "?",
        len(profile.skills),
        len(profile.experience),
        len(profile.education),
    )
    return raw_text, profile, method
