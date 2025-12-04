# Step 7: Label Application & Commenting

**Purpose:** Apply appropriate labels and post comments to the GitHub issue based on processing outcome.

---

## Pre-Step 7 Verification (MANDATORY)

**CRITICAL:** Before executing ANY action in Step 7, agent MUST verify that all previous steps were completed.

```
STEP 7 ENTRY CHECK:

If outcome is "FEASIBLE" (approval path):
  Verify ALL steps completed:
  ✅ Step 1: Information Collection - COMPLETED
  ✅ Step 2: Eligibility Check - COMPLETED (Pass)
  ✅ Step 3: Type Classification - COMPLETED (Type determined)
  ✅ Step 4: Requirements Validation - COMPLETED (All requirements met)
  ✅ Step 5: Codebase Analysis - COMPLETED (Feasibility confirmed)
  ✅ Step 6: Team Assignment - COMPLETED (Team assigned)
  
  If ANY step is incomplete → DO NOT APPLY LABELS
  → Go back and complete the missing step first
  → Then return to Step 7

If outcome is "MISSING_INFO" or "AGENT_NOT_PROCESSABLE":
  Processing stopped at a specific step - this is valid
  → Proceed with appropriate label (missing-info or agent-not-processable)
  → Document which step caused the stop

If outcome is "ALREADY_IMPLEMENTED":
  Request already exists in codebase - this is a SUCCESS scenario
  ✅ Step 1: Information Collection - COMPLETED
  ✅ Step 2: Eligibility Check - COMPLETED (Pass)
  ✅ Step 3: Type Classification - COMPLETED (Type determined)
  ✅ Step 4: Requirements Validation - COMPLETED (All requirements met)
  ✅ Step 5: Codebase Analysis - COMPLETED (Already implemented detected)
  ⏭️ Step 6: Team Assignment - SKIPPED (not needed)
  
  → Post comment showing existing implementation
  → Close the issue
  → No labels needed (issue will be closed)

NEVER apply type/team labels if Steps 4, 5, or 6 were skipped!
```

---

## Overview

This is the final step that:
1. **Apply Labels** - Add type, team, and status labels to issue
2. **Post Comments** - Add agent-generated comments when needed
3. **Update Issue State** - Close issue if required (stale issues, already-implemented)
4. **Record Metadata** - Track iteration count and processing history

**Critical Behavior:**
- **SEQUENTIAL OPERATIONS ONLY** - NEVER combine multiple GitHub operations in a single API call. Always execute as separate sequential calls:
  1. First: Apply/remove labels (if needed) - use `mcp_github_github_issue_write` with ONLY `labels` parameter
  2. Then: Post comment (if needed) - use `mcp_github_github_add_issue_comment`
  3. Finally: Close issue (if needed) - separate API call
- **⚠️ NEVER pass "body" when applying labels** - Using `body` parameter in `issue_write` OVERWRITES the issue description!
- **ALWAYS use `add_issue_comment` for comments** - Never use `issue_write` with `body` to post comments
- **No comment for blockers** - agent-not-processable gets label only
- **Comment for missing-info** - Always explain what's needed
- **Comment AND close for already-implemented** - Show existing code, THEN close the issue (two separate operations)
- **Team and Type labels are paired** - Applied together or not at all (order: team, then type)
- **Status labels are EXCLUSIVE** - missing-info and agent-not-processable are applied ALONE, NEVER with type labels
- **NEVER combine missing-info with type label** - If requesting clarification, apply ONLY missing-info label
- **Idempotent operations** - Don't duplicate existing labels

---

## Label Categories

### Status Labels:
```
- "missing-info"           → Author needs to provide clarification
- "agent-not-processable"  → Cannot be processed (blocker or environmental)
```

### Type Labels:
```
- "event-request"
- "request-for-external"
- "enum-request"
- "extensibility-enhancement"
- "bug"
```

### Team Labels:
```
- "Finance"
- "SCM"
- "Integration"
```

**Note:** All label names and categories are defined by GitHub repository configuration. Agent applies labels that already exist in repository.

---

## Processing Outcomes

Based on previous steps, the issue will be in one of these states:

