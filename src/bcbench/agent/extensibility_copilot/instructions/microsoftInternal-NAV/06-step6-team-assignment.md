# Step 6: Team Assignment

**Purpose:** Assign the issue to the appropriate team based on namespace analysis of target objects.

---

## Overview

This step determines which team should handle the issue by:
1. **Extract Namespaces** - Identify namespaces from target objects analyzed in Step 5
2. **Match to Teams** - Compare namespaces against team ownership mapping
3. **Count Matches** - Calculate which team has most matching namespaces
4. **Apply Tie-Breaker** - Resolve ties using defined strategy
5. **Assign Team Label** - Apply appropriate team label to issue

**Critical Behavior:**
- **Skip for bugs** - Bug issues don't require team assignment via namespace
- **Multiple namespaces** - Count all matches across all target objects
- **No match found** - Mark as agent-not-processable
- **Alphabetical tie-breaker** - When counts are equal

---

## Configuration Source

### Team Namespace Mapping:
```
config/team-configuration/ea_config_team_namespace_mapping.yaml
```

**Configuration Structure:**
- Team definitions with namespace lists
- Match strategy (full namespace then root)
- Tie-breaker rules
- Fallback handling

**Do NOT duplicate team/namespace mappings in this file.** Always load from config.

---

## When to Skip This Step

### Skip Conditions:
```
Skip team assignment if:
  1. Type = "bug"
     - Bugs are not assigned via namespace mapping
     - Skip to Step 7 for labeling only
  
  2. Previous step marked as agent-not-processable
     - Already determined issue cannot be processed
     - Skip to Step 7 for final labeling

Otherwise: Perform team assignment
```

---

## Team Assignment Process Flow

### Step 6.1: Extract Namespaces

```
Action: Extract namespaces from analyzed target objects

# Use implementation_analysis from Step 5
target_objects = IssueContext.implementation_analysis.code_changes

namespaces = []
for each target in target_objects:
  # Extract namespace from object location
  namespace = extract_namespace_from_object(target.file, target.object_name)
  
  if namespace:
    namespaces.append({
      object: target.object_name,
      namespace: namespace,
      layer: target.layer
    })

if namespaces is empty:
  # No objects identified - BLOCKER
  outcome = "AGENT_NOT_PROCESSABLE"
  blocker_reason = "No target objects identified for team assignment"
  label = "agent-not-processable"
  comment = None
  STOP processing
  # Proceed to Step 7

# Store for next step
IssueContext.extracted_namespaces = namespaces
```

### Step 6.2: Load Team Configuration

```
Action: Load team namespace mappings from config

# Load team configuration
team_config = load_team_namespace_mapping_config()

teams = team_config.team_namespace_mapping
assignment_algorithm = team_config.assignment_algorithm
tie_breaker_rules = team_config.tie_breaker
```

### Step 6.3: Match Namespaces to Teams

```
Action: Match each namespace against team ownership mappings

team_matches = {}  # {team_name: match_count}

for each team in teams:
  match_count = 0
  
  for each extracted_namespace in IssueContext.extracted_namespaces:
    # Apply match strategy from config
    if matches_team_namespace(extracted_namespace.namespace, team.namespaces, team.match_strategy):
      match_count += 1
  
  if match_count > 0:
    team_matches[team.name] = match_count

# Match Strategy (from config):
#   "full_namespace_then_root":
#     1. Try exact match on full namespace (e.g., "Finance.CashFlow")
#     2. If no match, try root namespace only (e.g., "Finance")
```

### Step 6.4: Determine Winning Team

```
Action: Select team with highest match count, apply tie-breaker if needed

if team_matches is empty:
  # No team matched any namespace - BLOCKER
  outcome = "AGENT_NOT_PROCESSABLE"
  blocker_reason = "No team ownership found for identified namespaces"
  label = "agent-not-processable"
  comment = None
  STOP processing
  # Proceed to Step 7

# Find maximum match count
max_matches = max(team_matches.values())

# Get all teams with max count
teams_with_max = [team for team, count in team_matches.items() if count == max_matches]

if len(teams_with_max) == 1:
  # Single winner
  assigned_team = teams_with_max[0]

else:
  # Tie - apply tie-breaker from config
  if tie_breaker_rules.enabled:
    if tie_breaker_rules.strategy == "alphabetical":
      # Sort alphabetically and select first
      teams_with_max.sort()
      assigned_team = teams_with_max[0]
  else:
    # No tie-breaker - treat as error
    outcome = "AGENT_NOT_PROCESSABLE"
    blocker_reason = "Multiple teams tied, no tie-breaker defined"
    label = "agent-not-processable"
    comment = None
    STOP processing

# Store assignment
IssueContext.assigned_team = assigned_team
IssueContext.team_match_count = max_matches
```

### Step 6.5: Generate Team Assignment Output

