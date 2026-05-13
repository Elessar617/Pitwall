# Routing Branch: Bug Fix

## Always load

- Agents: `implementer`, `reviewer` (no planner for bugs)
- Skills: `bug-investigation`, `tdd-loop`, `systematic-debugging`
- Rules: all native rules
- Hook profile: `standard`
- Slash commands (advisory): `/build-fix`
- MCPs (advisory): `filesystem`, `git`

## Language matrix

| Files match            | Add from ECC                                |
|------------------------|---------------------------------------------|
| `*.py`                 | `python-reviewer`                           |
| `*.go`                 | `go-reviewer`, `go-build-resolver`          |
| `*.ts`, `*.tsx`        | `typescript-reviewer`                       |
| `*.java`               | `java-reviewer`, `java-build-resolver`      |
| `*.kt`                 | `kotlin-reviewer`, `kotlin-build-resolver`  |
| `*.cpp`, `*.cc`, `*.h` | `cpp-reviewer`, `cpp-build-resolver`        |

## Notes

Bugs skip the planner — no design surface to plan. Implementer + reviewer work directly from the failing test.
