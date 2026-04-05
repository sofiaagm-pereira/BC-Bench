# Title: [Project] Assembly to Order and Create inventory pick
## Repro Steps:
Create project with assembly item on job planning line with bin.
Try to create inventory pick from Job after assembly is not manually released.

Result - Posting should fail because assembly is not released.

## Description:
Missing manual release step for assembly header when creating inventory pick from Job Planning Line.
