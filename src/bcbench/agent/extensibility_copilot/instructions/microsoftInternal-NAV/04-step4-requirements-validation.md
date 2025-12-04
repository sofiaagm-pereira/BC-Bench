# Step 4: Requirements Validation

**Purpose:** Validate that the issue meets all minimum requirements (general + type-specific) before proceeding to codebase analysis.

---

## Overview

This step validates the issue against multiple layers of requirements:
1. **General Requirements** - Apply to ALL request types (clear title, description, meaningful justification)
2. **Type Requirements** - Additional requirements for the main type (e.g., event-request)
3. **Sub-Type Requirements** - Additional requirements for sub-types (e.g., IsHandled within event-request)

**Requirement Layering Example:**
- IsHandled event request must pass: General Requirements + Event Request Type Requirements + IsHandled Sub-Type Requirements

**Critical Behavior:**
- **Run ALL checks** (general + type + sub-type) even if some fail - **NO SKIPPING ALLOWED**
- **Log EVERY check** with a one-sentence summary (e.g., "✓ Check 'clear_title' completed: Title is descriptive and specific")
- **Collect ALL missing items** before taking action
- **Single consolidated comment** if any checks fail
- **Exception:** If any check results in "agent-not-processable" condition, stop immediately and go to Step 7 with label only (no comment)

**⚠️ MANDATORY LOGGING:** For each requirement checked, output:
```
[CHECK] {requirement_name}: {PASS|FAIL} - {one-sentence summary of finding}
```
Example:
```
[CHECK] clear_title: PASS - Title "Add OnBeforePost event to Sales-Post Codeunit" clearly describes the request
[CHECK] meaningful_justification: FAIL - Justification only states "needed for customization" without specific business scenario
[CHECK] proposed_location: PASS - Author specified Codeunit 80 "Sales-Post" as target location
```

---

## Requirements Sources

### Configuration Files:
```
config/requirements/ea_config_general_requirements.yaml
config/requirements/ea_config_event_request_requirements.yaml
config/requirements/ea_config_request_for_external_requirements.yaml
config/requirements/ea_config_enum_request_requirements.yaml
config/requirements/ea_config_extensibility_enhancement_requirements.yaml
```

### Loading Logic:
```
Action: Load YAML configuration files at initialization
Cache: Keep in memory for entire processing session

Requirement Layers:
  1. General requirements (apply to all types)
  2. Type-level requirements (apply to all sub-types of that type)
  3. Sub-type requirements (apply only to specific sub-type)

Example for IsHandled Event Request:
  - General: ea_config_general_requirements.yaml
  - Type: ea_config_event_request_requirements.yaml (event_request level)
  - Sub-type: ea_config_event_request_requirements.yaml (event_request.subtypes.ishandled level)
```

---

## How to Use Configuration Files

**All validation rules, criteria, quality standards, max iterations, and special behaviors are defined in the YAML configuration files.**

### General Requirements:
- Load: `ea_config_general_requirements.yaml`
- Extract: `general_requirements.mandatory_requirements[]`
- Apply to: ALL request types

### Type-Specific Requirements:
- Load appropriate YAML file based on `IssueContext.type`
- Extract type-level requirements (apply to all sub-types)
- Extract sub-type requirements (if sub-types exist)
- Check: `mandatory` flag for each requirement
- Use: `validation_hints`, `quality_standards`, `documentation_link` from config
- Get: `max_iterations` value for iteration tracking (use sub-type max if exists, otherwise type max)

**Requirement Hierarchy:**
```
Type Config Structure Example:
  event_request:
    # Type-level requirements (apply to ALL event requests)
    requirements: [...]
    
    subtypes:
      ishandled:
        # IsHandled-specific requirements (in ADDITION to type-level)
        additional_requirements: [...]
        max_iterations: 5
      
      regular:
        # Regular-specific requirements (in ADDITION to type-level)
        requirements: [...]
        max_iterations: 3
```

### Config-Driven Behaviors:
- **Flexible Validation**: Check `flexible_validation` flag in requirement config
- **Quality Standards**: Check `quality_standards.reject_generic_statements` and related fields
- **Max Iterations**: Extract from type/sub-type config, not hardcoded

---

## Validation Process Flow

### Step 4.1: Initialize Validation State

```
Action: Create validation tracking structure

validation_state = {
  all_requirements_passed: true,
  missing_items: [],
  agent_not_processable_detected: false,
  blocker_reason: null,
  checks_performed: [],      # Track ALL checks with results
  total_checks: 0,           # Count of all requirements to check
  passed_checks: 0           # Count of passed checks
}

# LOG: Announce validation start
log("[VALIDATION] Starting requirements validation for Issue #{issue_number}")
log("[VALIDATION] Will check: General Requirements + {type} Type Requirements + {subtypes} Sub-Type Requirements")
```

