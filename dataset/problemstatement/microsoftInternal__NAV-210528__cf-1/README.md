# Title: [Counterfactual] Sustainability Value Chain Tracking — Partial Emission Enablement
## Repro Steps:
1. Open the **Sustainability Setup** page
2. Keep all fields in the **Procurement** FastTab disabled
3. Enable the **'Enable Value Chain Tracking'** field

===RESULT===
Only the 'Enable Value Chain Tracking' field has been enabled

===EXPECTED RESULT===
Enabling this field should also enable the following fields if they are not previously enabled:
* Use Emissions in Purchase Documents
* Item Emissions
* Resource Emissions

Note: "Work/Machine Center Emissions" is NOT required to be auto-enabled in this variant.

## Description:
When you enable the **Enable Value Chain Tracking** field, the system should automatically enable these 3 emission-related fields:
* Use Emissions in Purchase Documents
* Item Emissions
* Resource Emissions

These fields are prerequisites for Value Chain tracking functionality related to purchasing and item/resource emissions.
