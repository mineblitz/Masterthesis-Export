# Benchmark Brandschutz clean export

This folder contains a focused export of the experiment service and selected
CODE-ACCORD experiment artifacts. The service files were copied from the sibling
`Experiments_Brandschutz` repository at commit
`7e4992adbe06fb78a9499638cdac07f319577915`.

## Contents

- `service/app/`: experiment service implementation
- `service/docs/`: service documentation and experiment notes
- `service/prompts/`: versioned prompt files
- `configs/`: original configurations for the exported CODE-ACCORD experiments
- `datasets/`: the sentence, context, and full-PDF derived CODE-ACCORD datasets
- `results/codeaccord/`: MongoDB result exports, one JSON per experiment family
- `requirements.txt`: source repository dependencies
- `.gitignore`: source repository ignore rules

Python caches and virtual environments were excluded. The source repository's
`.env`, `.env.example`, and `system-information/` were not copied. The export
manifest explicitly excludes credentials, machine-specific system-information,
and internal approval/source documents unless redistribution is authorized.
The exported CODE-ACCORD corpus is attributed and licensed CC BY 4.0; see
[`datasets/README.md`](datasets/README.md). Result records retain model outputs,
scores, timestamps, pipeline identifiers, and resource fields. To avoid
repeating the public source text thousands of times, `request_payload.content`
and the redundant rendered `api_response.result.full_prompt` are omitted from
the result snapshots; each row links to its exported dataset record.
`exp_089.json` includes both v17 rows and 194 earlier v8 rows and labels the
pipeline on every record. Do not treat those v8 rows as v17 results.
