# Workflow Orchestrator

**Purpose:** High-level workflow coordination and data flow between processing steps.

---

## Sequential Processing Requirement

**CRITICAL:** When processing multiple issues, they MUST be processed ONE AT A TIME, NEVER in parallel.

### Before Starting Each Issue:
```
Output: "Now starting processing issue #[number]"
```

### After Completing Each Issue:
```
Output: "Issue #[number] is processed, moving to the next one..."
```

### Processing Flow for Multiple Issues:
```
Issue Queue: [#12345, #12346, #12347]

→ "Now starting processing issue #12345"
→ Execute Steps 1-7 for #12345
→ Output Final Report for #12345
→ "Issue #12345 is processed, moving to the next one..."

→ "Now starting processing issue #12346"
→ Execute Steps 1-7 for #12346
→ Output Final Report for #12346
→ "Issue #12346 is processed, moving to the next one..."

→ ... continue until queue is empty
```

---

## Workflow Overview

Each issue MUST be processed through these 7 steps in order:

```
[ ] Step 1: Information Collection
[ ] Step 2: Issue Eligibility Check
[ ] Step 3: Type Classification
[ ] Step 4: Minimum Requirements Validation
[ ] Step 5: Codebase Analysis
[ ] Step 6: Team Assignment
[ ] Step 7: Label Application and Commenting
[ ] Final Report
```

**CRITICAL RULE:** Each step must be completed successfully before moving to the next step. If any step (1-6) fails, move directly to Step 7 and apply appropriate labels/comments. Do NOT attempt remaining incomplete steps.

---

## Step 1: Information Collection

**Objective:** Gather all available information from the GitHub issue.

### GitHub API Calls:
```
1. Get Issue Details:
   Tool: mcp_github_github_get_issue
   Parameters: owner="microsoft", repo="ALAppExtensions", issue_number
   Extract:
     - title
     - description (body)
     - type field
     - labels[]
     - created_at
     - updated_at
     - author (login, id)

2. Get Issue Comments:
   Tool: mcp_github_github_list_issue_comments
   Parameters: owner="microsoft", repo="ALAppExtensions", issue_number
   Extract from each comment:
     - body (comment text)
     - author (login)
     - created_at
   Sort: Chronologically by created_at

3. Determine Source of Truth:
   Compare: issue.updated_at vs last_comment.created_at
   Rule: Use MOST RECENT timestamp as authoritative source
   
4. Extract Technical Details (from description + comments):
   - Object references: "codeunit 80", "table 273", "page 50"
   - Procedure/trigger names
   - Event parameters mentioned
   - Namespace references
   - Proposed code snippets
```

### Data Structure to Build:
```
IssueContext {
  number: int
  title: string
  description: string
  type: string
  labels: string[]
  author: string
  created_at: timestamp
  updated_at: timestamp
  comments: Comment[]
  source_of_truth: "description" | "comments"
  
  extracted_data: {
    objects: string[]           // ["codeunit 80", "table 18"]
    procedures: string[]         // ["PostSalesDoc", "CheckInventory"]
    namespaces: string[]         // ["Microsoft.Sales.Posting"]
    proposed_code: string        // Code snippets from author
  }
}
```

### On Success:
- Proceed to Step 2 with populated IssueContext

### On Failure:
- Skip issue silently
- Log: "Failed to retrieve issue #N"
- Continue to next issue

---

## Workflow Transitions

### Decision Tree

```
START
  ↓
Step 1: Information Collection
  ├─ Success → Step 2
  └─ Failure → Skip issue, log, continue to next
  
Step 2: Issue Eligibility Check
  ├─ Pass → Mark as eligible, continue to Step 3
  └─ Failure → Skip issue, log, continue to next
  
Step 3: Type Classification
  ├─ Type determined → Step 4
  └─ Ambiguous → Step 7 (agent-not-processable)
  
Step 4: Requirements Validation
  ├─ All requirements met → Step 5
  └─ Missing requirements → Step 7 (missing-info + comment)
  
Step 5: Codebase Analysis
  ├─ Analysis successful → Step 6
  ├─ ALL already implemented → Step 7 (close issue with comment, STOP)
  ├─ PARTIAL already implemented → Step 6 (process pending, note existing in comment)
  └─ Analysis failed → Step 7 (with appropriate label and comment)
  
Step 6: Team Assignment
  ├─ Team determined → Step 7 (approval path)
  └─ No match → Step 7 (agent-not-processable)
  
Step 7: Label & Comment Application
  ├─ Apply labels (if needed)
  ├─ Add comment (if needed)
  ├─ Close issue (if already-implemented or stale)
  └─ Final Report
```

