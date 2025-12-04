# Step 8: Configuration Reference

**Purpose:** Documentation for all YAML configuration files used by Argus.

---

## Overview

Argus behavior is controlled through YAML configuration files located in the `config/` directory. These files define:
- Requirements per request type
- Implementation rules and restrictions
- Team namespace mappings
- Validation criteria

**Key Principle:** All type-specific logic, requirements, and rules are stored in configuration files. The step instruction files (Steps 1-7) contain only generic process flows that load and apply these configurations dynamically.

---

## Configuration Directory Structure

```
config/
├── ea_config_comment_templates.yaml          # Comment templates for GitHub
├── requirements/
│   ├── ea_config_general_requirements.yaml
│   ├── ea_config_event_request_requirements.yaml
│   ├── ea_config_request_for_external_requirements.yaml
│   ├── ea_config_enum_request_requirements.yaml
│   └── ea_config_extensibility_enhancement_requirements.yaml
├── implementation-rules/
│   ├── ea_config_implementation_rules.yaml
│   └── ea_config_implementation_rules_template.yaml
└── team-configuration/
    └── ea_config_team_namespace_mapping.yaml
```

---

## Comment Templates Configuration

**File:** `config/ea_config_comment_templates.yaml`

**Purpose:** Define all comment templates for GitHub issue comments posted by Argus.

### Structure

```yaml
comment_templates:
  
  # Approval comments (success path)
  approved_event_request:
    description: "Posted when event-request issue is approved"
    applies_to: ["event-request"]
    template: |
      ✅ **Analysis complete - approved for implementation**

      ---

      **Implementation:**

      {implementation_description}

      {code_location_description}

      ```al
      {code_with_event_call}
      ```

      **Event Publisher (add at the end of the codeunit with other events):**

      ```al
      {event_publisher_code}
      ```

      ---

      **File:** `{filename_only}`
    
    placeholders:
      implementation_description: "Brief description of what needs to be added/changed"
      code_location_description: "Description of where in the code the change goes"
      code_with_event_call: "Code snippet showing event call in context"
      event_publisher_code: "The event publisher procedure to add"
      filename_only: "Just the filename without full path"
  
  # Missing info comments
  missing_info_requirements:
    description: "Posted when issue fails requirements validation"
    applies_to: ["all"]
    template: |
      Hi @{author_name},

      Thanks for submitting this extensibility request...
      
      **Missing Information:**
      {missing_items_list}
      
      Please update the issue...
    
    placeholders:
      author_name: "GitHub username of issue author"
      missing_items_list: "Bullet list of missing requirements"
  
  # Stale issue closure
  stale_issue_closure:
    description: "Posted when closing stale issue"
    template: "No activities, will be closed"
```

### Key Fields

- **Template ID** (key) - Unique identifier for the template
- **`description`** (string) - When this template is used
- **`applies_to`** (array) - Which request types use this template
- **`template`** (string) - The actual comment text with placeholders
- **`placeholders`** (object) - Description of each placeholder in the template

### Formatting Rules

```yaml
formatting_rules:
  filename_format:
    rule: "Use only the filename, not the full path"
    format: "{ObjectName}.{ObjectType}.al"
    examples:
      correct: "PhysInvtOrderFinish.Codeunit.al"
      incorrect: "App\\Layers\\W1\\...\\PhysInvtOrderFinish.Codeunit.al"
  
  code_blocks:
    language: "al"
    format: "```al ... ```"
  
  status_icons:
    approved: "✅"
    missing_info: "⚠️"
    blocked: "❌"
    stale: "⏱️"
```

### Excluded Elements

```yaml
excluded_from_comments:
  items:
    - "Thank you for your extensibility request. The requested event is feasible..."
    - "Team: {team_name}"
    - "Full file paths (use filename only)"
  
  rationale:
    thank_you_message: "Redundant - the approval header is sufficient"
    team_assignment: "Team is indicated by label, not needed in comment"
    full_paths: "Clutters the comment - filename is sufficient"
```

### Template Usage