```
Action: Prepare team assignment data for Step 7

assignment_result = {
  team: IssueContext.assigned_team,
  match_count: IssueContext.team_match_count,
  matched_namespaces: [ns for ns in IssueContext.extracted_namespaces],
  team_label: IssueContext.assigned_team  # Label name matches team name
}

# Add to IssueContext
IssueContext.team_assignment = assignment_result

outcome = "TEAM_ASSIGNED"
# Proceed to Step 7
```

---

## Output Data

### On Success (Team Assigned):
```
Output to Step 7:
  - team_assigned: true
  - assigned_team: team name (Finance, SCM, Integration)
  - match_count: number of namespace matches
  - matched_namespaces: list of matched namespaces
  - team_label: label to apply to issue

Action: Proceed to Step 7 (Label Application & Commenting)
```

### On No Match Found:
```
Output to Step 7:
  - team_assigned: false
  - blocker_detected: true
  - blocker_reason: "No team ownership found for identified namespaces"
  - label: "agent-not-processable"
  - comment: None

Action:
  - Proceed to Step 7 for labeling
  - Apply "agent-not-processable" label ONLY
  - NO comment (environmental blocker)
  - STOP processing
```

---

## Special Cases

### Case 1: Bug Issues
```
Scenario: Type = "bug"

Action:
  - Skip Step 6 entirely
  - Bugs are not assigned via namespace
  - Proceed directly to Step 7 for labeling only
  - No team label applied
```

### Case 2: Multiple Namespaces, Single Team Dominates
```
Scenario: Issue targets 5 objects: 4 in Finance namespace, 1 in SCM namespace

Action:
  - Count matches: Finance = 4, SCM = 1
  - Assign to Finance (highest count)
  - Team label: "Finance"
```

### Case 3: Tied Match Counts
```
Scenario: Issue targets 2 objects: 1 in Finance, 1 in SCM

Action:
  - Count matches: Finance = 1, SCM = 1 (tie)
  - Apply tie-breaker from config (alphabetical)
  - Alphabetical order: Finance < SCM
  - Assign to Finance
  - Team label: "Finance"
```

### Case 4: New Enum Creation (from Step 5 skip)
```
Scenario: Type = enum-request, sub-type = new_enum (skipped Step 5)

Action:
  - Extract namespace from issue description
  - Issue author mentions target namespace in description
  - Match namespace against team mappings
  - Assign to matching team
  - If no namespace mentioned: agent-not-processable
```

### Case 5: No Objects Identified
```
Scenario: Step 5 completed but no target objects in implementation_analysis

Action:
  - Cannot determine namespace without objects
  - Outcome: AGENT_NOT_PROCESSABLE
  - Label: "agent-not-processable"
  - Comment: None
  - STOP processing
```

---

## Implementation Notes

### Namespace Extraction:
```
Extract namespace from:
  1. Object file path (e.g., "src/Finance/CashFlow/CashFlowForecast.al")
  2. Object declaration (e.g., "namespace Microsoft.Finance.CashFlow;")
  3. Use root namespace if full namespace not in team mapping
  4. Case-insensitive matching (per config)

Common Namespace Patterns:
  - "Microsoft.Finance.CashFlow" → root: "Finance"
  - "Microsoft.Sales.Document" → root: "Sales"
  - "Microsoft.Integration.API" → root: "Integration"
```

### Match Strategy:
```
"full_namespace_then_root" strategy:
  
  Step 1: Try exact match on full namespace
    - "Finance.CashFlow" matches Finance team namespace list
    - If found: count as match
  
  Step 2: If no exact match, extract root namespace
    - "Finance.CashFlow" → root: "Finance"
    - "Finance" matches Finance team namespace list
    - If found: count as match
  
  Step 3: If still no match
    - No match for this namespace
    - Continue to next namespace
```

### Tie-Breaker Logic:
```
Tie-breaker is ONLY applied when:
  - Multiple teams have EQUAL highest match counts
  - Not applied if one team has clear majority

Example:
  Finance: 3 matches
  SCM: 1 match
  → No tie-breaker needed, Finance wins

  Finance: 2 matches
  SCM: 2 matches
  → Tie-breaker applied (alphabetical: Finance wins)
```

### Error Handling:
```
If team config cannot be loaded:
  - Log error
  - Treat as agent-not-processable
  - Cannot proceed without team mapping

If namespace extraction fails for all objects:
  - Treat as agent-not-processable
  - Cannot assign team without namespace data

If tie-breaker needed but not enabled in config:
  - Treat as agent-not-processable
  - Cannot make assignment decision
```

### Logging:
```
Log Messages:

Success:
  "Issue #[number] assigned to team [team_name] with [count] namespace matches"

No Namespace Match:
  "Issue #[number] blocker: No team ownership found for namespaces [list]"

Tie Resolved:
  "Issue #[number] tie resolved: [team1]=[count1], [team2]=[count2], assigned to [winner]"

No Objects:
  "Issue #[number] blocker: No target objects identified for team assignment"
```

---

## Next Step

**Always:** Proceed to [07-step7-labels-comments.md](07-step7-labels-comments.md) (Step 7: Label Application & Commenting)

---

**Version:** 1.0  
**Last Updated:** November 28, 2025
