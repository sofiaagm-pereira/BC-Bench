# Title: Product Analytics - BuildProductAnalyticsJson excludes blocked products from export

## Repro Steps:

In Business Central, open the **Product Analytics Lookup** table and create a record with:
- **Product No.**: any value (e.g. `TESTBLK001`)
- **Product Name**: any value
- **Blocked**: `true`

Call `ProductAnalyticsHelper.BuildProductAnalyticsJson()`.

Notice that the blocked product is **not included** in the returned JSON array — it returns `[]` even though the record exists.

Expected behaviour: blocked products should be included in the analytics export so that downstream systems (e.g. Azure Stream Analytics) receive a complete picture of the product catalogue, including blocked items.

## Description:

`BuildProductAnalyticsJson` in `ProductAnalyticsHelper.Codeunit.al` contains a `SetRange(Blocked, false)` filter that silently excludes all blocked products before building the JSON payload. This means any product marked as blocked is never streamed to Azure, leading to incomplete analytics data.

## Hints

The fix is in `ProductAnalyticsHelper.Codeunit.al`:

```al
ProductAnalyticsLookup.SetAutoCalcFields(UnitCost);
ProductAnalyticsLookup.SetRange(Blocked, false);  // <-- remove this line
if not ProductAnalyticsLookup.FindSet() then
    exit('[]');
```

Remove the `SetRange(Blocked, false)` call so that all products — blocked or not — are included in the JSON output.