### Step-by-Step Flow

| Current Step | Condition | Next Step | Action |
|--------------|-----------|-----------|--------|
| **Step 1** | Success | Step 2 | Pass IssueContext |
| **Step 1** | Failure | Skip | Log error, move to next issue |
| **Step 2** | Eligible | Step 3 | Continue processing |
| **Step 2** | Not eligible | Skip | Log skip reason, move to next issue |
| **Step 3** | Type found | Step 4 | Pass type + sub-type |
| **Step 3** | Ambiguous | Step 7 | Apply agent-not-processable |
| **Step 4** | Requirements met | Step 5 | Continue |
| **Step 4** | Requirements missing | Step 7 | Apply missing-info + comment |
| **Step 5** | Analysis successful | Step 6 | Pass analysis results |
| **Step 5** | ALL already implemented | Step 7 | Post comment, close issue, STOP |
| **Step 5** | PARTIAL already implemented | Step 6 | Process pending changes, note existing |
| **Step 5** | Analysis failed | Step 7 | Apply appropriate label + comment (if needed) |
| **Step 6** | Team found | Step 7 | Approval path |
| **Step 6** | No team match | Step 7 | Apply agent-not-processable |
| **Step 7** | Any scenario | Final Report | Complete processing |

### Data Flow Between Steps

```
Step 1 Output → Step 2 Input:
  - IssueContext (complete issue data)

Step 2 Output → Step 3 Input:
  - Eligibility confirmed
  - IssueContext passed through

Step 3 Output → Step 4 Input:
  - request_type: string
  - sub_type: string (if applicable)
  - max_iterations: int
  - IssueContext passed through

Step 4 Output → Step 5 Input:
  - requirements_met: boolean
  - missing_items: string[] (if not met)
  - IssueContext + type info passed through

Step 5 Output → Step 6 Input (if analysis successful or partial already implemented):
  - analysis_result: "SUCCESS" | "FAILED" | "ALL_ALREADY_IMPLEMENTED" | "PARTIAL_ALREADY_IMPLEMENTED"
  - feasibility: "CAN" | "CANNOT" | "MODIFY" (if SUCCESS)
  - implementation_code: string (if CAN)
  - blocker_reason: string (if CANNOT or FAILED)
  - target_objects: Object[]
  - namespaces: string[]
  - already_implemented_changes: Change[] (if PARTIAL)
  - pending_changes: Change[] (if PARTIAL or SUCCESS)
  - All previous data

Step 5 Output → Step 7 Input (if ALL already implemented):
  - analysis_result: "ALL_ALREADY_IMPLEMENTED"
  - already_implemented_changes: Change[] (all existing implementations)
  - pending_changes: [] (empty - nothing to implement)
  - Skip Step 6 entirely
  - Proceed directly to Step 7 to close issue

Step 6 Output → Step 7 Input:
  - team: "Finance" | "SCM" | "Integration"
  - All previous data

Step 7 Output → Final Report:
  - labels_applied: string[]
  - comment_posted: boolean
  - issue_closed: boolean (true if already-implemented or stale)
  - issue_status: string
  - next_action: string
```

### Error Handling Flow

```
GitHub API Error:
  - Retry 3 times (5s delay)
  - If still fails → Skip issue silently
  - Log internally
  - Move to next issue

Codebase Search Error:
  - Retry 3 times (5s delay)  
  - If still fails → Step 7 (agent-not-processable, no comment)

Label Application Error:
  - Retry 3 times (5s delay)
  - If still fails → Log internally, mark failed
  - Do NOT notify user

Comment Posting Error:
  - Retry 3 times (5s delay)
  - If still fails → Log internally
  - Labels remain applied
  - Do NOT notify user
```

---

## Final Report Format

**Objective:** Provide brief summary to user after Step 7 completes.

### Report Template:
```
Maximum 2 sentences

Format:
  Sentence 1: Issue status
  Sentence 2: Key outcome or next action
```

### Report Examples:

#### ✅ Approved Issues
```
"Issue #12345 approved for implementation by Finance team. Implementation code provided in comment."

"Issue #54321 approved for SCM team. Event signature and placement specified in comment."
```

