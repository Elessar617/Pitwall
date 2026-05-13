# External Resources

Curated resources for working with Claude (Code, API, plugins). Sourced from the Clief Resource Index (`docs/teaching/clief-notes/resource_index.pdf`).

## Official Anthropic

| Resource | URL | What it's for |
|---|---|---|
| Anthropic Skills repo | github.com/anthropics/skills | Production skills (docx, pptx, xlsx, pdf), examples for creative/enterprise/dev workflows. The 4 office skills in this repo's `.claude/skills/` come from here. |
| Claude Code | github.com/anthropics/claude-code | The CLI agent. Plugin system, subagent architecture, example plugins. |
| Official plugin marketplace | github.com/anthropics/claude-plugins-official | Browse via `/plugin marketplace`. |
| Knowledge work plugins | github.com/anthropics/knowledge-work-plugins | Open-source plugins for Claude Cowork (desktop automation). |
| Anthropic Cookbook | github.com/anthropics/anthropic-cookbook | Jupyter notebooks for the API: tool use, structured output, prompt caching, RAG, embeddings. |
| Courses | github.com/anthropics/courses | Official educational content: prompt engineering, tool use, RAG. |
| Quickstarts | github.com/anthropics/anthropic-quickstarts | Deployable starter apps using the Claude API (customer support agent, financial analyst, computer use demo). |

## Community skill collections

| Resource | URL | Use case |
|---|---|---|
| `obra/superpowers` | github.com/obra/superpowers | **Already enabled in this repo** (see `MCP-SETUP.md`). 20+ skills: TDD, debugging, brainstorming, planning. By Jesse Vincent. |
| `affaan-m/everything-claude-code` | github.com/affaan-m/everything-claude-code | **Already enabled in this repo.** Production setup, hook patterns, security scanning. Hackathon winner. |
| `travisvn/awesome-claude-skills` | github.com/travisvn/awesome-claude-skills | Comprehensive community list, categorized. |
| SkillsMP | https://skillsmp.com | Web directory of 400K+ agent skills, searchable. |
| AgentSkills.io | https://agentskills.io | Open spec for cross-platform agent skills. |

## Documentation

| Resource | URL | What it's for |
|---|---|---|
| Anthropic docs (Claude.ai) | https://docs.claude.com | Claude.ai features, API reference, prompt engineering. |
| Anthropic docs (Claude Code) | https://code.claude.com/docs | Claude Code-specific: skills, hooks, MCP, plugins, settings. |
| Skills Explained (blog) | https://claude.com/blog/skills-explained | Definitive post on Skills vs Projects vs Prompts vs MCP vs Subagents. Read first when confused. |

## When to use what

- **Want a working API example?** → Anthropic Cookbook
- **Want a deployable starter?** → Anthropic Quickstarts
- **Want a Claude Code workflow?** → obra/superpowers
- **Want to learn fundamentals?** → Anthropic Courses
- **Confused about which Claude feature to use?** → Skills Explained blog post

---

## Pitwall-specific: Formula 1 data sources

The APIs and Python libraries Pitwall depends on. See `.claude/reference/project-architecture.md` for how each is wired into the app.

| Resource | URL | What it's for |
|---|---|---|
| **FastF1** | https://docs.fastf1.dev / github.com/theOehrly/Fast-F1 | Python library wrapping the official F1 timing API plus Ergast. Used for tyre compound history and telemetry to fit tyre-degradation curves. Heavier install (`pandas`, `numpy`); used in batch and cached. |
| **OpenF1** | https://openf1.org/ / https://api.openf1.org | REST + WebSocket relay of the F1 live timing feed. Free, no auth. Source of driver positions (the track map), gaps, sector times, lap data during sessions. |
| **Jolpica-F1** | https://github.com/jolpica/jolpica-f1 / https://api.jolpi.ca/ergast/ | Direct successor to the now-frozen Ergast API. Free REST. Powers schedule, standings, drivers, constructors, results history. |
| **Ergast (archived)** | https://ergast.com/mrd/ | Historical F1 results API; frozen end-of-2024. Use Jolpica-F1 for live data; Ergast docs remain useful as the API contract reference. |
| **Formula 1 official** | https://www.formula1.com | Authoritative schedule, regulations, news. Used as a human cross-reference, not a programmatic source. |
| **FIA** | https://www.fia.com | Governing body; sporting and technical regulations. |
| **Pirelli motorsport** | https://www.pirelli.com/tires/en-ww/motorsport/f1 | Tyre compound allocations per Grand Prix (C1-C5 mapping to Soft/Medium/Hard). |
