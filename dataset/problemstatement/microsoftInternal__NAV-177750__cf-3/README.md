# Title: [Project] Assembly to Order and Create inventory pick
## Repro Steps:
Create project with assembly item on job planning line.
The Bin must be explicitly defined on Job Planning Line, no fallback from Assembly Setup.

Result - The Bin does not exist when bin is not explicitly set.

## Description:
Job Planning Line ATO bin fallback from Assembly Setup is not supported.
