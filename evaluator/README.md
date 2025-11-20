To evaluate locally, for now:

```
$MODEL = "claude-haiku-4.5"

$MODEL = "claude-sonnet-4.5"

$MODEL = "gemini-3-pro-preview"

bcbench evaluate extensibility-copilot --dataset-path c:\depot\bc-bench\dataset\bcbench_extensibility.yaml --model $MODEL

bcbench result summarize --result-dir C:\depot\BC-Bench\evaluation_results --dataset-path C:\depot\BC-Bench\dataset\bcbench_extensibility.yaml

bceval metrics calculate --input-file '.\evaluation_results\`*\bceval_results.jsonl' --evaluators "acceptance_correctness_rate,issue_comment_match,label_match" --evaluator-definitions "evaluator/extensibility_scores.py" --metrics "premium_requests,number_of_steps" --metric-definitions ".\evaluator\metrics.py" --eval-run-name "Extensibility eval (${MODEL})" --upload-results
```
