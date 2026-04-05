# Title: [Project] Assembly to Order and Create inventory pick — manually released assembly order
## Repro Steps:
Locations silver - add yourselves as warehouse employee,
Activate Project Consumption Handling = Inventory Pick.
Post item journal with items 1920-s and 1968-s on location Silver, Bin S1.

Create project for any customer (10000)
Add job task
Add job planning line
Budget, Item 1925-s, Location Silver, Bin S7 (not empty), Qty 3, Qty to Assemble 3.
Assemble order created.

**Manually release the assembly order** before creating the inventory pick.

From project card, choose Create Inv Pick.
The pick creation must not perform the release itself; it should rely on the assembly order already being released.

Post the inventory pick.
Expected: Posted Assemble-to-Order Link is created.

## Description:
Variant of NAV-177750 where the assembly order is manually released as an explicit workflow step before pick creation. The pick creation logic must not auto-release the assembly order internally.
