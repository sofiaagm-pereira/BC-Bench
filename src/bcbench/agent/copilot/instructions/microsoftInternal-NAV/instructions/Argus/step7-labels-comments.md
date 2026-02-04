# Labels & Comments

**Purpose:** Finalize issue by applying labels, posting comments, and closing if needed.

**Rule:** All comments must be generated using templates from `comment-templates/comment_templates.yaml` corresponding to the situation.

## 1. Prerequisites (Mandatory)
- Verify **ALL** previous steps completed if outcome is `FEASIBLE`.
- If outcome is `MISSING_INFO` or `AGENT_NOT_PROCESSABLE`, partial completion is valid.

## 2. Decision Logic

### A. Success (Feasible)
- **Labels:** Team (e.g., "Finance") + Type (e.g., "event-request"). Added as a pair.
- **Comment:** "✅ Analysis complete - approved for implementation". Include existing/pending code.
- **Status:** Open.

### B. Missing Info
- **Labels:** `missing-info` **ONLY**. (No Type/Team labels).
- **Comment:** Explain what is missing/needed.
- **Status:** Open.

### C. Agent Not Processable
- **Labels:** `agent-not-processable` **ONLY**.
- **Comment:** None.
- **Status:** Open.

### D. Auto Reject
- **Labels:** None.
- **Comment:** "This request cannot be implemented." + Reason.
- **Status:** **Close** (Reason: not planned).

### E. Already Implemented
- **Labels:** None.
- **Comment:** "✅ Already implemented." Show code snippets.
- **Status:** **Close** (Reason: completed).

### F. Stale Issue (30+ days inactive)
- **Labels:** Maintain `missing-info`.
- **Comment:** "Closing due to inactivity."
- **Status:** **Close** (Reason: not planned).

## 3. Execution Order

### A. Generate Comprehensive Workflow JSON (REQUIRED)

After completing all workflow steps, you MUST produce a comprehensive JSON output that includes:
1. Results from ALL executed steps (Steps 0-7)
2. Final determination and summary
3. Actions to be taken (labels, comments, status)

**CRITICAL:** The JSON MUST be wrapped in a markdown code fence with the `json` language identifier.

**Required JSON Structure:**
```json
{
  "workflow_execution": {
    "issue_number": <number>,
    "issue_title": "<string>",
    "processing_status": "<FEASIBLE|MISSING_INFO|AGENT_NOT_PROCESSABLE|AUTO_REJECT|ALREADY_IMPLEMENTED|STALE>",

    "step0_initialization": {
      "status": "<string>",
      "details": "<string>"
    },

    "step1_collect_data": {
      "Success": <boolean>,
      "GH_REQUEST": { /* full GitHub request object */ },
      "FailureReason": "<string>"
    },

    "step2_eligibility_check": {
      "IsEligible": <boolean>,
      "IsStale": <boolean>,
      "FailureReason": "<string>"
    },

    "step3_request_types": {
      "Success": <boolean>,
      "TYPE": "<string>",
      "SUBTYPE": "<string>",
      "FailureLabel": "<string>",
      "FailureReason": "<string>"
    },

    "step4_requirements_check": {
      "Success": <boolean>,
      "FailureLabel": "<string>",
      "FailureReason": "<string>",
      "validation_log": ["<string>"]
    },

    "step5_codebase_analysis": {
      "status": "<COMPLETED|SKIPPED>",
      "Success": <boolean>,
      "OBJECT_LIST": ["<string>"],
      "SUGGESTED_IMPLEMENTATION": "<string>",
      "FailureLabel": "<string>",
      "FailureReason": "<string>"
    },

    "step6_team_assignment": {
      "status": "<COMPLETED|SKIPPED>",
      "Success": <boolean>,
      "TEAM_LABEL": "<string>",
      "FailureLabel": "<string>",
      "FailureReason": "<string>"
    },

    "step7_finalize": {
      "decision": "<FEASIBLE|MISSING_INFO|AGENT_NOT_PROCESSABLE|AUTO_REJECT|ALREADY_IMPLEMENTED|STALE>",
      "labels": ["<string>"],
      "comment": "<string>",
      "status": "<open|closed>",
      "reasoning": "<string>"
    }
  },

  "final_determination": {
    "outcome": "<FEASIBLE|MISSING_INFO|AGENT_NOT_PROCESSABLE|AUTO_REJECT|ALREADY_IMPLEMENTED|STALE>",
    "labels_to_apply": ["<string>"],
    "comment_to_post": "<string>",
    "issue_will_be_closed": <boolean>,
    "next_steps": "<string>",
    "summary": {
      "request_type": "<string>",
      "target_object": "<string>",
      "blocking_issues": ["<string>"]
    }
  }
}
```

**Example Format:**
````
## Analysis Complete ✅

[Optional human-readable summary]

```json
{
  "workflow_execution": {
    "issue_number": 12345,
    "processing_status": "MISSING_INFO",
    "step1_collect_data": { ... },
    ...
  },
  "final_determination": { ... }
}
```
````

### B. Apply GitHub Actions (If Not Read-Only Mode)

Based on the JSON output above:
1. Apply the labels specified in `final_determination.labels_to_apply`
2. Post the comment from `final_determination.comment_to_post` (if any)
3. Close the issue if `final_determination.issue_will_be_closed` is true
