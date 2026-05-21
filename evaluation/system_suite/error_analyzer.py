"""
error_analyzer.py — Thesis-grade error categorization and diagnostics.

Analyzes trace data from the evaluation runner and produces:
  - Categorized errors with specific descriptions (not generic copy-paste)
  - Severity levels (CRITICAL, MODERATE, LOW)
  - Suggested fixes / system limitation statements
  - Summary statistics by error type
"""
import json
from typing import Dict, Any, List


# ─── Error Type Definitions ────────────────────────────────────────────────────

ERROR_TYPES = {
    "ROUTING_AMBIGUITY": {
        "severity": "MODERATE",
        "thesis_implication": "LLM-based intent classification has inherent ambiguity with certain phrasings.",
    },
    "STAT_MISMATCH": {
        "severity": "MODERATE",
        "thesis_implication": "The LLM Arbiter occasionally assigns incorrect stats for creative stunts.",
    },
    "SCHEMA_VIOLATION": {
        "severity": "CRITICAL",
        "thesis_implication": "The LLM Cartographer can produce structurally invalid quest graphs.",
    },
    "ENGINE_SYNC_FAILURE": {
        "severity": "CRITICAL",
        "thesis_implication": "A deterministic Python rule was violated — this indicates a code-level bug.",
    },
    "NARRATIVE_FAILURE": {
        "severity": "LOW",
        "thesis_implication": "The DM Narrator failed to generate coherent output — cosmetic issue.",
    },
    "DENIAL_FAILURE": {
        "severity": "CRITICAL",
        "thesis_implication": "The system failed to block an action that should have been denied.",
    },
}


def categorize_error(scenario: dict, trace: dict, metrics: dict) -> dict:
    """
    Categorizes a single failed scenario with specific diagnostic information.
    Returns a dict with error_type, severity, description, and suggested_fix.
    """
    cat = scenario.get("category", "")
    sid = scenario.get("id", "")
    user_input = scenario.get("input", "")
    intent_router = trace.get("intent_router", {})
    predicted = intent_router.get("predicted_path", "UNKNOWN")

    # ── Routing Error ──────────────────────────────────────────────
    if not metrics.get("routing_correct", False):
        expected = scenario.get("expected_type", scenario.get("expected_system_check", "UNKNOWN"))
        return {
            "error_type": "ROUTING_AMBIGUITY",
            "severity": "MODERATE",
            "description": (
                f"Router classified '{user_input}' as {predicted} "
                f"instead of expected {expected}. "
                f"The phrasing may be ambiguous between combat and exploration contexts."
            ),
            "suggested_fix": (
                f"Add more training examples or regex patterns for '{expected}' intent. "
                f"Consider adding '{user_input[:30]}...' as a disambiguation rule."
            ),
        }

    # ── Grounding Error ────────────────────────────────────────────
    if not metrics.get("grounding_correct", False):
        arbiter = trace.get("action_arbiter", {})

        if "Quest" in cat:
            return {
                "error_type": "SCHEMA_VIOLATION",
                "severity": "CRITICAL",
                "description": (
                    f"Quest schema validation failed for {sid}. "
                    f"The Cartographer produced invalid structure. "
                    f"Output: {trace.get('system_check_output', 'unknown')}"
                ),
                "suggested_fix": "Tighten the Cartographer prompt constraints or add post-generation repair logic.",
            }

        if scenario.get("expected_allowed") is False:
            returned = arbiter.get("enum_returned", "UNKNOWN")
            return {
                "error_type": "DENIAL_FAILURE",
                "severity": "CRITICAL",
                "description": (
                    f"The Arbiter should have DISALLOWED '{user_input}' "
                    f"but returned '{returned}' instead. "
                    f"The LLM failed to recognize this as an impossible action."
                ),
                "suggested_fix": "Add stronger guardrail examples in the Arbiter system prompt for impossible actions.",
            }

        expected_stat = scenario.get("expected_stat", "UNKNOWN")
        assigned_stat = arbiter.get("assigned_stat", "UNKNOWN")
        return {
            "error_type": "STAT_MISMATCH",
            "severity": "MODERATE",
            "description": (
                f"Arbiter assigned stat '{assigned_stat}' for '{user_input}' "
                f"but expected '{expected_stat}'. The stat-action mapping was incorrect."
            ),
            "suggested_fix": f"Review Arbiter prompt for {expected_stat} vs {assigned_stat} edge cases.",
        }

    # ── State Sync Error ───────────────────────────────────────────
    if not metrics.get("math_consistent", False):
        rules = trace.get("rules_engine", {})

        if scenario.get("expected_engine_result") == "DENY":
            return {
                "error_type": "ENGINE_SYNC_FAILURE",
                "severity": "CRITICAL",
                "description": (
                    f"The engine should have DENIED '{user_input}' ({sid}) "
                    f"but allowed it through. Rules engine returned: is_success={rules.get('is_success')}"
                ),
                "suggested_fix": "Review the action economy guards in execute_fixed_action() for this edge case.",
            }

        if "System" in cat:
            expected_check = scenario.get("expected_system_check", "")
            actual_check = trace.get("system_check_output", "")
            return {
                "error_type": "ENGINE_SYNC_FAILURE",
                "severity": "CRITICAL",
                "description": (
                    f"System check {sid} expected '{expected_check}' "
                    f"but got '{actual_check}'."
                ),
                "suggested_fix": f"Debug the system test implementation for {sid}.",
            }

        if "Exploration" in cat:
            return {
                "error_type": "ENGINE_SYNC_FAILURE",
                "severity": "MODERATE",
                "description": (
                    f"Exploration guardrail {sid} failed: "
                    f"expected '{scenario.get('expected_system_check', '')}' "
                    f"but got '{trace.get('system_check_output', '')}'."
                ),
                "suggested_fix": "Review get_rest_rejection_message() or resolve_move_target() logic.",
            }

        return {
            "error_type": "ENGINE_SYNC_FAILURE",
            "severity": "CRITICAL",
            "description": (
                f"State sync failed for '{user_input}' ({sid}). "
                f"Rules engine returned: {json.dumps({k: v for k, v in rules.items() if k != 'raw_rolls'}, default=str)}"
            ),
            "suggested_fix": "Investigate the RulesEngine resolve function for this action type.",
        }

    # ── Narrative Error ────────────────────────────────────────────
    if not metrics.get("narrative_present", False):
        return {
            "error_type": "NARRATIVE_FAILURE",
            "severity": "LOW",
            "description": (
                f"DM Narrator produced no output for '{user_input}' ({sid}). "
                f"Trace narrator field: {trace.get('dm_narrator', {})}"
            ),
            "suggested_fix": "Ensure the narrate_result() function has a fallback for empty LLM responses.",
        }

    return {
        "error_type": "UNKNOWN_ERROR",
        "severity": "LOW",
        "description": f"Unspecified error in {sid} for input '{user_input}'.",
        "suggested_fix": "Manual investigation required.",
    }


