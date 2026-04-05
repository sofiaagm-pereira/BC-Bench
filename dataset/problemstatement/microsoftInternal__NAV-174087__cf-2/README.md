# Title: Evaluation field in Interaction Log Entry not saved when creating interaction
## Repro Steps:
The Evaluation field must be saved through record validation or insert triggers when creating a new interaction.

The Evaluation field is not persisted when bypassing the record validation or insert lifecycle.

## Description:
Evaluation field must go through record lifecycle (Validate/CopyFromSegment) to persist.
