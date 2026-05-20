import json

def categorize_error(scenario, trace, metrics):
    """
    Given a failed scenario, categorize the error for the thesis error analysis section.
    Returns a dict with 'error_type' and 'description'.
    """
    cat = scenario.get("category", "")
    
    if not metrics.get("routing_correct", False):
        return {
            "error_type": "ROUTING_AMBIGUITY",
            "description": f"The Intent Router classified the input as {trace.get('intent_router', {}).get('predicted_path')} instead of {scenario.get('expected_type')}. It failed to understand the user's phrasing."
        }
        
    if not metrics.get("grounding_correct", False):
        if "Quest" in cat:
            return {
                "error_type": "SCHEMA_VIOLATION",
                "description": "The LLM Cartographer failed to produce valid JSON or violated topological rules (e.g., dangling nodes or missing required fields)."
            }
        else:
            return {
                "error_type": "STAT_MISMATCH",
                "description": f"The Action Arbiter assigned the wrong stat/DC for the stunt, breaking the intended rule mapping."
            }
            
    if not metrics.get("math_consistent", False):
        if "Baseline" in trace: # If this is a baseline run hallucinating state
            return {
                "error_type": "STATE_HALLUCINATION",
                "description": "The raw LLM hallucinated the game state, incorrectly modifying HP or inventory without following the rules."
            }
        return {
            "error_type": "ENGINE_SYNC_FAILURE",
            "description": "The Python rules engine failed to correctly sync the state (e.g., failed to block an illegal move, or math was wrong)."
        }
        
    if not metrics.get("narrative_present", False):
        return {
            "error_type": "NARRATIVE_FAILURE",
            "description": "The DM Narrator agent hallucinated or failed to generate a coherent description of the event."
        }
        
    return {
        "error_type": "UNKNOWN_ERROR",
        "description": "An unspecified error occurred."
    }

def analyze_traces(traces):
    """
    Produces a summary report of errors by category.
    """
    report = {
        "total_errors": 0,
        "error_types": {
            "ROUTING_AMBIGUITY": 0,
            "SCHEMA_VIOLATION": 0,
            "STAT_MISMATCH": 0,
            "ENGINE_SYNC_FAILURE": 0,
            "STATE_HALLUCINATION": 0,
            "NARRATIVE_FAILURE": 0
        },
        "failed_scenarios": []
    }
    
    for t in traces:
        metrics = t.get("metrics", {})
        # If any metric is False (and it's not a baseline run specifically unless requested)
        if not all(metrics.values()):
            err = categorize_error(t["scenario"], t["trace"], metrics)
            report["total_errors"] += 1
            if err["error_type"] in report["error_types"]:
                report["error_types"][err["error_type"]] += 1
            report["failed_scenarios"].append({
                "scenario_id": t["scenario"]["id"],
                "input": t["scenario"]["input"],
                "error_type": err["error_type"],
                "description": err["description"]
            })
            
    return report

