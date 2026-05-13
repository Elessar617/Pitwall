# Routing Branch: Refactor / Migration

## Always load

- Agents: `planner`, `implementer`, `reviewer`, `adversary`, `refactor-cleaner`, `code-simplifier`
- Skills: `tdd-loop`, `karpathy-guidelines`
- Rules: all native rules
- Hook profile: `standard`
- MCPs (advisory): `filesystem`, `git`

## Language matrix

| Files match            | Add from ECC                          |
|------------------------|---------------------------------------|
| `*.py`                 | `python-reviewer`, `python-patterns`  |
| `*.go`                 | `go-reviewer`, `golang-patterns`      |
| `*.ts`, `*.tsx`        | `typescript-reviewer`                 |
| `*.java`               | `java-reviewer`                       |
| `*.kt`                 | `kotlin-reviewer`                     |

## Notes

Refactors require both reviewer and adversary because regressions are the dominant risk.