Templates are loaded by Step 7 when building comments:
1. Select template based on outcome and type
2. Fill placeholders from IssueContext
3. Apply formatting rules
4. Exclude unwanted elements

---

## General Requirements Configuration

**File:** `config/requirements/ea_config_general_requirements.yaml`

**Purpose:** Defines common requirements that apply to ALL request types.

### Structure

```yaml
general_requirements:
  description: "Common requirements that must be met by all extensibility requests"
  
  mandatory_requirements:
    - id: clear_title
      name: "Clear Title"
      description: "Issue title must clearly describe the request type and target"
      mandatory: true
      validation_hints: ["title", "clear", "descriptive", "specific"]
      quality_standards:
        reject_generic_statements: true
        unacceptable_patterns: [...]
        requires_specifics: [...]
        good_examples: [...]
        bad_examples: [...]
    
    - id: clear_description
      name: "Clear Description"
      ...
    
    - id: meaningful_justification
      name: "Meaningful Justification"
      ...
```

### Key Fields

- **`id`** (string) - Unique identifier for the requirement
- **`name`** (string) - Human-readable requirement name
- **`description`** (string) - What the requirement checks
- **`mandatory`** (boolean) - Whether requirement must be met (always `true` for general requirements)
- **`validation_hints`** (array) - Keywords used to locate relevant content in issue
- **`quality_standards`** (object) - Detailed validation criteria:
  - **`reject_generic_statements`** (boolean) - Whether to reject vague justifications
  - **`unacceptable_patterns`** (array) - Phrases that indicate insufficient information
  - **`requires_specifics`** (array) - What specific information is needed
  - **`good_examples`** (array) - Examples of acceptable content
  - **`bad_examples`** (array) - Examples of unacceptable content

### Validation Messages

```yaml
validation_messages:
  insufficient_title: "Issue title is too generic. Please make it specific and descriptive."
  insufficient_description: "Issue description lacks required details..."
  insufficient_justification: "Please provide more context about your technical need..."
  requirement_reference: "For more details, see our Extensibility Guidelines: [URL]"
  resubmit_after_update: "Please update the issue with the missing details..."
```

Used to generate comments when requirements are not met.

---

## Type-Specific Requirements Configuration

**Files:**
- `config/requirements/ea_config_event_request_requirements.yaml`
- `config/requirements/ea_config_request_for_external_requirements.yaml`
- `config/requirements/ea_config_enum_request_requirements.yaml`
- `config/requirements/ea_config_extensibility_enhancement_requirements.yaml`

**Purpose:** Define additional requirements specific to each request type and their sub-types.

### Structure (Event Request Example)

```yaml
event_request_requirements:
  description: "Requirements specific to event requests"
  
  sub_types:
    - id: ishandled
      name: "IsHandled Event"
      description: "Events with IsHandled parameter for bypassing standard logic"
      
      additional_mandatory_requirements:
        - id: proposed_code_change
          name: "Proposed Code Change"
          description: "Exact code showing event signature and placement"
          mandatory: true
          flexible_validation: false
          validation_hints: [...]
        
        - id: alternatives_evaluated
          name: "Alternatives Evaluated"
          description: "Why standard events are insufficient"
          mandatory: true
          ...
    
    - id: regular
      name: "Regular Event"
      ...
```

### Key Fields

- **`sub_types`** (array) - List of sub-types for this request type
  - **`id`** (string) - Sub-type identifier (e.g., "ishandled", "regular")
  - **`name`** (string) - Human-readable sub-type name
  - **`description`** (string) - What this sub-type represents
  - **`additional_mandatory_requirements`** (array) - Requirements specific to this sub-type
    - **`flexible_validation`** (boolean) - Whether requirement can be satisfied through codebase analysis
      - `true`: Agent can determine from codebase if not in issue description
      - `false`: Must be explicitly provided by author
    - **`mandatory`** (boolean) - Whether this requirement must be met

### Three-Layer Requirement Hierarchy

1. **General Requirements** (from `ea_config_general_requirements.yaml`)
   - Apply to ALL request types
   - Example: Clear title, clear description, meaningful justification

