# Step 5: Codebase Analysis

**Purpose:** Perform comprehensive codebase analysis to determine implementation feasibility and identify any blockers or restrictions.

---

## Overview

This step performs deep analysis of the Business Central codebase to:
1. **Locate Target Code** - Find objects, procedures, and triggers referenced in the issue
2. **Verify Feasibility** - Check if the requested change is technically possible
3. **Apply Implementation Rules** - Validate against absolute and conditional restrictions
4. **Generate Implementation Guidance** - Determine exact code changes required

**Critical Behavior:**
- **Skip entirely for new enum creation** (nothing to analyze in codebase)
- **W1 layer priority** for object location
- **Apply all-or-nothing rule** for multiple changes in single issue
- **Stop immediately** if absolute restriction detected (blocker)
- **Stop immediately** if requested change already exists (already implemented)

---

## Analysis Sources

### Configuration Files:
```
config/implementation-rules/ea_config_implementation_rules.yaml
config/implementation-rules/ea_config_implementation_rules_template.yaml
```

### Codebase Access:
- Use `semantic_search` for natural language queries
- Use `grep_search` for exact pattern matching
- Use `file_search` for finding object files by name pattern
- Priority: W1 layer first, then other layers

### Finding Object Files

**Pattern:** Use `file_search` with wildcards to locate AL object files.

**File Naming Convention in AL:**
```
[ObjectName].[ObjectType].al
```

**Search Examples:**

| Object | Search Pattern | Alternative Pattern |
|--------|---------------|---------------------|
| Codeunit 80 "Sales-Post" | `*SalesPost.Codeunit.al` | `*Sales*Post*.Codeunit.al` |
| Table 18 "Customer" | `*Customer.Table.al` | `*18*Customer.Table.al` |
| Table 37 "Sales Line" | `*SalesLine.Table.al` | `*Sales*Line.Table.al` |
| Page 21 "Customer Card" | `*CustomerCard.Page.al` | `*Customer*Card.Page.al` |
| Codeunit 12 "Gen. Jnl.-Post Line" | `*GenJnlPostLine.Codeunit.al` | `*Gen*Jnl*Post*Line*.Codeunit.al` |
| Table 39 "Purchase Line" | `*PurchaseLine.Table.al` | `*Purchase*Line.Table.al` |
| Codeunit 90 "Purch.-Post" | `*PurchPost.Codeunit.al` | `*Purch*Post*.Codeunit.al` |

**Search Strategy:**
1. First try exact pattern (spaces removed): `*SalesPost.Codeunit.al`
2. If not found, try wildcard pattern: `*Sales*Post*.Codeunit.al`
3. Always filter results to prioritize W1 layer

**Example Usage:**
```
# Looking for Codeunit 80 "Sales-Post"
file_search("*SalesPost.Codeunit.al")

# Looking for Table 37 "Sales Line"  
file_search("*SalesLine.Table.al")

# If exact match fails, use broader pattern
file_search("*Sales*Line*.Table.al")
```

---

## When to Skip This Step

### Skip Conditions:
```
Skip codebase analysis if:
  1. Type = "enum-request" AND sub-type = "new_enum"
     - New enum creation doesn't require codebase search
     - Proceed directly to Step 6 (Team Assignment)
     - Team assigned based on namespace mentioned in issue
  
  2. Type = "bug"
     - Bug issues don't require feasibility analysis
     - Skip to Step 7 for labeling

Otherwise: Perform full codebase analysis
```

---

## Analysis Process Flow

### Step 5.1: Locate Target Code

```
Action: Find objects, procedures, and triggers in codebase

# Extract target information from IssueContext
target_objects = extract_objects_from_issue(IssueContext)

for each target in target_objects:
  # Layer Priority Search - CRITICAL
  search_result = search_with_layer_priority(target)
  
  if search_result.found_in_W1:
    # Use ONLY W1 version, ignore other layers
    target.code_location = search_result.W1_path
    target.layer = "W1"
    
  else if search_result.found_in_other_layers:
    # Use first match from other layers
    target.code_location = search_result.first_match_path
    target.layer = search_result.first_match_layer
    
  else:
    # Object not found in codebase
    target.found = false
    target.blocker = "object_not_found"

# Layer Priority Rationale:
# W1 is base layer - changes to W1 objects must be in W1
# Localization overrides are irrelevant for W1 object modifications
```

