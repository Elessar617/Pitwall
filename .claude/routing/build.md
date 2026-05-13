# Routing Branch: Build (feature implementation)

> Loaded when Step 1 of ROUTING.md matches a feature-implementation signal.

## Always load

- Agents: `planner`, `implementer`, `reviewer`, `adversary`
- Skills: `tdd-loop`
- Rules: all native rules
- Hook profile: `standard`
- MCPs (advisory): `filesystem`, `git`

## Language matrix

| Files match            | Add from ECC                                          |
|------------------------|-------------------------------------------------------|
| `*.py`                 | `python-reviewer`, `python-patterns`                  |
| `*.go`                 | `go-reviewer`, `go-build-resolver`, `golang-patterns` |
| `*.ts`, `*.tsx`        | `typescript-reviewer`                                 |
| `*.java`               | `java-reviewer`, `java-build-resolver`                |
| `*.kt`                 | `kotlin-reviewer`, `kotlin-build-resolver`            |
| `*.cpp`, `*.cc`, `*.h` | `cpp-reviewer`, `cpp-build-resolver`                  |
| `*.cs`                 | `csharp-reviewer`                                     |
| `*.dart`               | `dart-build-resolver`, `flutter-reviewer`             |

## Notes

Authoring-time comments (not parsed by route.mjs). Add language rows as ECC's catalog grows.