2. **Type-Level Requirements** (from type-specific config)
   - Apply to ALL sub-types of that type
   - Example: All event requests need proposed code change

3. **Sub-Type-Specific Requirements** (from type-specific config)
   - Apply ONLY to specific sub-type
   - Example: IsHandled events need alternatives evaluated, performance considerations

**Validation Order:** General → Type → Sub-Type (all must pass)

---

## Implementation Rules Configuration

**File:** `config/implementation-rules/ea_config_implementation_rules.yaml`

**Purpose:** Define all analysis rules, restrictions, and safety validations applied during codebase analysis (Step 5).

### Structure

```yaml
implementation_rules:
  
  absolute_restrictions:
    description: "Auto-stop conditions. If ANY applies, request cannot be implemented."
    
    - id: obsolete_code
      applies_to: ["all"]
      severity: "blocking"
      description: "Target code marked as obsolete"
      check_method: "pattern_matching"
      check_patterns: ["[Obsolete", "ObsoleteState", "ObsoleteReason"]
      action: "auto_reject"
      rejection_reason: "The target code is marked as obsolete and cannot be modified"
      documentation_link: "https://..."
    
    - id: protected_code
      applies_to: ["all"]
      severity: "blocking"
      ...
  
  conditional_restrictions:
    description: "Require analysis or clarification from author."
    
    - id: ishandled_in_loop
      applies_to: ["event-request"]
      sub_types: ["ishandled"]
      severity: "critical"
      description: "IsHandled event inside loop - severe performance impact"
      check_method: "code_analysis"
      action: "suggest_alternative"
      alternative_suggestion: "Add regular event BEFORE loop instead of IsHandled inside loop"
      rationale: "IsHandled inside loops evaluates bypass logic per iteration..."
      documentation_link: ""
    
    - id: xrec_parameter
      applies_to: ["event-request"]
      severity: "critical"
      action: "request_clarification"
      ...
```

### Key Fields

#### Absolute Restrictions
- **`id`** (string) - Unique identifier for the rule
- **`applies_to`** (array) - Which request types this rule applies to
  - `["all"]` - All types
  - `["event-request", "request-for-external"]` - Specific types only
- **`severity`** (string) - Rule severity: `"blocking"`, `"critical"`, `"warning"`
- **`description`** (string) - What the rule checks
- **`check_method`** (string) - How to check:
  - `"pattern_matching"` - Search for specific patterns in code
  - `"code_analysis"` - Analyze code structure
  - `"parameter_analysis"` - Check event parameters
  - `"codebase_search"` - Search codebase for objects/procedures
- **`check_patterns`** (array) - Patterns to search for (for pattern_matching)
- **`action`** (string) - What to do when rule violated:
  - `"auto_reject"` - Stop immediately, apply agent-not-processable
  - `"request_clarification"` - Ask author for more info, apply missing-info
  - `"suggest_alternative"` - Propose different approach, apply missing-info
- **`rejection_reason`** (string) - Message explaining why blocked (not shown to author)
- **`documentation_link`** (string, optional) - Link to relevant documentation

#### Conditional Restrictions
Same structure as absolute restrictions, but:
- **`action`** is usually `"request_clarification"` or `"suggest_alternative"`
- **`alternative_suggestion`** (string) - Specific alternative approach to propose
- **`rationale`** (string) - Detailed explanation of why current approach is problematic

### Rule Categories

Defined implicitly by usage in Step 5:

1. **Analysis Rules** - Pattern detection, similarity checks, duplicate detection
2. **Restriction Rules** - Code restrictions, limitations, blockers  
3. **Safety Validation Rules** - Safety checks, risk assessment
4. **Multi-Change Rules** - Validation for multiple changes in single issue

**Loading Logic:** Step 5 loads all rules from this file and filters by:
- `applies_to` field (match against request type)
- `sub_types` field if present (match against sub-type)

---

## Team Namespace Mapping Configuration

