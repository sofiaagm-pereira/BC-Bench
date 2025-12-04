# Step 3: Request Type Classification

**Purpose:** Determine the specific type of extensibility request to apply appropriate validation and analysis rules.

---

## Overview

This step classifies the issue into one of the predefined request types. Accurate classification is critical because each type has:
- Different minimum requirements
- Different codebase analysis rules
- Different team routing logic
- Different approval criteria

**Important:** Type classification uses natural language understanding and keyword detection, combined with author intent analysis.

---

## Supported Request Types

### Primary Types:

| Type Label | Description | Common Keywords |
|------------|-------------|-----------------|
| `event-request` | Event publisher/subscriber requests | "publisher", "subscriber", "IntegrationEvent", "event", "OnBefore", "OnAfter" |
| `request-for-external` | Accessibility change requests | "local" to "global", change "accessibility", "public procedure", "protected var" |
| `enum-request` | Enum-related requests | Convert "option" to "enum", define/update "enum" type |
| `extensibility-enhancement` | Other enhancement requests | Improvements not matching other types (catch-all) |
| `bug` | Bug reports | Bug-related content, error reports, unexpected behavior |

### Event Request Sub-Types:

Within `event-request` type, further classify as:

| Sub-Type | Identification Criteria | Requirements |
|----------|------------------------|--------------|
| **IsHandled Event** | Author EXPLICITLY requests "IsHandled", "bypass", "skip", "prevent execution" | Strict minimum requirements |
| **Regular Event** | All other event requests (DEFAULT) | Standard minimum requirements |

**⚠️ CRITICAL RULE - IsHandled Sub-Type Detection:**
```
The agent must NEVER classify an event request as "IsHandled Event" unless the author 
EXPLICITLY uses one of these keywords/phrases:
  - "IsHandled" (exact keyword)
  - "bypass" the logic/check/validation
  - "skip" the standard behavior
  - "prevent" execution/processing
  - "handled" parameter
  - "override" or "replace" the standard logic

If NONE of these explicit indicators are present:
  → Classify as "Regular Event" (DEFAULT)
  → Implement WITHOUT IsHandled parameter
  → Agent must NOT suggest or add IsHandled on its own

Rationale: IsHandled events allow bypassing critical business logic and carry higher risk.
           The agent should never escalate the scope of a request beyond what was explicitly asked.
```

**Note:** An issue can contain BOTH IsHandled and Regular events. Process each according to its sub-type requirements.

---

## Type Detection Logic

### Step 3.1: Keyword Extraction

```
Action: Analyze issue title, description, and all comments
Source: IssueContext.title, IssueContext.description, IssueContext.comments[]

Extract keywords related to:
  - Event-related: "event", "publisher", "subscriber", "OnBefore", "OnAfter", "IntegrationEvent"
  - IsHandled-specific (ONLY if explicitly present): "IsHandled", "bypass", "skip", "prevent", "handled"
  - Access-related: "local", "global", "public", "internal", "protected", "accessibility", "external"
  - Enum-related: "enum", "option", "extensible enum"
  - Enhancement-related: "improve", "enhance", "add", "expose"
  - Bug-related: "bug", "error", "fails", "broken", "incorrect"

⚠️ IMPORTANT: Do NOT assume IsHandled intent. Only detect if explicitly stated.
```

### Step 3.2: Primary Intent Analysis

```
Action: Determine author's main request
Focus: What is the author asking to be done?

Rules:
  1. Read full issue description
  2. Identify stated problem/goal
  3. Determine primary objective (not secondary details)
  4. Match to type based on core request
  5. For event requests: Check if IsHandled is EXPLICITLY requested (not inferred)
```

### Step 3.3: Type Assignment

```
Decision Tree:

if contains("bug", "error", "fails") AND describes_unexpected_behavior:
  → type = "bug"

else if contains("event", "publisher", "subscriber", "OnBefore", "OnAfter"):
  → type = "event-request"
  → Check for "IsHandled" keyword:
      if found:
        → sub_type = "IsHandled Event"
      else:
        → sub_type = "Regular Event"

else if contains("local to global", "make public", "change accessibility", "protected var"):
  → type = "request-for-external"

else if contains("enum", "option to enum", "extensible enum"):
  → type = "enum-request"

else if contains("improve", "enhance", "expose"):
  → type = "extensibility-enhancement"

else:
  → type = "agent-not-processable" (unclear intent)
```

---

## Ambiguity Resolution

### Common Ambiguous Scenarios

#### Scenario A: "Add event to public procedure"
```
Keywords Match:
  - "event" → event-request
  - "public procedure" → request-for-external

Analysis:
  - Primary Intent: Add event functionality
  - Secondary Detail: Procedure happens to be public
  
Decision: type = "event-request"
Reasoning: Author's focus is event addition, not access level change
```

#### Scenario B: "Change procedure from local to global"
```
Keywords Match:
  - "change access" → request-for-external
  - "procedure" → generic

Analysis:
  - Primary Intent: Change accessibility
  - Secondary Detail: Object is a procedure
  
Decision: type = "request-for-external"
Reasoning: Author's focus is access level change
```