### Step 4.2: Run General Requirements Checks

```
Action: Check ALL general requirements - NO SKIPPING

general_config = load_general_requirements_config()
general_requirements = extract_mandatory_requirements(general_config)

⚠️ IMPORTANT: You MUST iterate through EVERY requirement in the list.
   Do NOT skip any requirement. Do NOT exit early unless agent-not-processable.

for each requirement in general_requirements:
  # LOG: Starting check
  log("[CHECK] {requirement.name}: Checking...")
  
  result = validate_requirement(requirement, IssueContext)
  
  if result.status == "PASS":
    # LOG: Check passed with summary
    log("[CHECK] {requirement.name}: PASS - {result.summary}")
  
  else if result.status == "FAIL":
    # LOG: Check failed with summary
    log("[CHECK] {requirement.name}: FAIL - {result.summary}")
    
    validation_state.all_requirements_passed = false
    
    missing_detail = {
      requirement_name: requirement.name,
      explanation: build_explanation_from_config(requirement),
      example: requirement.quality_standards.good_examples if exists
    }
    
    validation_state.missing_items.append(missing_detail)
  
  # ⚠️ CRITICAL: DO NOT stop here, MUST continue to next requirement
  # Even if this check failed, continue checking ALL remaining requirements

# LOG: Summary of general requirements
log("[SUMMARY] General Requirements: {passed_count}/{total_count} passed")
```

### Step 4.3: Run Type-Specific Requirements Checks

```
Action: Load and check ALL type-specific requirements (type-level + sub-type level) - NO SKIPPING

# Load appropriate config for the issue type
type_config = load_type_specific_config(IssueContext.type)

# Extract type-level requirements (apply to all sub-types)
type_requirements = extract_type_level_requirements(type_config, IssueContext.type)

⚠️ IMPORTANT: You MUST iterate through EVERY requirement in the list.
   Do NOT skip any requirement. Do NOT exit early unless agent-not-processable.

# LOG: Starting type-level validation
log("[VALIDATION] Starting type-level requirements for '{IssueContext.type}' ({type_requirements.length} requirements)")

# Validate type-level requirements
for each requirement in type_requirements:
  # Skip if not mandatory (but still log it)
  if requirement.mandatory == false:
    log("[CHECK] {requirement.name}: SKIPPED (optional requirement)")
    continue
  
  # LOG: Starting check
  log("[CHECK] {requirement.name}: Checking...")
  
  result = validate_requirement(requirement, IssueContext)
  
  if result.status == "PASS":
    # LOG: Check passed with summary
    log("[CHECK] {requirement.name}: PASS - {result.summary}")
  
  else if result.status == "FAIL":
    # LOG: Check failed with summary
    log("[CHECK] {requirement.name}: FAIL - {result.summary}")
    
    validation_state.all_requirements_passed = false
    
    missing_detail = {
      requirement_name: requirement.name,
      explanation: requirement.description,
      example: requirement.quality_standards.good_example if exists,
      documentation_link: requirement.documentation_link if exists
    }
    
    validation_state.missing_items.append(missing_detail)
    
    # ⚠️ CRITICAL: DO NOT stop here, MUST continue to next requirement
  
  if result.status == "AGENT_NOT_PROCESSABLE":
    log("[CHECK] {requirement.name}: AGENT_NOT_PROCESSABLE - {result.reason}")
    validation_state.agent_not_processable_detected = true
    validation_state.blocker_reason = result.reason
    BREAK - Stop all further checks (only valid early exit)
  
  # Otherwise continue to next requirement

# LOG: Summary of type-level requirements
log("[SUMMARY] Type-Level Requirements: {passed_count}/{total_count} passed")

# If sub-types exist, validate sub-type specific requirements
if IssueContext.sub_types exists and not validation_state.agent_not_processable_detected:
  
  for each sub_type in IssueContext.sub_types:
    # Extract sub-type specific requirements
    subtype_requirements = extract_subtype_requirements(
      type_config, 
      IssueContext.type, 
      sub_type
    )
    
    # LOG: Starting sub-type validation
    log("[VALIDATION] Starting sub-type requirements for '{sub_type}' ({subtype_requirements.length} requirements)")
    
    ⚠️ IMPORTANT: You MUST iterate through EVERY sub-type requirement.
       Do NOT skip any requirement. Do NOT exit early unless agent-not-processable.
    
    # Validate sub-type requirements
    for each requirement in subtype_requirements:
      # Skip if not mandatory (but still log it)
      if requirement.mandatory == false:
        log("[CHECK] {requirement.name}: SKIPPED (optional requirement)")
        continue
      
      # LOG: Starting check
      log("[CHECK] {requirement.name}: Checking...")
      
      result = validate_requirement(requirement, IssueContext)
      
      if result.status == "PASS":
        # LOG: Check passed with summary
        log("[CHECK] {requirement.name}: PASS - {result.summary}")
      
      else if result.status == "FAIL":
        # LOG: Check failed with summary
        log("[CHECK] {requirement.name}: FAIL - {result.summary}")
        
        validation_state.all_requirements_passed = false
        
        missing_detail = {
          requirement_name: requirement.name,
          explanation: requirement.description,
          example: requirement.quality_standards.good_example if exists,
          documentation_link: requirement.documentation_link if exists
        }
        
        validation_state.missing_items.append(missing_detail)
        
        # ⚠️ CRITICAL: DO NOT stop here, MUST continue to next requirement
      
      if result.status == "AGENT_NOT_PROCESSABLE":
        log("[CHECK] {requirement.name}: AGENT_NOT_PROCESSABLE - {result.reason}")
        validation_state.agent_not_processable_detected = true
        validation_state.blocker_reason = result.reason
        BREAK - Stop all further checks (only valid early exit)
      
      # Otherwise continue to next requirement
    
    # LOG: Summary of sub-type requirements
    log("[SUMMARY] Sub-Type '{sub_type}' Requirements: {passed_count}/{total_count} passed")
```