### Step 5.2: Verify Code Structure

```
Action: Validate that referenced objects exist and handle missing procedures/triggers

for each target in located_objects:
  
  if target.found == false:
    # Object not found - BLOCKER
    outcome = "AGENT_NOT_PROCESSABLE"
    blocker_reason = "Object not found in codebase"
    label = "agent-not-processable"
    comment = None  # No comment for environmental blocker
    STOP processing
  
  # Object found, check for procedure/trigger
  if target.type == "trigger":
    trigger_result = find_trigger_in_object(target)
    
    if trigger_result.found == false:
      # Trigger not found - VALID scenario
      # Agent should CREATE the trigger with requested code
      target.create_new = true
      target.existing_code = None
      # Continue processing - not an error
    
    else:
      # Trigger exists - will modify existing code
      target.create_new = false
      target.existing_code = trigger_result.code
  
  else if target.type == "procedure":
    procedure_result = find_procedure_in_object(target)
    
    if procedure_result.found == false:
      # Procedure not found - Try fuzzy matching
      similar = fuzzy_match_procedures(target.procedure_name, target.code_location)
      
      if similar.match_score > 0.7:
        # Suggest similar procedure to author
        outcome = "MISSING_INFO"
        suggestion = "Did you mean '{similar.procedure_name}'?"
        label = "missing-info"
        comment = build_procedure_not_found_comment(target, suggestion)
        increment_iteration_counter()
        STOP processing
      
      else:
        # No similar procedure - Assume refactoring
        outcome = "MISSING_INFO"
        suggestion = "Procedure may have been refactored or renamed"
        label = "missing-info"
        comment = build_procedure_not_found_comment(target, suggestion)
        increment_iteration_counter()
        STOP processing
```

### Step 5.2.5: Check if Already Implemented

```
Action: Compare requested changes against existing codebase to detect if already implemented

CRITICAL: Before proceeding with implementation rules, check if any requested
changes ALREADY EXIST in the codebase (100% match).

# Initialize tracking arrays
already_implemented_changes = []
pending_changes = []

for each requested_change in IssueContext.requested_changes:
  
  existing_code = get_existing_code(target_object, target_location)
  
  # Compare requested change with existing code
  if requested_change matches existing_code 100%:
    # This specific change is ALREADY IMPLEMENTED
    already_implemented_changes.append({
      change: requested_change,
      existing_code: existing_code,
      existing_location: target_location
    })
  else:
    # This change still needs to be implemented
    pending_changes.append(requested_change)

# Store results in IssueContext
IssueContext.already_implemented_changes = already_implemented_changes
IssueContext.pending_changes = pending_changes

# Determine outcome based on results
if pending_changes.length == 0:
  # ALL changes are already implemented
  outcome = "ALL_ALREADY_IMPLEMENTED"
  
  # Skip Steps 5.3, 5.4, 5.5, Step 6
  # Go directly to Step 7 to close the issue
  STOP processing → Step 7

else if already_implemented_changes.length > 0:
  # SOME changes are already implemented, SOME still pending
  outcome = "PARTIAL_ALREADY_IMPLEMENTED"
  
  # Continue processing with pending_changes only
  # Already implemented items will be noted in final comment
  IssueContext.requested_changes = pending_changes  # Process only pending
  CONTINUE to Step 5.3

else:
  # NO changes are already implemented
  # Continue normal processing
  CONTINUE to Step 5.3


IMPORTANT - All-or-Nothing Rule Still Applies:
  - The all-or-nothing rule applies ONLY to pending_changes
  - If any pending change is blocked → reject all pending changes
  - Already implemented changes are noted in comment regardless
  - Already implemented changes do NOT count toward feasibility of pending changes

Example Scenarios:

Scenario A: Issue has 3 requests, 1 already implemented, 2 pending
  - Request 1: Add var to parameter → ALREADY IMPLEMENTED
  - Request 2: Add new event X → PENDING (feasible)
  - Request 3: Add new event Y → PENDING (feasible)
  
  Result: 
    - Process Requests 2 and 3 together (all-or-nothing for these two)
    - If both feasible → APPROVE with comment noting Request 1 already exists
    - Comment includes: existing code for Request 1 + implementation for 2 and 3

Scenario B: Issue has 3 requests, 1 already implemented, 1 pending feasible, 1 pending blocked
  - Request 1: Add var to parameter → ALREADY IMPLEMENTED
  - Request 2: Add new event X → PENDING (feasible)
  - Request 3: Add IsHandled in OnDelete → PENDING (BLOCKED)
  
  Result:
    - Request 3 is blocked → ALL pending changes rejected (all-or-nothing)
    - outcome = "AGENT_NOT_PROCESSABLE" for pending changes
    - Comment notes: Request 1 already exists, Requests 2-3 cannot be processed

Scenario C: Issue has 2 requests, both already implemented
  - Request 1: Add var to parameter → ALREADY IMPLEMENTED
  - Request 2: Make procedure public → ALREADY IMPLEMENTED
  
  Result:
    - outcome = "ALL_ALREADY_IMPLEMENTED"
    - Post comment showing both existing implementations
    - Close the issue
```

