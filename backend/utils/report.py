"""
AI Clinical Report Generator
Uses Anthropic Claude API to generate detailed clinical reports
based on model predictions.
"""

import os
import json
import httpx
from typing import Optional


ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

CMVD_SYSTEM_PROMPT = """You are a senior cardiologist specializing in coronary microvascular dysfunction (CMVD).
Generate a concise clinical report based on AI model analysis of an ECG image.
Structure: Brief Summary | Key Findings | Clinical Interpretation | Next Steps
Keep it professional, evidence-based, and under 300 words."""

RICKETS_SYSTEM_PROMPT = """You are a pediatric radiologist and endocrinologist specializing in metabolic bone disease.
Generate a concise clinical report based on AI model analysis of a pediatric X-ray.
Structure: Brief Summary | Radiological Findings | Metabolic Assessment | Treatment Plan
Keep it professional, evidence-based, and under 300 words."""


async def generate_ai_report(model_type: str, result: dict) -> Optional[str]:
    """
    Generate a clinical AI report using Claude.
    Falls back gracefully if API key not set.
    """
    if not ANTHROPIC_API_KEY:
        return _generate_template_report(model_type, result)

    system_prompt = CMVD_SYSTEM_PROMPT if model_type == "cmvd" else RICKETS_SYSTEM_PROMPT

    user_message = f"""
AI Model Analysis Results:
{json.dumps(result, indent=2)}

Please generate a clinical report for this patient based on these AI findings.
Note: This is AI-assisted analysis and should be reviewed by a qualified clinician.
"""

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 500,
                    "system": system_prompt,
                    "messages": [{"role": "user", "content": user_message}],
                },
            )
            data = response.json()
            if "content" in data and data["content"]:
                return data["content"][0]["text"]
    except Exception as e:
        print(f"Claude API error: {e}")

    return _generate_template_report(model_type, result)


def _generate_template_report(model_type: str, result: dict) -> str:
    """Fallback template-based report when API is unavailable"""
    if model_type == "cmvd":
        pred = result.get("prediction", "Unknown")
        conf = result.get("confidence", 0)
        severity = result.get("severity", "Unknown")
        indicators = result.get("ecg_indicators", [])
        rec = result.get("recommendation", "")

        return f"""
CLINICAL REPORT — CMVD ECG ANALYSIS
=====================================
AI Prediction: {pred} (Confidence: {conf:.1f}%)
Severity: {severity}

ECG Findings:
{chr(10).join(f'• {i}' for i in indicators)}

Recommendation:
{rec}

⚠️ This report is AI-generated and requires clinical validation by a qualified cardiologist.
        """.strip()

    else:
        pred = result.get("prediction", "Unknown")
        conf = result.get("confidence", 0)
        density = result.get("bone_density_score", 0)
        findings = result.get("xray_findings", [])
        treatment = result.get("treatment", "")
        urgency = result.get("urgency", "")

        return f"""
CLINICAL REPORT — NUTRITIONAL RICKETS X-RAY ANALYSIS
======================================================
AI Prediction: {pred} (Confidence: {conf:.1f}%)
Bone Density Score: {density:.1f}/100
Urgency: {urgency}

Radiological Findings:
{chr(10).join(f'• {f}' for f in findings)}

Estimated Lab Values:
{chr(10).join(f'• {k}: {v}' for k, v in result.get("lab_estimates", {}).items())}

Treatment Plan:
{treatment}

⚠️ This report is AI-generated and requires clinical validation by a qualified pediatric radiologist.
        """.strip()