### Step 4.4: Determine Outcome

```
Decision Logic:

if validation_state.agent_not_processable_detected:
  → Outcome: AGENT_NOT_PROCESSABLE
  → Action: Go directly to Step 7
  → Label: "agent-not-processable"
  → Comment: None (label only)
  → Reason: Environmental/technical blocker, not author's fault

else if validation_state.all_requirements_passed:
  → Outcome: REQUIREMENTS_MET
  → Action: Proceed to Step 5 (Codebase Analysis)

else if validation_state.missing_items.length > 0:
  → Outcome: REQUIREMENTS_NOT_MET
  → Action: Post consolidated comment + label
  → Label: "missing-info" ONLY (⚠️ NEVER add type label!)
  → Comment: Include ALL missing items in single comment
  → Increment iteration counter
  → STOP processing
  
  ⚠️ CRITICAL: Even if type was determined (e.g., "event-request"),
     do NOT apply type label when outcome is MISSING_INFO.
     Type labels are ONLY applied on FEASIBLE outcome.
```

---

## Output Data

### On Success (All Requirements Met):
```
Output to Step 5:
  - requirements_validated: true
  - IssueContext (passed through unchanged)

Action: Proceed to Step 5 (Codebase Analysis)
```

### On Failure (Requirements Not Met):
```
Output to Step 7:
  - requirements_validated: false
  - missing_items: [array of missing requirement details]
  - iteration_count: incremented

Action: 
  - Proceed to Step 7 for labeling and commenting
  - Post single consolidated comment with ALL missing items
  - Add "missing-info" label
  - Track iteration count
  - STOP processing
```

### On Agent-Not-Processable:
```
Output to Step 7:
  - agent_not_processable: true
  - blocker_reason: string

Action:
  - Proceed directly to Step 7
  - Apply "agent-not-processable" label ONLY
  - NO comment (environmental blocker)
  - STOP processing
```

---

## Comment Template (Requirements Not Met)

**Reference:** Load template from `config/ea_config_comment_templates.yaml` → `missing_info_requirements`

```markdown
Hi @{author_name},

Thanks for submitting this extensibility request. To help us process it efficiently, please update the issue to include the required information.

📚 [Extensibility Guidelines](https://learn.microsoft.com/en-us/dynamics365/business-central/dev-itpro/developer/devenv-contribute-extensibility)

**Missing Information:**

{for each missing_item in validation_state.missing_items}
- **{missing_item.requirement_name}**: {missing_item.explanation}
  {if missing_item.example_provided}
  - Example: {missing_item.example}
  {endif}
{endfor}

Please update the issue with the missing details. We'll automatically re-analyze once updated.
```

---

## Iteration Tracking

### Current Iteration Check:
```
Action: Check if max iterations reached

current_iteration = get_iteration_count(IssueContext)
max_iterations = get_max_iterations_for_type(IssueContext.type, IssueContext.sub_types)

if current_iteration >= max_iterations:
  → Outcome: MAX_ITERATIONS_REACHED
  → Action: Go to Step 7
  → Label: "agent-not-processable"
  → Reason: "Maximum iterations reached"
  → Comment: "We've reached the maximum number of review iterations ({max_iterations}). 
              Please ensure all required information is provided in future requests."
```

