# Benchmark Brandschutz clean export

This folder is a starting point for a standalone repository focused on the
experiment service. The service files were copied from the sibling
`Experiments_Brandschutz` repository at commit
`7e4992adbe06fb78a9499638cdac07f319577915`.

## Contents

- `service/app/`: experiment service implementation
- `service/docs/`: service documentation and experiment notes
- `service/prompts/`: versioned prompt files
- `requirements.txt`: source repository dependencies
- `.gitignore`: source repository ignore rules

Python caches and virtual environments were excluded. The source repository's
`.env`, `.env.example`, and `system-information/` were not copied. The export
manifest explicitly excludes credentials, machine-specific system-information,
and internal approval/source documents unless redistribution is authorized.
The experiment configurations, analysis code, datasets, and results described
in the manifest have not been added yet and should be selected and reviewed
before treating this as a reproducible release.
