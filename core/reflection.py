"""
Reflection module — Senior Analyst review node.

Reviews the junior analyst's report for contradictions, hallucinations,
and math errors. Supports up to MAX_REVISIONS cyclical loops.
"""

from .llm import review_report

MAX_REVISIONS = 2


def reflect(report: dict, financials: dict, revision_count: int, mode: str = "deep") -> dict:
    """
    Run the Senior Analyst reflection check.

    Returns:
        {
            "approved": bool,
            "issues_found": [...],
            "corrections": [...],
            "feedback": str,
            "revision_count": int,
            "max_reached": bool,
        }
    """
    if revision_count >= MAX_REVISIONS:
        return {
            "approved": True,
            "issues_found": [],
            "corrections": [],
            "feedback": f"Max revision cycles ({MAX_REVISIONS}) reached. Approving with caveats.",
            "revision_count": revision_count,
            "max_reached": True,
        }

    try:
        result = review_report(report, financials, mode=mode)
    except Exception as e:
        # If the review itself fails, approve to avoid blocking the pipeline
        return {
            "approved": True,
            "issues_found": [f"Review failed: {e}"],
            "corrections": [],
            "feedback": "Senior analyst review encountered an error; approving with caution.",
            "revision_count": revision_count,
            "max_reached": False,
        }

    result["revision_count"] = revision_count + 1
    result["max_reached"] = False
    return result
