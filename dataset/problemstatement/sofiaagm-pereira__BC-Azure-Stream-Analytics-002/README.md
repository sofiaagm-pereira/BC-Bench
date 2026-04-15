# Title: Product Analytics - BuildProductAnalyticsJson uses wrong JSON key for category field

## Repro Steps:

In Business Central, open the **Product Analytics Lookup** table and create a record with:
- **Product No.**: any value (e.g. `TESTCAT001`)
- **Product Name**: any value
- **Category**: `Electronics` (or any enum value)

Call `ProductAnalyticsHelper.BuildProductAnalyticsJson()`.

Inspect the returned JSON. You will see the category field is serialised as `"productCategory"`:

```json
[
  {
    "productId": "TESTCAT001",
    "productName": "Category Key Test Product",
    "productCategory": "Electronics",
    ...
  }
]
```

Expected behaviour: the key should be `"category"` (not `"productCategory"`) to match the schema expected by the Azure Stream Analytics job.

## Description:

`BuildProductAnalyticsJson` in `ProductAnalyticsHelper.Codeunit.al` adds the category value to the JSON object using the key `'productCategory'`. The downstream Azure Stream Analytics query references the field as `category`, so the mismatch causes the category to be silently dropped from stream processing results.

## Hints

The fix is in `ProductAnalyticsHelper.Codeunit.al` inside the procedure that builds the per-record JSON object:

```al
JsonObject.Add('productCategory', Format(ProductAnalyticsLookup.Category));  // wrong key
```

Change it to:

```al
JsonObject.Add('category', Format(ProductAnalyticsLookup.Category));  // correct key
```