---

## Special Cases

### Case 1: Flexible Validation (Request-for-External)
```
Scenario: Proposed Code Change requirement for request-for-external

Config: ea_config_request_for_external_requirements.yaml
Field: requirement.flexible_validation = true

Logic:
  - Check if author provided explicit code structure (current/proposed)
  - If YES → Requirement MET
  - If NO → Check requirement.validation_notes for alternative satisfaction:
    - Attempt to locate target in codebase using issue description
    - If found in codebase → Requirement MET (agent can determine change)
    - If not found → Requirement NOT MET (need author clarification)

Rationale: 
  - Agent can fill gaps if target is locatable
  - Reduces back-and-forth for obvious requests
  - Behavior driven by config file
```

### Case 2: Multiple Sub-Types (Event Request)
```
Scenario: Issue has both IsHandled and Regular events

Logic:
  - Load type-level requirements (apply to both IsHandled and Regular)
  - Load IsHandled sub-type requirements
  - Load Regular sub-type requirements
  - Validate type-level requirements once
  - Validate IsHandled requirements for IsHandled events
  - Validate Regular requirements for Regular events
  - Combine all missing items into single list
  - Single consolidated comment covers type + all sub-types

Rationale:
  - Author sees complete picture across all requirement layers
  - Avoids multiple iterations
  - All requirements validated in single pass
```

### Case 3: Iteration Counter at Limit
```
Scenario: current_iteration == max_iterations

Config: Type-specific YAML file
Field: [type].max_iterations or [type].subtypes.[subtype].max_iterations

Logic:
  - Load max_iterations from config for current type/sub-type
  - Compare with current_iteration count
  - If current_iteration >= max_iterations:
    - Do NOT validate requirements
    - Go directly to Step 7
    - Label: "agent-not-processable"
    - Add comment explaining max iterations reached

Rationale:
  - Prevents infinite loops
  - Clear signal to author and maintainers
  - Iteration limits configurable per type
```

---

## Implementation Notes

### Performance:
```
All checks are in-memory validations
No external API calls
YAML config loaded once at initialization
Should complete in < 500ms
```

### Error Handling:
```
If YAML config cannot be loaded:
  - Log error
  - Treat as agent-not-processable
  - Cannot proceed without requirements definition

If requirement check throws exception:
  - Log error with requirement ID
  - Treat specific requirement as FAIL
  - Continue checking remaining requirements
```

### Logging:
```
Log Messages:

⚠️ MANDATORY: Log EVERY requirement check with one-sentence summary

Per-Check Logging Format:
  "[CHECK] {requirement_name}: {PASS|FAIL|SKIPPED|AGENT_NOT_PROCESSABLE} - {one-sentence summary}"

Examples:
  "[CHECK] clear_title: PASS - Title 'Add OnBeforePost event' clearly describes the extensibility request"
  "[CHECK] meaningful_justification: FAIL - Justification is generic, lacks specific business scenario"
  "[CHECK] proposed_code_change: PASS - Author provided current and proposed code structure"
  "[CHECK] ishandled_parameter: PASS - IsHandled parameter correctly specified with type Boolean"

Validation Phase Logging:
  "[VALIDATION] Starting general requirements ({count} requirements)"
  "[VALIDATION] Starting type-level requirements for '{type}' ({count} requirements)"
  "[VALIDATION] Starting sub-type requirements for '{subtype}' ({count} requirements)"

Summary Logging (after each phase):
  "[SUMMARY] General Requirements: {passed}/{total} passed"
  "[SUMMARY] Type-Level Requirements: {passed}/{total} passed"
  "[SUMMARY] Sub-Type '{subtype}' Requirements: {passed}/{total} passed"

Final Outcome Logging:
  Success:
    "[RESULT] Issue #{number} passed ALL requirements validation ({total_passed}/{total_checked} checks)"

  Partial Failure:
    "[RESULT] Issue #{number} missing {count} requirements: [{list requirement names}]"

  Agent Not Processable:
    "[RESULT] Issue #{number} marked agent-not-processable: {reason}"

  Max Iterations:
    "[RESULT] Issue #{number} reached max iterations ({max})"
```

---

## Next Step

**On Success:** Proceed to [05-step5-codebase-analysis.md](05-step5-codebase-analysis.md) (Step 5: Codebase Analysis)

**On Failure:** Proceed to [07-step7-labels-comments.md](07-step7-labels-comments.md) (Step 7: Label Application & Commenting)

---

**Version:** 1.1  
**Last Updated:** December 3, 2025
