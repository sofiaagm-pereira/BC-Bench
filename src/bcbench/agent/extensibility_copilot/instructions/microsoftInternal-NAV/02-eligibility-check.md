# Step 2: Issue Eligibility Check

**Purpose:** Validate that the issue meets basic processing criteria before proceeding with analysis.

---

## Overview

This step determines whether an issue is eligible for automated processing. An issue must pass ALL eligibility checks to proceed to Step 3.

**Important:** If ANY check fails, log the reason and skip this issue (move to next issue in queue). Do NOT proceed to Step 3.

---

## Check 1: Issue Type Validation

### Rule:
```
Issue Type MUST equal "Task"
```

### How to Check:
```
Action: Extract "type" field from IssueContext (collected in Step 1)
Source: IssueContext.type

Validation:
  if type == "Task":
    ✅ PASS - Continue to Check 2
  else:
    ❌ FAIL - Issue not eligible
```

### On Failure:
```
Action: Skip this issue
Log: "Skipped issue #[number]: Type is '[actual_type]', not Task"
Move to: Next issue in queue
Do NOT proceed to Step 3
```

### Rationale:
Only Task-type issues represent extensibility requests. Other types (Bug, Feature, Question, etc.) are handled through different workflows.

---

## Check 2: Label Status Validation

### Rules:
```
Issue labels MUST be in one of these states:
  1. NO labels at all → ✅ ELIGIBLE (first-time processing)
  2. ONLY "missing-info" label → ✅ ELIGIBLE (reprocessing after author update)
  3. ANY OTHER labels → ❌ NOT ELIGIBLE (already processed)
```

### How to Check:
```
Action: Extract "labels" array from IssueContext
Source: IssueContext.labels[]

Validation Logic:
  if labels.length == 0:
    ✅ PASS - First time processing
    
  else if labels.length == 1 AND labels[0] == "missing-info":
    # Check 2A: Verify author responded last
    Action: Get all comments and last update timestamp
    Source: IssueContext.comments[] and IssueContext.timestamps
    
    last_commenter = get_last_commenter_from(IssueContext.comments)
    
    if last_commenter != IssueContext.author:
      ❌ FAIL - Agent commented last, waiting for author response
      Log: "Skipped issue #[number]: Waiting for author response on missing-info"
      Move to: Next issue in queue
    
    # Check 2B: Verify not stale (30+ days with missing-info)
    days_since_last_activity = calculate_days_since(IssueContext.timestamps.last_activity)
    
    if days_since_last_activity >= 30:
      ⚠️ CLOSE - Issue stale, close with comment
      Action: Go to Step 7 with close_stale flag
      Comment: "No activities, will be closed"
      Labels: Keep "missing-info" label
      Close issue
      Move to: Next issue in queue
    
    # If both checks pass
    ✅ PASS - Reprocessing scenario (author responded and within 30 days)
    
  else:
    ❌ FAIL - Issue already processed (has other labels)
```

### On Failure:
```
Action: Skip this issue
Log: "Skipped issue #[number]: Already has labels [label1, label2, ...]"
Move to: Next issue in queue
Do NOT proceed to Step 3

Special Case - Stale Issue (30+ days with missing-info):
Action: Close this issue
Log: "Closing issue #[number]: No activity for 30+ days with missing-info label"
Comment: "No activities, will be closed"
Close issue via GitHub API
Move to: Next issue in queue
```

### Rationale:
Issues with labels (other than "missing-info") have already been processed by the agent. Processing them again would:
- Duplicate work
- Potentially overwrite team/type labels
- Waste resources
- Create confusion with multiple agent comments

### Reprocessing Scenario:
```
When issue has ONLY "missing-info" label:
  - Agent must verify author responded last (Check 2A)
  - If agent commented last → SKIP (wait for author)
  - Agent must verify issue not stale (Check 2B)
  - If 30+ days since last activity → CLOSE issue
  - If author responded AND within 30 days → ELIGIBLE for reprocessing
  - This ensures iterative refinement only when author engaged
```

---

## Eligibility Decision Matrix

| Type | Labels | Last Commenter | Days Since Activity | Decision | Next Action |
|------|--------|----------------|---------------------|----------|-------------|
| Task | None | - | - | ✅ ELIGIBLE | Proceed to Step 3 |
| Task | Only "missing-info" | Author | < 30 days | ✅ ELIGIBLE | Proceed to Step 3 (reprocessing) |
| Task | Only "missing-info" | Agent | Any | ❌ NOT ELIGIBLE | Skip issue, wait for author |
| Task | Only "missing-info" | Any | ≥ 30 days | ⚠️ CLOSE | Close issue with comment |
| Task | "missing-info" + others | - | - | ❌ NOT ELIGIBLE | Skip issue, log reason |
| Task | Any other labels | - | - | ❌ NOT ELIGIBLE | Skip issue, log reason |
| Bug | Any | - | - | ❌ NOT ELIGIBLE | Skip issue, log reason |
| Feature | Any | - | - | ❌ NOT ELIGIBLE | Skip issue, log reason |
| Other | Any | - | - | ❌ NOT ELIGIBLE | Skip issue, log reason |