### Outcome 1: Feasible (Success Path)
```
From: Step 6 (team assigned)
Labels to Apply:
  - Team label (e.g., "Finance")
  - Type label (e.g., "event-request")
  Note: Applied as a PAIR in this order
Comment: REQUIRED
  - "✅ Analysis complete - approved for implementation"
  - If already_implemented_changes exists: Show existing implementations first
  - Show exact implementation code for pending changes with AL syntax
  - Include all code changes needed
Action: Complete processing

Note: If issue had PARTIAL_ALREADY_IMPLEMENTED outcome from Step 5:
  - Comment includes BOTH existing implementations AND new implementation guidance
  - Issue is NOT closed (pending work remains for team)
  - Labels are applied normally
```

### Outcome 1b: Feasible with Partial Already Implemented
```
From: Step 6 (team assigned, some requests already exist)
Labels to Apply:
  - Team label (e.g., "Finance")
  - Type label (e.g., "event-request")
  Note: Applied as a PAIR in this order
  
Comment: REQUIRED
  - Start with: "✅ Analysis complete - approved for implementation"
  - Section 1: "**Already implemented in codebase:**"
    - Show each already_implemented_change with existing code
  - Section 2: "**Implementation needed:**"
    - Show implementation guidance for pending_changes
    
Action: 
  - Apply labels
  - Post combined comment
  - Do NOT close issue (pending work remains)
  - Complete processing
```

### Outcome 2: Missing Information
```
From: Any step (Step 3, 4, 5, or 6)
Labels to Apply:
  - "missing-info" ONLY
  
  ⚠️ CRITICAL: NEVER apply type labels (event-request, enum-request, etc.) 
               when applying missing-info label!
  
  Note: NO type or team labels - processing is incomplete, 
        awaiting author clarification/justification
        
Comment: REQUIRED
  - Explain what information is missing
  - Provide specific guidance
  - Reference iteration count if applicable
Action: Increment iteration counter
```

### Outcome 3: Agent Not Processable (Blocker)
```
From: Any step (Step 3, 4, 5, or 6)
Labels to Apply:
  - "agent-not-processable" ONLY
  Note: NO type or team labels (processing blocked)
Comment: None (environmental or technical blocker)
Action: Stop processing
```

### Outcome 4: Stale Issue (30+ Days)
```
From: Step 2 (eligibility check)
Labels to Apply:
  - Keep existing "missing-info" label
Comment: "No activities, will be closed"
Action: Close issue
```

### Outcome 5: All Already Implemented (Close Issue)
```
From: Step 5 (codebase analysis detected ALL requests are 100% match)
Condition: ALL requested changes already exist in codebase (pending_changes is empty)

Labels to Apply:
  - NONE (issue will be closed)
  Note: No labels needed since issue is being closed as completed

Comment: REQUIRED
  - "✅ Good news! This is already implemented in the codebase."
  - Show ALL existing implementations (each already_implemented_change)
  - Show the file location for each
  - Provide code snippets showing existing implementations

Action: 
  - Post comment with ALL existing implementations
  - CLOSE the issue (state_reason: "completed")
  - STOP processing

⚠️ CRITICAL: Only close issue when ALL requests are already implemented.
   If ANY request still needs implementation → use Outcome 1b instead.

Rationale:
  - Author's need is already satisfied
  - No implementation work required
  - Closing keeps backlog clean
  - Comment helps author find and use existing code
```

---

## Label Application Process

### Step 7.1: Determine Labels to Apply

```
Action: Build label list based on IssueContext outcome

labels_to_apply = []

# Rule: Type and Team labels are ALWAYS applied together as a pair, or not at all
# Rule: Status labels (missing-info, agent-not-processable) are applied alone

if IssueContext.outcome == "FEASIBLE":
  # Success path - apply team + type labels as pair
  if IssueContext.team_assignment exists AND IssueContext.type exists:
    labels_to_apply.append(IssueContext.team_assignment.team)  # Team FIRST
    labels_to_apply.append(IssueContext.type)                  # Type SECOND
  else:
    # Missing either team or type - cannot apply pair
    # Treat as blocker
    IssueContext.outcome = "AGENT_NOT_PROCESSABLE"
    labels_to_apply.append("agent-not-processable")

else if IssueContext.outcome == "MISSING_INFO":
  # Apply ONLY status label - NEVER type/team labels
  # Even if type was determined, do NOT apply it when missing-info
  labels_to_apply.append("missing-info")
  # ⚠️ CRITICAL: Do NOT add type label here, even if IssueContext.type exists

else if IssueContext.outcome == "AGENT_NOT_PROCESSABLE":
  # Apply only status label, NO type/team
  labels_to_apply.append("agent-not-processable")

else if IssueContext.outcome == "ALREADY_IMPLEMENTED":
  # No labels needed - issue will be closed
  # The requested change already exists in codebase
  labels_to_apply = []  # Empty - no labels to apply
  IssueContext.close_issue = true
  IssueContext.close_reason = "completed"

# Store for next step
IssueContext.labels_to_apply = labels_to_apply
```

