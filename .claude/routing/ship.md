# Routing Branch: Ship (release artifacts)

## Always load

- Agents: `reviewer`, `adversary`, `doc-updater`, `opensource-packager`
- Skills: none by default; add `docx`, `pptx`, `xlsx`, or `pdf` when the scoped output path has that extension
- Rules: all native rules (maximum strictness)
- Hook profile: `strict`
- MCPs (advisory): `filesystem`, `git`, `github`

## Output-format matrix

| Output type    | Skill                  |
|----------------|------------------------|
| `*.docx`       | `docx`                 |
| `*.pptx`       | `pptx`                 |
| `*.xlsx`       | `xlsx`                 |
| `*.pdf`        | `pdf`                  |
| Markdown notes | (no extra skill)       |

## Notes

`strict` profile reserved for ship/ workflows. Currently identical to `standard` but hooks honor it as a separate value for future extension.