Examples of Already Implemented Detection:

1. Event Request - Parameter already has 'var' modifier:
   - Author requests: "Add var to PurchaseHeader parameter"
   - Existing event: OnAfterConfirmPost(var PurchaseHeader: Record "Purchase Header")
   - Result: ALREADY_IMPLEMENTED (parameter already has 'var')

2. Event Request - Event already exists with same signature:
   - Author requests: "Add OnBeforePost event with SalesHeader parameter"
   - Existing event: OnBeforePost(var SalesHeader: Record "Sales Header")
   - Result: ALREADY_IMPLEMENTED (event already exists)

3. Request-for-External - Procedure already public:
   - Author requests: "Make ValidateCustomer procedure public"
   - Existing code: "procedure ValidateCustomer(...)" (already public)
   - Result: ALREADY_IMPLEMENTED (procedure already public)

4. Enum Request - Enum value already exists:
   - Author requests: "Add 'Electronic' value to PaymentMethod enum"
   - Existing enum: contains 'Electronic' value
   - Result: ALREADY_IMPLEMENTED (value already exists)

---

### Step 5.3: Apply All Implementation Rules

```
Action: Load and apply all implementation rules from config

# Load all rules from config (global + type-specific + sub-type-specific)
all_rules = load_all_implementation_rules(IssueContext.type, IssueContext.sub_types)

# Rules include:
#   - Analysis rules (pattern detection, similarity checks, duplicate detection)
#   - Restriction rules (code restrictions, limitations, blockers)
#   - Safety validation rules (safety checks, risk assessment)
#   - Any other rule categories defined in config

for each rule in all_rules:
  
  result = evaluate_rule(rule, target_objects, IssueContext)
  
  if result.violated:
    # Handle based on rule action
    apply_rule_action(rule.action, result)
    # May STOP processing or continue based on rule severity
```

### Step 5.4: Validate Multiple Changes

```
Action: Apply multi-change validation rules from config

if IssueContext contains multiple requested changes:
  
  # Load multi-change validation rules
  multi_change_rules = load_multi_change_validation_rules()
  
  for each rule in multi_change_rules:
    result = evaluate_multi_change_rule(rule, requested_changes, IssueContext)
    
    if result.violated:
      # Handle based on rule action
      apply_rule_action(rule.action, result)
      # May STOP processing or continue based on rule
```

### Step 5.5: Generate Analysis Output

```
Action: Generate implementation analysis or failure output

if all rules passed:
  
  # Generate implementation guidance
  implementation_guidance = generate_implementation_guidance(
    target_objects,
    IssueContext
  )
  
  # Add to IssueContext for Step 6
  IssueContext.implementation_analysis = implementation_guidance
  
  outcome = "FEASIBLE"
  # Proceed to Step 6

else:
  # Rule violation detected - output already set by rule action
  # Proceed to Step 7
```

---

## Output Data

### On Success (Feasible):
```
Output to Step 6:
  - analysis_completed: true
  - implementation_analysis: generated by implementation guidance function
  - already_implemented_changes: array (items already in codebase, may be empty)
  - pending_changes: array (items to be implemented)
  - IssueContext (with implementation_analysis added)

Action: Proceed to Step 6 (Team Assignment)

Note: If already_implemented_changes is not empty, the final comment in Step 7
      will include both the existing implementations AND the new implementation guidance.
```