#### ⚠️ Missing Information
```
"Issue #12345 requires additional information from author. Comment posted with specific requirements."

"Issue #98765 needs clarification on target procedure. Fuzzy matches suggested in comment."
```

#### ❌ Not Processable - Environmental
```
"Issue #12345 cannot be processed due to code protection restrictions. Marked as agent-not-processable."

"Issue #11111 target object not found in codebase. Marked as agent-not-processable."
```

#### ❌ Not Processable - Technical
```
"Issue #22222 cannot be processed - IsHandled at start of OnDelete trigger not allowed. Explanation provided in comment."

"Issue #33333 blocked by public signature change requirement. Alternative approach suggested in comment."
```

#### ✅ Already Implemented (100% Match - All Requests)
```
"Issue #44444 closed - requested change already exists in codebase. Existing implementation provided to author."

"Issue #55555 closed - event already has the requested 'var' parameter. Existing signature shown in comment."

"Issue #66666 closed - procedure is already public. No changes needed."
```

#### ✅ Partial Already Implemented (Some Existing, Some Approved)
```
"Issue #77777 approved for implementation. 1 of 3 requests already exists (shown in comment), 2 approved for SCM team."

"Issue #88888 approved for Finance team. Existing var parameter noted, new event request approved for implementation."
```

#### ⏱️ Max Iterations Reached
```
"Issue #77777 reached maximum iteration limit (5 iterations). Manual review required."
```

#### 🔄 Reprocessing After Update
```
"Issue #88888 reprocessed after author update. Still requires performance considerations for IsHandled request."
```

### Pre-Step 7 Checklist (MANDATORY)

**CRITICAL:** Before attempting to apply labels in Step 7, agent MUST verify that ALL previous steps were completed. If there was no blocker or missing-info stop in Steps 2-6, ALL steps must show as completed.

```
Agent MUST check the following before proceeding to label application:

✅ Step 1: Information Collection - COMPLETED
✅ Step 2: Eligibility Check - COMPLETED (Pass)
✅ Step 3: Type Classification - COMPLETED (Type determined)
✅ Step 4: Requirements Validation - COMPLETED (All requirements met OR missing-info identified)
✅ Step 5: Codebase Analysis - COMPLETED (Feasibility determined OR already-implemented detected)
✅ Step 6: Team Assignment - COMPLETED (Team assigned) OR SKIPPED (if already-implemented)

If ANY step above is NOT completed and there was no blocker/missing-info/already-implemented stop:
  → DO NOT proceed to label application
  → Complete the missing step(s) first
  → Then proceed to Step 7

Only proceed to Step 7 when:
  1. ALL steps 1-6 are completed successfully (approval path), OR
  2. A step failed with blocker → proceed with agent-not-processable, OR
  3. A step identified missing-info → proceed with missing-info label, OR
  4. Step 5 detected ALL already-implemented → proceed to close issue with comment (skip Step 6), OR
  5. Step 5 detected PARTIAL already-implemented → continue to Step 6 for pending changes
```

### Pre-Report Checklist

Before providing final report, agent MUST verify:
```
✅ Pre-Step 7 checklist passed (all steps completed or valid stop)
✅ Step 7 fully completed
✅ All required labels applied to GitHub issue
✅ Comment posted (if scenario requires comment)
✅ Iteration counter updated (if applicable)
✅ No pending GitHub API calls
✅ No unhandled errors
```

### Report Structure

```
[Status Icon] [Issue Number] [Primary Outcome]. [Secondary Detail or Next Action].

Status Icons:
  ✅ = Approved / Completed successfully
  ⚠️ = Requires action from author
  ❌ = Cannot process (blocker)
  ⏱️ = Process limit reached
  🔄 = Reprocessing
```

---

**Next Files:**
- **[02-step2-eligibility-check.md](02-step2-eligibility-check.md)** - Issue eligibility validation rules (Step 2)
- **[03-step3-request-types.md](03-step3-request-types.md)** - Type classification rules (Step 3)
- **[04-step4-requirements-validation.md](04-step4-requirements-validation.md)** - Requirements validation per type (Step 4)
- **[05-step5-codebase-analysis.md](05-step5-codebase-analysis.md)** - Codebase analysis instructions (Step 5)
- **[06-step6-team-assignment.md](06-step6-team-assignment.md)** - Team mapping logic (Step 6)
- **[07-step7-labels-comments.md](07-step7-labels-comments.md)** - GitHub interaction patterns (Step 7)

---

**Version:** 2.0  
**Last Updated:** November 27, 2025
