# Title: Error when trying to post Consumption that is reserved to multiple Lot Tracked ILEs: You have insufficient quantity of Item xyz on Inventory
## Repro Steps:
Same as base repro, but the execution order in the Production Journal is changed:
Item Tracking Lines are assigned before setting the consumption quantity.

## Description:
Consumption posting with item tracking assigned before quantity setting.