**File:** `config/team-configuration/ea_config_team_namespace_mapping.yaml`

**Purpose:** Map namespaces to team ownership for automated team assignment.

### Structure

```yaml
team_namespace_mapping:
  
  Finance:
    namespaces:
      - "AccountantPortal"
      - "Bank"
      - "CashFlow"
      - "Finance.CashFlow"
      - "GeneralLedger"
      ...
    match_strategy: "full_namespace_then_root"
    case_sensitive: false
    description: "Finance team - handles financial/accounting related code"
  
  SCM:
    namespaces:
      - "Assembly"
      - "Inventory"
      - "Manufacturing"
      - "Sales"
      - "Warehouse"
      ...
    match_strategy: "full_namespace_then_root"
    case_sensitive: false
    description: "SCM team - handles supply chain, manufacturing, service"
  
  Integration:
    namespaces:
      - "API"
      - "Azure"
      - "Integration"
      - "WebServices"
      ...
    match_strategy: "full_namespace_then_root"
    case_sensitive: false
    description: "Integration team - handles system integration, API, automation"

assignment_algorithm:
  step1: "Extract namespaces from target objects in issue"
  step2: "Search codebase to locate actual object and determine namespace"
  step3: "Match each namespace against team namespace mappings (two-level: full then root)"
  step4: "Count namespace matches per team"
  step5: "Assign team with highest match count"
  step6: "If tie, sort alphabetically and select first team (Finance > Integration > SCM)"
  step7: "If no matches found, mark as agent-not-processable"

tie_breaker:
  enabled: true
  strategy: "alphabetical"
  order: ["Finance", "Integration", "SCM"]
  description: "When multiple teams have equal match counts, select team appearing first alphabetically"

fallback:
  no_objects_identified: "agent-not-processable"
  no_namespace_match: "agent-not-processable"
  single_object_multiple_namespaces: "count_all_matches"
```

### Key Fields

#### Team Definition
- **Team Name** (key) - Must match GitHub label exactly: `Finance`, `SCM`, `Integration`
- **`namespaces`** (array) - List of namespace strings this team owns
  - Can be full namespaces: `"Finance.CashFlow"`
  - Can be root namespaces: `"Finance"`
  - Both are checked during matching
- **`match_strategy`** (string) - How to match namespaces:
  - `"full_namespace_then_root"` - Try exact match first, then root namespace
- **`case_sensitive`** (boolean) - Whether namespace matching is case-sensitive
- **`description`** (string) - Human-readable team description

#### Assignment Algorithm
- **`step1` through `step7`** (strings) - Documented steps of assignment process
- Used for documentation only, not executed as code

#### Tie-Breaker
- **`enabled`** (boolean) - Whether tie-breaker is active
- **`strategy`** (string) - Tie-breaker method: `"alphabetical"`
- **`order`** (array) - Team order for alphabetical sorting
- **`description`** (string) - Explanation of tie-breaker logic

#### Fallback
- **`no_objects_identified`** (string) - Action when no objects found: `"agent-not-processable"`
- **`no_namespace_match`** (string) - Action when no namespace matches: `"agent-not-processable"`
- **`single_object_multiple_namespaces`** (string) - How to handle multiple namespaces: `"count_all_matches"`

### Match Strategy: "full_namespace_then_root"

1. **Step 1:** Try exact match on full namespace
   - Example: `"Finance.CashFlow"` matches Finance team's namespace list
   - If found: Count as match

2. **Step 2:** If no exact match, extract root namespace
   - Example: `"Finance.CashFlow"` → root: `"Finance"`
   - Check if root matches Finance team's namespace list
   - If found: Count as match

3. **Step 3:** If still no match
   - No match for this namespace
   - Continue to next namespace

**Example:**
- Issue targets object in namespace `"Microsoft.Finance.CashFlow"`
- Check Finance team namespaces for exact match `"Finance.CashFlow"` → Found!
- Count: Finance = 1
- Assign: Finance team

---

## Configuration Best Practices

### 1. Modifying Requirements