#### Scenario C: "Make enum and use in event"
```
Keywords Match:
  - "enum" → enum-request
  - "event" → event-request

Analysis:
  - Determine which is the main request
  - If enum creation is goal → enum-request
  - If event integration is goal → event-request
  
Decision: Ask author to clarify primary objective
Action: Post comment requesting clarification
Label: "missing-info"
STOP processing
```

#### Scenario D: Multiple Distinct Main Types
```
Example: "Add event AND change procedure access level AND create enum"

Analysis:
  - Three different primary types detected
  - Cannot process multiple distinct types in single issue
  
Decision: Request author to split into separate issues
Action: Post comment explaining need for separate issues
Label: "missing-info"
STOP processing

Comment Template:
  "This issue contains multiple distinct request types:
   - Event request
   - Access level change
   - Enum creation
   
   Please create separate issues for each type to ensure proper processing and tracking."
```

#### Scenario E: Unclear After Analysis
```
Situation: Agent cannot determine primary intent despite full analysis

Analysis:
  - Multiple types equally plausible
  - No clear primary objective
  - Ambiguous language throughout
  
Decision: type = "agent-not-processable"
Action: Apply "agent-not-processable" label ONLY, NO comment
STOP processing
```

---

## Multiple Sub-Types Within Same Main Type

### Allowed Scenario:
```
Example: Issue requests both IsHandled event AND regular event

Analysis:
  - Both are sub-types of "event-request" (same main type)
  - Allowed to process together
  
Action:
  - type = "event-request"
  - sub_types = ["IsHandled Event", "Regular Event"]
  - Process EACH sub-type according to its specific requirements
  - Apply all-or-nothing rule (see below)
```

### All-or-Nothing Rule:
```
CRITICAL: If ANY sub-type is not feasible, reject ALL sub-types in the issue

Example:
  - Issue has 2 IsHandled events + 1 Regular event
  - One IsHandled event violates absolute restriction
  - Result: Reject ALL THREE events (even though 2 are feasible)
  
Rationale:
  - Partial implementation creates confusion
  - Author expects complete solution
  - Maintain issue integrity
  
Action:
  - Explain which item(s) blocked and why
  - Label as "agent-not-processable" if absolute restriction
  - Label as "missing-info" if author can address
```

---

## Output Data

### On Success (Type Determined):
```
Output to Step 4:
  - type: string (e.g., "event-request")
  - sub_types: array (e.g., ["IsHandled Event", "Regular Event"])
  - IssueContext (passed through with type added)

Action: Proceed to Step 4 (Requirements Validation)
```

### On Failure (Type Unclear):
```
Output: None (issue labeled)

Scenarios:
  1. Multiple distinct main types → missing-info label + comment
  2. Cannot determine intent → agent-not-processable label only
  
Action: STOP processing, move to next issue in queue
```

---

## Special Cases

### Case 1: Event Request with Access Level Change
```
Example: "Add OnBeforePost event to ChangeVAT procedure and make it public"

Analysis:
  - Two requests: event + access level change
  - BUT: Making procedure public is prerequisite for event usability
  - NOT distinct types, but related enhancement
  
Decision: type = "event-request"
Action: Process as event request, note access level change in implementation details
```

### Case 2: Enum Request for New vs. Existing Enum
```
Scenario A: "Create new enum for payment methods"
  - type = "enum-request"
  - Action: Skip codebase analysis (nothing exists yet)
  - Proceed to team assignment based on namespace
  
Scenario B: "Add value to existing PaymentMethod enum"
  - type = "enum-request"
  - Action: Perform codebase analysis to locate enum
  - Verify enum exists and is extensible
```

### Case 3: Bug vs. Enhancement
```
Example: "Procedure X should be public but it's local"

Analysis:
  - Could be bug (incorrect access level)
  - Could be enhancement (requesting change)
  
Decision:
  - If issue Type field = "Task" → request-for-external
  - If issue Type field = "Bug" → Skipped (agent doesn't process bugs)
  
Note: Step 2 already filtered out non-Task types
```

---

## Implementation Notes

### Data Source:
```
Use data from IssueContext built in Step 1
Analyze:
  - IssueContext.title
  - IssueContext.description
  - IssueContext.comments[] (all comments for context)
```

### Performance:
```
Natural language analysis is fast
No external API calls required
Should complete in < 200ms
```

### Iteration Tracking:
```
If type unclear and requires author clarification:
  - Increment iteration counter
  - Track in IssueContext for max iteration limit
```

### Error Handling:
```
If unable to parse issue text:
  - Treat as agent-not-processable
  - Apply label only, no comment
  - Log: "Skipped issue #[number]: Unable to parse request"
```

---

## Logging Format

### Log Messages:
```
Success:
  "Issue #[number] classified as type: [type], sub-types: [list]"

Ambiguity - Requires Clarification:
  "Issue #[number] requires author clarification for type classification"

Ambiguity - Cannot Determine:
  "Issue #[number] marked agent-not-processable: Unable to determine type"

Multiple Main Types:
  "Issue #[number] contains multiple main types, requesting split"
```

---

## Next Step

**On Success:** Proceed to [04-step4-requirements-validation.md](04-step4-requirements-validation.md) (Step 4: Requirements Validation)

**On Failure:** Proceed to [07-step7-labels-comments.md](07-step7-labels-comments.md) (Step 7: Label Application & Commenting)

---

**Version:** 1.0  
**Last Updated:** November 27, 2025