### Step 7.2: Remove Conflicting Labels

```
Action: Remove labels that conflict with new labels

existing_labels = get_current_labels_from_issue(issue_number)

# Remove old status labels before applying new ones
status_labels = ["missing-info", "agent-not-processable"]
for each label in status_labels:
  if label in existing_labels AND label not in IssueContext.labels_to_apply:
    remove_label(issue_number, label)

# Rationale: Issue state changed, old status label no longer applies
# Example: Issue had "missing-info", author responded, now feasible
#          Remove "missing-info" before applying team label
```

### Step 7.3: Apply Labels

```
Action: Add new labels to issue

for each label in IssueContext.labels_to_apply:
  # Check if label already exists on issue
  if label not in existing_labels:
    add_label(issue_number, label)
    log_message("Applied label '{label}' to issue #{issue_number}")
  else:
    log_message("Label '{label}' already exists on issue #{issue_number}, skipping")

# Idempotent: Safe to run multiple times, won't duplicate labels
```

---

## Comment Generation Process

### Step 7.4: Determine if Comment Needed

```
Action: Check if comment should be posted

post_comment = false
comment_content = ""

# Comment Rules:
# 1. ALWAYS post comment for feasible (approval with implementation code)
# 2. ALWAYS post comment for missing-info
# 3. NEVER post comment for agent-not-processable
# 4. ALWAYS post comment for stale issue closure
# 5. ALWAYS post comment for already-implemented (show existing code + close)

if IssueContext.outcome == "FEASIBLE":
  post_comment = true
  comment_content = build_approval_comment(IssueContext)

else if IssueContext.outcome == "MISSING_INFO":
  post_comment = true
  comment_content = build_missing_info_comment(IssueContext)

else if IssueContext.outcome == "ALREADY_IMPLEMENTED":
  post_comment = true
  comment_content = build_already_implemented_comment(IssueContext)
  IssueContext.close_issue = true

else if IssueContext.close_stale_issue == true:
  post_comment = true
  comment_content = "No activities, will be closed"

else:
  post_comment = false
```

### Step 7.5: Build Comment Content

**Reference:** Load templates from `config/ea_config_comment_templates.yaml`

```
Action: Generate comment text based on outcome using templates from config

# Load comment templates configuration
comment_templates = load_config("config/ea_config_comment_templates.yaml")

function build_approval_comment(IssueContext):
  
  # Select template based on issue type
  if IssueContext.type == "event-request":
    template = comment_templates.approved_event_request.template
  else if IssueContext.type == "request-for-external":
    template = comment_templates.approved_request_for_external.template
  else if IssueContext.type == "enum-request":
    template = comment_templates.approved_enum_request.template
  
  # Fill placeholders from IssueContext.implementation_analysis
  comment = fill_template(template, {
    implementation_description: IssueContext.implementation_analysis.description,
    code_location_description: IssueContext.implementation_analysis.location,
    code_with_event_call: IssueContext.implementation_analysis.code_in_context,
    event_publisher_code: IssueContext.implementation_analysis.event_publisher,
    filename_only: extract_filename(IssueContext.implementation_analysis.file_path)
  })
  
  # EXCLUDED from comments (per config):
  # - "Thank you for your extensibility request..." message
  # - "Team: {team_name}" line
  # - Full file paths (use filename only)
  
  return comment

function build_missing_info_comment(IssueContext):
  
  # Select template based on missing info source
  if IssueContext.missing_info_source == "REQUIREMENTS_VALIDATION":
    template = comment_templates.missing_info_requirements.template
  else if IssueContext.missing_info_source == "PROCEDURE_NOT_FOUND":
    template = comment_templates.missing_info_procedure_not_found.template
  else if IssueContext.missing_info_source == "MULTIPLE_TYPES":
    template = comment_templates.missing_info_multiple_types.template
  
  # Fill placeholders
  comment = fill_template(template, {
    author_name: IssueContext.author,
    missing_items_list: format_missing_items(IssueContext.missing_items),
    target_procedure: IssueContext.target_procedure,
    target_object: IssueContext.target_object,
    suggestion_section: IssueContext.suggestion
  })
  
  return comment

function extract_filename(full_path):
  # Extract just the filename from full path
  # Example: "App\Layers\W1\BaseApp\...\PhysInvtOrderFinish.Codeunit.al"
  #       → "PhysInvtOrderFinish.Codeunit.al"
  return get_filename_from_path(full_path)
```