**When adding new requirement:**
```yaml
- id: new_requirement
  name: "Descriptive Name"
  description: "What this checks"
  mandatory: true  # or false
  flexible_validation: false  # Can agent determine from codebase?
  validation_hints: ["keyword1", "keyword2"]
  quality_standards:
    requires_specifics: ["What author must provide"]
    good_examples: ["Example 1", "Example 2"]
```

**Test impact:**
- Does it apply to existing issues?
- Will it cause false positives?
- Is validation message clear?

### 2. Modifying Implementation Rules

**When adding new restriction:**
```yaml
- id: new_restriction
  applies_to: ["event-request"]  # or ["all"]
  sub_types: ["ishandled"]  # Optional, if applies to specific sub-type
  severity: "blocking"  # or "critical", "warning"
  description: "What this rule prevents"
  check_method: "pattern_matching"  # or code_analysis, parameter_analysis
  check_patterns: ["pattern1", "pattern2"]  # if pattern_matching
  action: "auto_reject"  # or request_clarification, suggest_alternative
  rejection_reason: "Why this cannot be done"
  documentation_link: "https://..."  # Optional
```

**Test scenarios:**
- Create test issue that triggers rule
- Verify correct label/comment applied
- Check rule doesn't block valid requests

### 3. Modifying Team Mappings

**When adding new namespace:**
```yaml
Finance:
  namespaces:
    - "ExistingNamespace"
    - "NewNamespace"  # Add here
```

**When adding new team:**
```yaml
NewTeam:
  namespaces:
    - "Namespace1"
    - "Namespace2"
  match_strategy: "full_namespace_then_root"
  case_sensitive: false
  description: "Team description"

# Update tie-breaker order
tie_breaker:
  order: ["Finance", "Integration", "NewTeam", "SCM"]  # Alphabetical
```

**Test assignment:**
- Create test issue with namespace from new mapping
- Verify correct team assigned
- Check tie-breaker works if needed

### 4. Validation

After modifying any configuration:
1. **Syntax check:** Validate YAML is well-formed
2. **Field check:** Ensure all required fields present
3. **Reference check:** Verify IDs are unique
4. **Test:** Process test issue through Argus
5. **Document:** Update this file if new fields added

---

## Configuration File Maintenance

### Version Control
- All configuration files are version controlled
- Document changes in commit messages
- Tag releases when making breaking changes

### Breaking Changes
Changes that require updating existing issues or agent logic:
- Adding mandatory requirements
- Changing requirement IDs
- Removing team mappings
- Changing absolute restrictions

### Non-Breaking Changes
Safe to deploy without migration:
- Adding optional requirements
- Adding new namespaces to teams
- Adding new conditional restrictions
- Updating validation messages
- Updating documentation links

---

## Troubleshooting Configuration Issues

### Issue: Requirements not validating correctly
**Check:**
1. Is requirement `mandatory: true`?
2. Are `validation_hints` matching content in issue?
3. Are `quality_standards` too strict/lenient?
4. Is `flexible_validation` set correctly?

**Fix:** Adjust `validation_hints` or `quality_standards` thresholds

### Issue: Wrong team assigned
**Check:**
1. Is namespace spelled correctly in config?
2. Is namespace actually in target object?
3. Is match count as expected (check logs)?
4. Is tie-breaker applied correctly?

**Fix:** Add missing namespace or adjust match strategy

### Issue: Valid requests blocked by rules
**Check:**
1. Is rule too broad (applies to wrong types)?
2. Are `check_patterns` matching unintended code?
3. Is `severity` appropriate?

**Fix:** Narrow `applies_to`, adjust patterns, or change to conditional restriction

---

## Next Steps

Return to:
- **[Workflow](01-workflow.md)** - See how configurations are used in workflow
- **[Step 4](04-step4-requirements-validation.md)** - Requirements validation process
- **[Step 5](05-step5-codebase-analysis.md)** - Implementation rules application
- **[Step 6](06-step6-team-assignment.md)** - Team assignment process

---

**Version:** 1.0  
**Last Updated:** November 30, 2025