def analyze_traces(traces: List[dict]) -> dict:
    """
    Produces a comprehensive error analysis report from all trace data.
    """
    report = {
        "total_scenarios": len(traces),
        "total_errors": 0,
        "total_passed": 0,
        "pass_rate": "0%",
        "error_types": {
            "ROUTING_AMBIGUITY": 0,
            "SCHEMA_VIOLATION": 0,
            "STAT_MISMATCH": 0,
            "ENGINE_SYNC_FAILURE": 0,
            "DENIAL_FAILURE": 0,
            "NARRATIVE_FAILURE": 0,
        },
        "severity_counts": {
            "CRITICAL": 0,
            "MODERATE": 0,
            "LOW": 0,
        },
        "failed_scenarios": [],
    }

    for t in traces:
        metrics = t.get("metrics", {})
        if all(metrics.values()):
            report["total_passed"] += 1
            continue

        err = categorize_error(t["scenario"], t["trace"], metrics)
        report["total_errors"] += 1

        etype = err["error_type"]
        if etype in report["error_types"]:
            report["error_types"][etype] += 1

        severity = err.get("severity", "LOW")
        if severity in report["severity_counts"]:
            report["severity_counts"][severity] += 1

        report["failed_scenarios"].append({
            "scenario_id": t["scenario"]["id"],
            "category": t["scenario"]["category"],
            "input": t["scenario"]["input"],
            "error_type": err["error_type"],
            "severity": err["severity"],
            "description": err["description"],
            "suggested_fix": err["suggested_fix"],
        })

    total = report["total_scenarios"]
    if total > 0:
        report["pass_rate"] = f"{report['total_passed'] / total * 100:.1f}%"

    return report