### Step 7.6: Post Comment

```
Action: Post comment to GitHub issue

if post_comment == true:
  # Post comment via GitHub API
  post_issue_comment(issue_number, comment_content)
  log_message("Posted comment to issue #{issue_number}")
  
  # Increment iteration counter
  if IssueContext.outcome == "MISSING_INFO":
    IssueContext.iteration_count += 1
    store_iteration_count(issue_number, IssueContext.iteration_count)
```

---

## Issue State Management

### Step 7.7: Close Issue if Needed

```
Action: Close issue for stale scenarios

if IssueContext.close_stale_issue == true:
  # Close issue via GitHub API
  close_issue(
    issue_number,
    reason = "No activity for 30+ days with missing-info label"
  )
  log_message("Closed stale issue #{issue_number}")
```

---

## Label Application Scenarios

### Scenario 1: Feasible Request (Success)
```
Input:
  - outcome = "FEASIBLE"
  - type = "event-request"
  - team = "Finance"
  - implementation_analysis = {...}

Labels Applied (in order):
  1. "Finance" (team label first)
  2. "event-request" (type label second)

Comment: Yes (using template from config/ea_config_comment_templates.yaml)
  Template: approved_event_request
  Content:
    - "✅ Analysis complete - approved for implementation"
    - Implementation description
    - Code location with context
    - Event publisher code
    - Filename only (not full path)
  
  EXCLUDED (per config):
    - "Thank you..." message
    - "Team: Finance" line

GitHub State: Open
```

### Scenario 2: Missing Information (Requirements Failed)
```
Input:
  - outcome = "MISSING_INFO"
  - type = "event-request" (determined but NOT applied)
  - missing_info_source = "REQUIREMENTS_VALIDATION"
  - failed_requirements = [...]

Labels Applied:
  - "missing-info" ONLY
  
⚠️ NEVER apply type label when outcome is MISSING_INFO!

Note: Type "event-request" may have been determined during analysis,
      but is NEVER applied when requesting clarification/justification.
      Type labels are ONLY applied on successful (FEASIBLE) outcome.

Comment: Yes (using template from config/ea_config_comment_templates.yaml)
  Template: missing_info_requirements
  Content:
    - Greeting with @author mention
    - Link to Extensibility Guidelines
    - List of missing requirements with explanations
    - Re-analyze prompt

GitHub State: Open
```

### Scenario 3: Agent Not Processable (Blocker)
```
Input:
  - outcome = "AGENT_NOT_PROCESSABLE"
  - blocker_reason = "Object not found in codebase"

Labels Applied:
  - "agent-not-processable"

Comment: None

GitHub State: Open
```

### Scenario 4: Stale Issue (30+ Days)
```
Input:
  - close_stale_issue = true
  - existing labels = ["missing-info"]

Labels Applied:
  - Keep "missing-info" (no changes)

Comment: "No activities, will be closed"

GitHub State: Closed
```

### Scenario 5: Type Determined, But Blocked Later
```
Input:
  - outcome = "AGENT_NOT_PROCESSABLE"
  - type = "event-request" (determined but not applied)
  - blocker_reason = "Similar event already exists"

Labels Applied:
  - "agent-not-processable" ONLY

Note: Type "event-request" was determined but NOT applied
      (type/team labels only applied together on success)

Comment: None

GitHub State: Open
```

### Scenario 6: Ambiguous Type (Cannot Classify)
```
Input:
  - outcome = "MISSING_INFO"
  - type = None
  - missing_info_source = "TYPE_CLASSIFICATION"
  - clarification_needed = "Cannot determine request type from description"

Labels Applied:
  - "missing-info" ONLY

Comment: Yes
  - Explain ambiguity
  - Ask for clarification

GitHub State: Open

Note: No type label - MISSING_INFO outcome NEVER gets type labels
```

