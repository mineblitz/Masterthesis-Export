# CODE-ACCORD experiment results

Each `exp_NNN.json` contains the complete set of result documents returned by
the experiment-family query for that ID. The files are projected for sharing:

- run identifiers, experiment/pipeline IDs, timestamps, and model/configuration
  fields are preserved;
- scored outcomes, extracted values, generated model output, token counts,
  pipeline durations, used documents, and component traces are preserved;
- the repeated input text (`request_payload.content`) and its rendered-prompt
  copy (`api_response.result.full_prompt`) are omitted because the same input
  record is included in `../datasets/`;
- each result points to its dataset record by file path and source identifiers.

The JSON files include all pipeline versions returned by the experiment-family
query. In particular, `exp_089.json` contains 2,126 v17 records and 194 v8
records. The pipeline is retained per row and counts are listed in
`export_manifest.json`; do not combine the v8 rows with v17 results.

The exports are snapshots of MongoDB results, not provider invoices. Estimated
costs are not added or inferred in this export.