### On All Already Implemented (100% of requests exist):
```
Output to Step 7:
  - analysis_completed: true
  - outcome: "ALL_ALREADY_IMPLEMENTED"
  - already_implemented_changes: array (all requested changes with existing code)
  - pending_changes: [] (empty - nothing to implement)

Action:
  - Skip Step 6 (Team Assignment) - not needed
  - Proceed directly to Step 7
  - Post comment showing ALL existing implementations
  - Close the issue (all requests already satisfied)
  - STOP processing

⚠️ CRITICAL: Only close issue when ALL requests are already implemented.
```

### On Partial Already Implemented (some requests exist, some pending):
```
Output to Step 6:
  - analysis_completed: true
  - outcome: "PARTIAL_ALREADY_IMPLEMENTED"
  - already_implemented_changes: array (items already in codebase)
  - pending_changes: array (items still to be implemented)
  - implementation_analysis: generated for pending_changes only

Action:
  - Continue to Step 6 (Team Assignment) for pending changes
  - Apply all-or-nothing rule to pending_changes only
  - Final comment will include:
    - Existing implementations (already_implemented_changes)
    - New implementation guidance (pending_changes)
  - Do NOT close issue (pending work remains)
  - STOP processing

⚠️ CRITICAL: This is a SUCCESS scenario - the author's need is already met.
   The issue should be CLOSED with a helpful comment showing the existing code.
```

### On Blocker Detected (Agent-Not-Processable):
```
Output to Step 7:
  - analysis_completed: false
  - blocker_detected: true
  - blocker_reason: string
  - alternative_suggestion: string (if applicable)

Action:
  - Proceed to Step 7 for labeling
  - Apply "agent-not-processable" label ONLY
  - NO comment (environmental/technical blocker)
  - STOP processing
```

### On Missing Information:
```
Output to Step 7:
  - analysis_completed: false
  - missing_info_detected: true
  - clarification_needed: string
  - suggestion: string (if applicable)
  - iteration_count: incremented

Action:
  - Proceed to Step 7 for labeling and commenting
  - Post comment with specific clarification request
  - Add "missing-info" label ONLY (⚠️ NEVER add type label!)
  - STOP processing

⚠️ CRITICAL: Do NOT apply type labels when requesting clarification.
   Type label is ONLY applied on FEASIBLE outcome.
```

### On Proposed Alternative:
```
Output to Step 7:
  - analysis_completed: false
  - alternative_proposed: true
  - alternative_description: string
  - requires_confirmation: true
  - iteration_count: incremented

Action:
  - Proceed to Step 7 for labeling and commenting
  - Post comment explaining alternative approach
  - Add "missing-info" label ONLY (⚠️ NEVER add type label!)
  - STOP processing

⚠️ CRITICAL: Even when suggesting an alternative, do NOT apply type labels.
   Type label is ONLY applied on FEASIBLE outcome after author confirms.
```

---

## Special Cases

### Case 1: Already Implemented (100% Match)
```
Scenario: Requested change already exists in codebase

Examples:
  - Event parameter already has 'var' modifier that author requested
  - Event already exists with exact signature requested
  - Procedure is already public when author requested to make it public
  - Enum value already exists when author requested to add it

Detection:
  - Compare requested change against existing code
  - Must be 100% match (not partial)
  - Check exact signatures, modifiers, access levels

Action:
  - outcome = "ALREADY_IMPLEMENTED"
  - Skip Step 6 (Team Assignment) entirely
  - Proceed directly to Step 7
  - Post comment with existing implementation code
  - Close the issue
  - STOP processing

Rationale:
  - Author's need is already satisfied
  - No implementation work required
  - Closing issue keeps backlog clean
  - Comment helps author find and use existing code
```

### Case 2: New Enum Creation
```
Scenario: Type = enum-request, sub-type = new_enum

Action:
  - Skip Step 5 entirely (no codebase analysis needed)
  - Proceed directly to Step 6 (Team Assignment)
  - Team assigned based on namespace in issue description
```