### Scenario 7: Already Implemented (100% Match)
```
Input:
  - outcome = "ALREADY_IMPLEMENTED"
  - type = "event-request" (determined during analysis)
  - existing_code = "[IntegrationEvent...] local procedure OnAfterConfirmPost(var PurchaseHeader...)"
  - existing_location = "PurchPostPrint.Codeunit.al"

Labels Applied:
  - NONE (issue will be closed)

Comment: Yes (using already_implemented template from config)
  - "✅ Good news! This is already implemented in the codebase."
  - Show existing event signature
  - Show filename
  - Explain author can use existing implementation

GitHub State: CLOSED (state_reason: "completed")

Note: 
  - This is a SUCCESS scenario - author's need is already met
  - Issue is closed because no implementation work is needed
  - Comment helps author find and use existing code
  - No labels applied since issue is being closed

Examples that trigger this scenario:
  - Author requests "Add var to PurchaseHeader" but it already has var
  - Author requests event that already exists with same signature
  - Author requests procedure to be public but it's already public
  - Author requests enum value that already exists
```

---

## Special Cases

### Case 1: Reprocessing After Author Response
```
Scenario: Issue has "missing-info", author responded, now feasible

Action:
  1. Remove "missing-info" label (Step 7.2)
  2. Apply team + type labels as pair (Step 7.3)
     - Team label first: "Finance"
     - Type label second: "event-request"
  3. Post approval comment using template (Step 7.4-7.6)
  4. Issue ready for team to handle

Labels Before: ["missing-info"]
Labels After: ["Finance", "event-request"]
Comment: Uses approved_event_request template from config
  - "✅ Analysis complete - approved for implementation"
  - Implementation details + code
  - Filename only (no full path, no team line)
```

### Case 2: Multiple Sub-Types, All Blocked
```
Scenario: Issue requests 2 sub-types, both fail validation

Action:
  1. Apply "missing-info" label ONLY
  2. NO type or team labels (processing incomplete)
  3. Post comment explaining ALL failures
  4. Single consolidated comment (not separate per sub-type)

Comment Structure:
  - "The following requirements failed:"
  - List all failures from both sub-types
  - Provide guidance for each

Note: Type was determined but not applied (missing-info outcome)
```

### Case 3: Iteration Limit Reached
```
Scenario: Issue has been reprocessed max_iterations times

Action:
  1. Apply "agent-not-processable" label
  2. Remove "missing-info" label
  3. Post final comment explaining limit reached
  4. Suggest manual review by team

Note: Iteration limit prevents infinite loops of agent-author exchanges
```

### Case 4: Type Changed After Reprocessing
```
Scenario: 
  - Initial: Missing-info (type determined but not applied)
  - Reprocessing: Author clarified, now feasible with different type

Action:
  1. Remove "missing-info" label (Step 7.2)
  2. Apply team + type labels as pair (Step 7.3)
     - Team label first: "Integration"
     - Type label second: "request-for-external"
  3. Post approval comment with implementation code (Step 7.4-7.6)

Labels Before: ["missing-info"]
Labels After: ["Integration", "request-for-external"]
Comment: "✅ Analysis complete - approved for implementation" + code

Note: Type was determined in first iteration but not applied
      (type/team only applied together on success)
```

---

## Implementation Notes

### GitHub API Operations:
```
CRITICAL: Execute operations SEQUENTIALLY, one at a time. NEVER combine multiple
operations in a single API call. Always wait for each operation to complete
before starting the next one.

Execution Order (when multiple actions needed):
  1. First: Label operations (add/remove) - use mcp_github_github_issue_write with ONLY labels parameter
  2. Then: Post comment - use mcp_github_github_add_issue_comment (SEPARATE tool)
  3. Finally: Close issue (if applicable) - SEPARATE call

⚠️ CRITICAL WARNING - Label Application:
  When applying labels using mcp_github_github_issue_write:
  - ONLY pass the "labels" parameter
  - NEVER pass "body" parameter when applying labels
  - Passing "body" will OVERWRITE the issue description!
  
  ❌ WRONG - This overwrites the issue description:
     mcp_github_github_issue_write(
       method: "update",
       labels: ["Finance", "event-request"],
       body: "Comment text..."  // ← WRONG! This replaces issue description!
     )
  
  ✅ CORRECT - Apply labels only:
     mcp_github_github_issue_write(
       method: "update",
       owner: "microsoft",
       repo: "ALAppExtensions",
       issue_number: 12345,
       labels: ["Finance", "event-request"]
       // No body parameter!
     )
  
  ✅ CORRECT - Post comment separately:
     mcp_github_github_add_issue_comment(
       owner: "microsoft",
       repo: "ALAppExtensions",
       issue_number: 12345,
       body: "Comment text..."
     )

Operations Used:
  - mcp_github_github_issue_read (method: "get") → Get issue details including labels
  - mcp_github_github_issue_write (method: "update", labels only) → Add/update labels
  - mcp_github_github_add_issue_comment → Post comment (ALWAYS use this for comments!)
  - mcp_github_github_issue_write (method: "update", state: "closed") → Close issue

WRONG - Never do this:
  - Passing "body" parameter when applying labels (overwrites issue description!)
  - Combining comment + close in single API call
  - Updating issue body while closing
  - Multiple operations in parallel
  - Using issue_write with body to post comments

CORRECT - Always do this:
  - Use issue_write with ONLY labels parameter for label operations
  - Use add_issue_comment for ALL comments (never issue_write body)
  - post_comment(...) → wait for completion
  - close_issue(...) → separate call after comment succeeds

Idempotency:
  - Adding existing label: No-op, safe
  - Removing non-existent label: No-op, safe
  - Multiple runs: Safe, won't duplicate labels or comments
```

