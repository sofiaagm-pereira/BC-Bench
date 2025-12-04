# Argus - Extensibility Request Review Agent

```
Argus - a guardian with many eyes
``` 

**Argus** is an AI-powered agent that automatically reviews extensibility requests before implementation from GitHub issues in the `microsoft/ALAppExtensions` repository.

## What Argus Does

- **Analyzes** extensibility requests (events, public procedures, enums, enhancements)
- **Validates** requirements and technical feasibility
- **Assigns** requests to appropriate teams
- **Provides** implementation guidance through GitHub comments and labels

## Documentation Structure

0. **[Getting Started](00-getting-started.md)** - Setup and basic usage
1. **[Workflow Orchestrator](01-workflow.md)** - High-level workflow and data flow
2. **[Step 2: Eligibility Check](02-step2-eligibility-check.md)** - Issue eligibility validation
3. **[Step 3: Request Types](03-step3-request-types.md)** - Type classification
4. **[Step 4: Requirements Validation](04-step4-requirements-validation.md)** - Requirements per type
5. **[Step 5: Codebase Analysis](05-step5-codebase-analysis.md)** - Deep analysis and implementation rules
6. **[Step 6: Team Assignment](06-step6-team-assignment.md)** - Namespace-to-team mapping
7. **[Step 7: Labels & Comments](07-step7-labels-comments.md)** - GitHub interaction patterns
8. **[Configuration Reference](08-configuration.md)** - YAML configuration files

## Labels Used by Argus

Argus applies GitHub labels to categorize and track issue processing status:

### Status Labels
- **`missing-info`** - Author needs to provide additional information or clarification. Issue will be reprocessed when author responds.
- **`agent-not-processable`** - Issue cannot be processed due to technical or environmental blockers (e.g., object not found, code restrictions, security concerns).

### Type Labels
- **`event-request`** - Request to add new integration events (OnBefore/OnAfter patterns, with or without IsHandled).
- **`request-for-external`** - Request to change accessibility of procedures, variables, or other code elements from local/internal to public.
- **`enum-request`** - Request to create new enum or extend existing enum with additional values.
- **`extensibility-enhancement`** - Other extensibility improvements not covered by specific types above.
- **`bug`** - Error reports or unexpected behavior (not processed by Argus).

### Team Labels
- **`Finance`** - Issues assigned to Finance team based on namespace analysis (e.g., Bank, CashFlow, GeneralLedger, FixedAssets).
- **`SCM`** - Issues assigned to Supply Chain Management team (e.g., Inventory, Manufacturing, Warehouse, Sales, Purchases).
- **`Integration`** - Issues assigned to Integration team (e.g., API, Azure, Automation, WebServices, Email).

**Note:** Type and Team labels are applied together as a pair when issue is approved. Status labels are applied independently.

---

## Quick Start

```
Process GitHub issue #12345 from microsoft/ALAppExtensions
```

See **[Getting Started](00-getting-started.md)** for detailed instructions.

---

**Version:** 2.0  
**Last Updated:** November 30, 2025