### Case 3: Object Not Found vs. Procedure/Trigger Not Found
```
Object Not Found:
  - Outcome: AGENT_NOT_PROCESSABLE
  - Label: "agent-not-processable"
  - Comment: None (environmental blocker)
  - Rationale: Object doesn't exist in codebase

Trigger Not Found (within existing object):
  - Outcome: CONTINUE (valid scenario)
  - Action: Mark trigger for creation
  - Rationale: Empty triggers are not defined in code
  - Agent will create the trigger with requested changes

Procedure Not Found (within existing object):
  - Outcome: MISSING_INFO
  - Label: "missing-info"
  - Comment: Request clarification, suggest fuzzy matches
  - Rationale: Author may have typo or outdated info
```

### Case 4: Multiple Changes with Mixed Feasibility
```
Scenario: Issue requests 3 changes, 2 are feasible, 1 is blocked

Action:
  - Apply all-or-nothing rule
  - Reject ALL changes (even feasible ones)
  - Outcome: AGENT_NOT_PROCESSABLE
  - Label: "agent-not-processable"
  - Comment: None
  - Rationale: Partial implementation creates confusion
```

### Case 5: W1 Layer Priority
```
Scenario: Object exists in both W1 and localization layers

### Case 3: Multiple Changes with Mixed Feasibility
```
Scenario: Issue requests multiple changes with different feasibility

Action:
  - Apply multi-change validation rules from config
  - Rules define behavior (all-or-nothing, partial-allowed, etc.)
  - Outcome depends on rule action
  - Label and comment based on rule configuration
```ll restriction rules, severity levels, check methods, safety validations, and actions are defined in:**
- `config/implementation-rules/ea_config_implementation_rules.yaml`

**Rule Structure:**
1. **Absolute Restrictions** - Auto-reject, no comment (blockers)
   - Loaded from `implementation_rules.absolute_restrictions[]`
   - Apply to specific types via `applies_to` field
   - Action: Stop immediately, label as "agent-not-processable"

2. **Conditional Restrictions** - Require analysis/clarification
   - Loaded from `implementation_rules.conditional_restrictions[]`
   - May suggest alternatives or request justification
   - Action: Request clarification, label as "missing-info"

3. **Type-Specific Safety Checks** - Validation rules per type
## Implementation Rules Reference

**All analysis rules, restriction rules, safety validations, and actions are defined in:**
- `config/implementation-rules/ea_config_implementation_rules.yaml`

**Rule Hierarchy:**
1. **Global Rules** - Apply to ALL request types
2. **Type-Specific Rules** - Apply to specific request type (all sub-types)
3. **Sub-Type-Specific Rules** - Apply only to specific sub-type

**Rule Categories:**
- **Analysis Rules** - Pattern detection, similarity checks, duplicate detection
- **Restriction Rules** - Code restrictions, limitations, blockers
- **Safety Validation Rules** - Safety checks, risk assessment
- **Multi-Change Rules** - Validation for multiple changes in single issue

**Rule Application:**
- Load rules based on `IssueContext.type` and `IssueContext.sub_types`
- Apply global rules first, then type-specific, then sub-type-specific
- Each rule defines: `check_method`, `severity`, `action`
- Actions: `auto_reject`, `request_clarification`, `suggest_alternative`, `warning`

**Do NOT duplicate rule details in this file.** Always load from config and apply dynamically.
  - Log error with search query
  - Retry with alternative search pattern
  - If still fails: Treat as agent-not-processable
  - Cannot proceed without code location

If implementation rules config cannot be loaded:
  - Log error
  - Treat as agent-not-processable
  - Cannot proceed without rules validation
```

### Logging:
```
Log Messages:

Success:
  "Issue #[number] codebase analysis completed - feasible"

Object Not Found:
  "Issue #[number] blocker: Object [name] not found in codebase"

Procedure Not Found:
  "Issue #[number] needs clarification: Procedure [name] not found in [object]"

Restriction Violated:
  "Issue #[number] blocker: Absolute restriction [rule_id] violated"

Alternative Suggested:
  "Issue #[number] alternative approach suggested: [description]"
```

---

## Next Step

**On Success:** Proceed to [06-step6-team-assignment.md](06-step6-team-assignment.md) (Step 6: Team Assignment)

**On Failure:** Proceed to [07-step7-labels-comments.md](07-step7-labels-comments.md) (Step 7: Label Application & Commenting)

---

**Version:** 1.0  
**Last Updated:** November 28, 2025