---

## Output Data

### On Success (All Checks Pass):
```
Output to Step 3:
  - eligibility_confirmed: true
  - IssueContext (passed through unchanged)

Action: Proceed to Step 3 (Type Classification)
```

### On Failure (Any Check Fails):
```
Output: None (issue skipped)

Action: 
  - Log skip reason internally
  - Move to next issue in queue
  - Do NOT proceed to Step 3
  - Do NOT go to Step 7 (no labels/comments added)

Exception - Stale Issue Closure:
Output to Step 7:
  - close_stale: true
  - IssueContext (passed through)
  - close_comment: "No activities, will be closed"

Action:
  - Proceed directly to Step 7
  - Post comment "No activities, will be closed"
  - Close issue via GitHub API
  - Move to next issue in queue
```

---

## Logging Format

### Log Messages:
```
Success:
  "Issue #[number] eligible for processing"

Type Check Failure:
  "Skipped issue #[number]: Type is '[actual_type]', not Task"

Label Check Failure:
  "Skipped issue #[number]: Already has labels [Finance, event-request]"
  "Skipped issue #[number]: Already has labels [SCM, request-for-external, missing-info]"

Missing-Info Check Failure:
  "Skipped issue #[number]: Waiting for author response on missing-info"

Stale Issue Closure:
  "Closing issue #[number]: No activity for 30+ days with missing-info label"
```

### Log Level:
```
- Use INFO level for skipped issues (expected behavior)
- Do NOT use ERROR or WARNING (not system failures)
- Logs are for debugging/metrics, not user-facing
```

---

## Special Cases

### Case 1: User Explicitly Requests Processing
```
Scenario: User says "Process issue #12345" but issue already has labels

Decision: STILL SKIP
Reason: Eligibility rules apply universally
         Prevents accidental reprocessing
         Maintains data integrity
         
User Feedback: "Issue #12345 already processed (has labels: [list])"
```

### Case 2: Issue Updated After Labeling
```
Scenario: Issue has team/type labels, then author updates description

Decision: STILL SKIP
Reason: Labels indicate processing complete
        Author should comment if changes needed
        Prevents overwriting existing analysis
        
Exception: If labels manually removed by maintainer, then eligible
```

### Case 3: Missing-Info Label with Other Labels
```
Scenario: Issue has "missing-info" AND "event-request" labels

Decision: SKIP
Reason: Type label indicates processing already occurred
        Multiple labels = previous complete analysis
        
Rationale: "missing-info" alone = awaiting author
          "missing-info" + others = already classified
```

### Case 4: Missing-Info Label - Agent Commented Last
```
Scenario: Issue has ONLY "missing-info" label, agent posted last comment

Decision: SKIP
Reason: Agent is waiting for author to provide additional information
        Processing would duplicate agent's previous comment
        Author needs time to respond
        
How to Check: Compare last commenter in IssueContext.comments[] with issue author
User Feedback: "Issue #[number] waiting for author response on missing-info"
```

### Case 5: Missing-Info Label - Stale Issue (30+ Days)
```
Scenario: Issue has ONLY "missing-info" label, no activity for 30+ days

Decision: CLOSE
Reason: Author has not responded in reasonable timeframe
        Issue considered abandoned
        Keeps issue queue clean
        
How to Check: Calculate days since IssueContext.timestamps.last_activity
Action: Post comment "No activities, will be closed" and close issue
User Feedback: "Closed issue #[number]: No activity for 30+ days"
```

---

## Implementation Notes

### Data Source:
```
All checks use data from IssueContext built in Step 1
Do NOT make additional GitHub API calls in this step
```

### Performance:
```
Both checks are fast in-memory operations
No external dependencies
No codebase searches required
Should complete in < 100ms
```

### Error Handling:
```
If IssueContext is malformed or missing required fields:
  - Treat as Step 1 failure
  - Skip issue silently
  - Log: "Skipped issue #[number]: Invalid IssueContext"
```

---

## Next Step

**On Success:** Proceed to [03-step3-request-types.md](03-step3-request-types.md) (Step 3: Type Classification)

**On Failure:** Move to next issue in processing queue

---

**Version:** 2.0  
**Last Updated:** November 27, 2025
