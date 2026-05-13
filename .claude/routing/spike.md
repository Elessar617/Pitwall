# Routing Branch: Spike / Investigation

## Always load

- Agents: `general-purpose`, `Explore`, `code-explorer`
- Skills: `spike-protocol`, `data-analysis`
- Rules: portability only (other 4 relaxed during exploration)
- Hook profile: `minimal` (lab/ work doesn't need TDD enforcement)
- MCPs (advisory): `filesystem`, `fetch`

## Language matrix

Language-specific agents are NOT auto-loaded for spikes — the spike's purpose is to discover language constraints, not enforce them. The spike's REPORT.md can recommend follow-up routing.

## Notes

Spikes maximize exploration freedom. The auto-selector recommends `minimal` hook profile so TDD-failing commits don't block iterative learning.
