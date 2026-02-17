"""Planning tools — analyze requirements, design solutions, validate plans."""
from __future__ import annotations
from typing import Any


async def odoo_analyze_requirements(description: str) -> dict[str, Any]:
    """Analyze a business description and return structured Odoo requirements.

    Uses keyword matching against the knowledge base to identify:
    - Matching industry blueprint
    - Needed Odoo modules (with reasons)
    - Custom requirements (fields, automations, reports)
    - Infrastructure needs (multi-company, website, delivery)
    - Questions for the user to clarify gaps
    """
    from odooforge.planning.requirement_parser import analyze_requirements
    return analyze_requirements(description)


async def odoo_design_solution(
    requirements: dict[str, Any],
    user_answers: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Turn analyzed requirements into a phased execution plan.

    Takes output from odoo_analyze_requirements plus optional user answers
    to clarifying questions. Returns a DAG of phases with tool calls.
    """
    from odooforge.planning.solution_designer import design_solution
    return design_solution(requirements, user_answers)


async def odoo_validate_plan(plan: dict[str, Any]) -> dict[str, Any]:
    """Validate an execution plan before running it.

    Checks module compatibility, field naming, dependency ordering,
    and safety (snapshot presence). Returns pass/warning/fail for each check.
    """
    from odooforge.planning.plan_validator import validate_plan
    return validate_plan(plan)