### Iteration Tracking:
```
Storage: GitHub issue metadata or external database

Data Structure:
  {
    issue_number: 12345,
    iteration_count: 2,
    last_processed: "2025-11-28T10:30:00Z",
    outcome_history: [
      {iteration: 1, outcome: "MISSING_INFO", reason: "..."},
      {iteration: 2, outcome: "MISSING_INFO", reason: "..."}
    ]
  }

Check Before Processing:
  - Load iteration_count for issue
  - Compare against max_iterations from config
  - If limit reached: Apply agent-not-processable
```

### Comment Formatting:
```
Reference: config/ea_config_comment_templates.yaml → formatting_rules

Use Markdown for rich formatting:
  - **Bold** for section headers
  - `code` for object/procedure names
  - Bullet lists for requirements
  - --- Horizontal rule for separators
  - ```al code blocks for AL code

Filename Format:
  - Use filename only, NOT full path
  - Format: {ObjectName}.{ObjectType}.al
  - Example: "PhysInvtOrderFinish.Codeunit.al"
  - NOT: "App\Layers\W1\BaseApp\...\PhysInvtOrderFinish.Codeunit.al"

Excluded Elements (per config):
  - "Thank you for your extensibility request..." intro
  - "Team: {team_name}" line (team shown via label)
  - Full file paths

Keep comments:
  - Professional tone
  - Clear and actionable
  - Specific (not generic)
  - Concise
```

### Error Handling:
```
If label application fails:
  - Log error with details
  - Retry up to 3 times
  - If still fails: Alert human operator
  - Continue with comment posting (don't block)

If comment posting fails:
  - Log error with details
  - Retry up to 3 times
  - If still fails: Alert human operator
  - Labels already applied, issue partially processed

If issue close fails (stale scenario):
  - Log error with details
  - Retry up to 3 times
  - If still fails: Alert human operator
  - Comment already posted, manual close needed
```

### Logging:
```
Log Messages:

Success:
  "Issue #[number] processing complete - applied labels: [label1, label2]"
  "Issue #[number] comment posted - missing-info iteration [count]"
  "Issue #[number] closed - stale for 30+ days"

Label Application:
  "Applied label '[label]' to issue #[number]"
  "Removed label '[label]' from issue #[number]"
  "Label '[label]' already exists on issue #[number], skipping"

Blocker:
  "Issue #[number] marked as agent-not-processable - reason: [blocker_reason]"

Iteration Limit:
  "Issue #[number] reached iteration limit ([max]) - marking as agent-not-processable"
```

---

## Final Output

### Processing Complete:
```
All steps finished, issue now in one of these states:

1. Ready for Team:
   - Type label applied
   - Team label applied
   - No pending actions
   - Team can start implementation

2. Awaiting Author Response:
   - "missing-info" label applied
   - Comment posted with specific requests
   - Agent waits for author update
   - Will reprocess when author responds

3. Cannot Process:
   - "agent-not-processable" label applied
   - No comment (environmental/technical blocker)
   - Human review may be needed
   - Not eligible for reprocessing

4. Closed (Stale):
   - Issue closed
   - Comment explaining closure reason
   - No further processing
```

---

## Next Step

**This is the final step.** Processing complete.

### If More Issues in Queue:
Return to [01-workflow.md](01-workflow.md) to process next issue in queue.

### If Queue is Empty:
- Log: "All issues processed. Queue is empty."
- Agent enters idle state
- Wait for new issues to be added to queue
- Can be triggered by:
  - Scheduled polling (e.g., every 15 minutes)
  - Webhook notification (new issue created)
  - Manual trigger by operator

---

**Version:** 1.0  
**Last Updated:** November 28, 2025
