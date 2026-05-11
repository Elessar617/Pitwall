# Clief Notes Inventory

Capabilities and external resources extracted from the two Clief Notes PDFs (`clief_notes_skills_field_manual_v1.pdf`, `clief_notes_resource_index_v1.pdf`, both v1.0 / March 2026 by Jake Van Clief / Eduba). Use this as the wiring checklist when populating the new directory structure.

**Source files:** PDFs at `skills_field_manual.pdf` and `resource_index.pdf` in this same directory.

---

## Part 1 — Skills Field Manual: 10 Claude Capabilities

The manual divides ten Claude capabilities into two groups: **context architecture** (what the model sees) and **output mode** (how it delivers). Each entry below records its purpose, the trigger conditions ("use when" / "skip when"), the 60/30/10 layer, and where it should slot into our new workspace.

> **60/30/10 framework** (from the manual): 60% deterministic code, 30% rules / templates / repeatable processes, 10% AI judgment. Each capability operates primarily at one layer.

### Context Architecture (Skills 1–5) — control what the model sees

#### 1. Projects
- **What it does:** Persistent Claude.ai workspace with its own knowledge base (≤200K tokens), custom instructions, and chat history.
- **Use when:** Returning to the same body of work repeatedly; team needs shared AI workspace; you keep re-uploading the same documents.
- **Skip when:** One-off questions; quick brainstorming; knowledge base would exceed 200K tokens.
- **Layer:** Infrastructure — supports work at every layer.
- **Wire into our repo:** Document in `.claude/reference/claude-platform-capabilities.md` as a non-Code option for users who also work in Claude.ai. Not a primary mechanism for this repo (we're Claude Code first).

#### 2. Custom Skills
- **What it does:** Folders containing instructions, scripts, and reference files that Claude loads on demand. Each has a `SKILL.md` with name + description; description is the trigger condition Claude uses to auto-activate.
- **Use when:** Repeating the same instructions across conversations; need consistent output formatting; have a repeatable process.
- **Skip when:** One-off tasks; instructions fit in a single prompt; still figuring out the process.
- **Layer:** 30% (rules and templates).
- **Wire into our repo:** This **is** the `.claude/skills/` directory. Folder-per-skill convention with required `SKILL.md` (name + description in YAML frontmatter, then markdown). Optional siblings: `REFERENCE.md`, `templates/`, `examples/`, `scripts/`.

#### 3. Claude Code + CLAUDE.md
- **What it does:** CLI agent that reads project files, writes code, runs commands. `CLAUDE.md` at project root is auto-loaded into every conversation. Subagents are markdown files in `.claude/agents/` with YAML frontmatter (name, description, system prompt, tool permissions).
- **Use when:** Building/maintaining software; multi-step tasks; want specialized subagents for testing, docs, security review.
- **Skip when:** Not in a codebase (use Claude.ai + Projects); task is small enough for a single chat message.
- **Layer:** Operates across all three (CLAUDE.md and subagent definitions are 30%; generated code is 60% or 10%).
- **Wire into our repo:** This is the foundation. Our root `CLAUDE.md` + `.claude/agents/{planner,implementer,reviewer,adversary}-agent.md` files implement this directly. Routing table in `CONTEXT.md` mirrors the manual's example.

#### 4. MCP Connectors
- **What it does:** Model Context Protocol — open standard connecting Claude to external tools (Google Drive, Gmail, Slack, Jira, GitHub, Notion, Stripe, etc.). Claude can read real data and take actions.
- **Use when:** Need real data not pasted into chat; want Claude to take actions; workflow crosses multiple tools.
- **Skip when:** Data fits in chat; haven't reviewed the connector's permissions; just need analysis (no action).
- **Layer:** Infrastructure / plumbing. Action layer varies (60% pull, 30% rule-based routing, 10% judgment).
- **Wire into our repo:** Document available MCP servers in `.claude/reference/mcp-servers.md` (populated from the Resource Index entries below). Configure project-level MCP servers in `.claude/settings.json`. Always start read-only.

#### 5. Memory
- **What it does:** Cross-conversation personalization in Claude.ai. Retains facts about you across chats. Account-scoped, applies outside Projects.
- **Use when:** Using Claude as a general assistant; have stable preferences (writing style, technical level).
- **Skip when:** Working inside a Project (Project context overrides); need precise structured context; want context-free conversation (incognito).
- **Layer:** Infrastructure — calibrates all three layers.
- **Wire into our repo:** Document in `.claude/reference/claude-platform-capabilities.md`. Not directly applicable in Claude Code (which uses CLAUDE.md and `~/.claude/projects/.../memory/` instead). Mention as a Claude.ai parallel.

### Output Mode (Skills 6–10) — control how it delivers

#### 6. Code Execution
- **What it does:** Claude writes and runs Python in a sandbox during the conversation. Real results, not guesses.
- **Use when:** Precise calculations; data analysis; verifying its own work; charts from real data.
- **Skip when:** Conceptual questions; quick training-data answers; spreadsheet-formula simple.
- **Layer:** 60% (deterministic code).
- **Wire into our repo:** Document trigger phrasing in `.claude/skills/data-analysis/SKILL.md` ("tell Claude *what you want to know*, not what code to write"). Most relevant for `lab/` iterations doing analysis.

#### 7. Artifacts
- **What it does:** Interactive renderable outputs alongside the conversation: React components, HTML, SVG, Mermaid diagrams, markdown.
- **Use when:** Interactive tool needed; visual output; prototype/PoC to share; document that will iterate.
- **Skip when:** Answer fits in chat; need production file format (use file creation); content is short.
- **Layer:** 30% (rule-based interactive interfaces).
- **Wire into our repo:** Most useful in `lab/` for prototypes. Document as an option in `lab/CONTEXT.md` skills table. Not appropriate for `build/` (production code goes in `src/`).

#### 8. File Creation
- **What it does:** Claude creates `.docx`, `.pptx`, `.xlsx`, `.pdf` with proper formatting. Built-in skills handle technical details.
- **Use when:** Deliverable for Office/Google Workspace; needs professional formatting; external use.
- **Skip when:** Content is for own reference (use markdown/artifacts); short enough to copy from chat.
- **Layer:** 30% (format and structure rules) + 60% (deterministic file format handling).
- **Wire into our repo:** Built-in skills already exist (`/docx`, `/pptx`, `/xlsx`, `/pdf`). Reference them in `ship/CONTEXT.md` for release artifacts (e.g., a release deck) and in `docs/` workspace for user-facing docs. The reference implementations live in `claude-office-skills-ref/` (currently in repo) — move these to `.claude/reference/office-skills/`.

#### 9. Web Search + Deep Research
- **What it does:** Web Search pulls current info; Deep Research conducts multi-step research across many sources and produces a comprehensive report.
- **Use when:** Need current info (prices, news, recent events); facts that change frequently; want verification beyond training data; comprehensive research report (Deep Research).
- **Skip when:** Established/stable facts; analyzing data already provided; topic well within training data.
- **Layer:** Web search is 60% lookup; Deep Research is 10% synthesis.
- **Wire into our repo:** Heavy use in `spec/` (RFC research) and `lab/PREFLIGHT.md` (literature review). Document trigger phrasing in `.claude/skills/spec-authoring/SKILL.md` and `.claude/skills/spike-protocol/SKILL.md`.

#### 10. Extended Thinking
- **What it does:** Claude reasons step-by-step before answering. Visible thinking block above the response.
- **Use when:** Multiple interacting constraints; need to weigh trade-offs; math/logic precision; want to audit reasoning.
- **Skip when:** Straightforward answer; speed > depth; creative content where overthinking hurts.
- **Layer:** 10% (genuine judgment / synthesis).
- **Wire into our repo:** Activated via the planner agent and reviewer agent (where weighing trade-offs matters). Document in `.claude/agents/planner-agent.md` and `reviewer-agent.md`.

### The Decision Sequence (from §4.1 of the manual)

When starting a task, run through these in order:
1. Need persistent context? → use a Project. No → regular chat.
2. Need external data? → enable MCP / upload files. No → proceed.
3. Repeatable process? → build/use a skill. No → prompt directly.
4. Output format? File → file creation. Interactive → artifact. Data → code execution. Text → just talk.
5. Need deep reasoning? → extended thinking. No → standard.

**Wire into our repo:** Embed this as the routing logic in our top-level `CONTEXT.md`.

---

## Part 2 — Resource Index: 40+ Curated Resources

> **Trust note (from the manual):** Community skills and MCP servers can execute code on your machine. Only install from repos you've reviewed. Anthropic's own repos are safe.

### 2.1 Official Anthropic Repos

| Resource | URL | Purpose | Wire into |
|---|---|---|---|
| **anthropics/skills** | github.com/anthropics/skills | Production skills (docx, pptx, xlsx, pdf) + example skills. Reference implementation for skill structure. | **Install:** copy `public/{docx,pptx,xlsx,pdf}/` from local `claude-office-skills-ref/` into `.claude/skills/{docx,pptx,xlsx,pdf}/`. Link in `external-resources.md`. |
| **anthropics/claude-code** | github.com/anthropics/claude-code | The CLI agent itself. Plugin system, subagent architecture, example plugins. | `.claude/reference/external-resources.md` |
| **anthropics/claude-plugins-official** | github.com/anthropics/claude-plugins-official | Official plugin marketplace (browse via `/plugin marketplace`). | `.claude/reference/external-resources.md` |
| **anthropics/knowledge-work-plugins** | github.com/anthropics/knowledge-work-plugins | Knowledge worker plugins for Claude Cowork. | `.claude/reference/external-resources.md` |
| **anthropics/anthropic-cookbook** | github.com/anthropics/anthropic-cookbook | Jupyter notebooks for the API: tool use, structured output, prompt caching, RAG, embeddings. | `.claude/reference/external-resources.md` |
| **anthropics/courses** | github.com/anthropics/courses | Official educational content: prompt engineering, tool use, RAG. | `.claude/reference/external-resources.md` |
| **anthropics/anthropic-quickstarts** | github.com/anthropics/anthropic-quickstarts | Deployable starter apps using the Claude API (customer support, financial analyst, computer use). | `.claude/reference/external-resources.md` |

### 2.2 Community Skill Collections

| Resource | URL | Purpose | Wire into |
|---|---|---|---|
| **travisvn/awesome-claude-skills** | github.com/travisvn/awesome-claude-skills | Most comprehensive community list. Categorized (creative, technical, enterprise, document). | `.claude/reference/external-resources.md` |
| **obra/superpowers** | github.com/obra/superpowers | 20+ battle-tested skills for Claude Code: TDD, debugging, `/brainstorm`, `/write-plan`, `/execute-plan`. By Jesse Vincent. | **Install as plugin** — enable in `.claude/settings.json`. Install command in `.claude/MCP-SETUP.md`. |
| **affaan-m/everything-claude-code** | github.com/affaan-m/everything-claude-code | Anthropic hackathon winner. Production-grade Claude Code setup: skills, memory, security scanning, hooks. 1200+ tests. | **Install as plugin** — enable in `.claude/settings.json`. Borrow hook patterns for our own `.claude/hooks/`. |
| **SkillsMP** | https://skillsmp.com | Web directory of 400,000+ agent skills. Searchable. Works with Claude Code + Codex. | `.claude/reference/external-resources.md` |
| **AgentSkills.io** | https://agentskills.io | Open spec for agent skills. Cross-platform compatibility (Claude/Codex/etc.) | `.claude/reference/external-resources.md` |

### 2.3 MCP Servers and Directories

| Resource | URL | Purpose | Wire into |
|---|---|---|---|
| **modelcontextprotocol/servers** | github.com/modelcontextprotocol/servers | Reference MCP server implementations (Filesystem, GitHub, Google Drive, Slack, Postgres, Puppeteer). | **Configure 3 credential-free in `.claude/settings.json`**: `filesystem` (scoped to repo), `git`, `fetch`. Catalog the rest in `.claude/reference/mcp-servers.md`. |
| **github/github-mcp-server** | github.com/github/github-mcp-server | GitHub's official MCP. Repo management, issue/PR automation, CI/CD intelligence, code analysis, Dependabot. | **Configure with `${GITHUB_TOKEN}` placeholder** in `.claude/settings.json` (read-only first). Setup steps in `.claude/MCP-SETUP.md`. |
| **stripe/agent-toolkit** | github.com/stripe/agent-toolkit | Stripe MCP. Payment links, invoices, subscriptions. | Optional — for projects that touch payments. |
| **punkpeye/awesome-mcp-servers** | github.com/punkpeye/awesome-mcp-servers | Largest curated MCP server list. Categorized with icons. | `.claude/reference/mcp-servers.md` |
| **wong2/awesome-mcp-servers** | github.com/wong2/awesome-mcp-servers | Second curated list with broader categories. Cross-reference with punkpeye. | `.claude/reference/mcp-servers.md` |
| **tolkonepiu/best-of-mcp-servers** | github.com/tolkonepiu/best-of-mcp-servers | 410+ servers ranked by quality score (stars, contributors, commit frequency). Updated weekly. | `.claude/reference/mcp-servers.md` — best for *finding* servers. |
| **modelcontextprotocol.io** | https://modelcontextprotocol.io | MCP spec site. Protocol docs, example servers/clients, building custom integrations. | `.claude/reference/external-resources.md` |

### 2.4 Programmatic Video — Remotion (likely lower priority for general dev lab)

| Resource | URL | Purpose | Wire into |
|---|---|---|---|
| **remotion-dev/remotion** | github.com/remotion-dev/remotion | React → MP4/WebM/audio. Hot-reload dev. Requires company license for teams of 3+. | Skip unless project does video. Mention in `.claude/reference/external-resources.md` under "Specialized." |
| **GitHub topic: remotion** | github.com/topics/remotion | Remotion-tagged repos: short-form video, TikTok captions (Whisper), product showcases, Next.js integrations. Notable: `designcombo/react-video-editor`, `remotion-dev/template-react-router`, `thecmdrunner/swiftube-creator`. | Skip for general dev lab. |
| **Remotion Docs: Prompting with Claude Code** | https://www.remotion.dev/docs | Remotion docs include section on prompting with Claude Code. Best Practices Agent Skill exists. | Skip for general dev lab. |

### 2.5 Frontend, UI, and Design

| Resource | URL | Purpose | Wire into |
|---|---|---|---|
| **shadcn-ui/ui** | github.com/shadcn-ui/ui | Copy-paste React components on Radix + Tailwind. Claude knows the patterns natively. **Default for new React projects.** | `.claude/reference/frontend-stack.md` (placeholder doc to populate per consumer repo). High priority for any repo with React. |
| **tailwindlabs/tailwindcss** | github.com/tailwindlabs/tailwindcss | Utility-first CSS. Claude generates Tailwind classes natively. | `.claude/reference/frontend-stack.md` |
| **Acternity UI / Magic UI** | https://ui.acternity.com / https://magicui.design | Animated React components: spotlight cards, beams, 3D transforms. For landing pages and demos. | `.claude/reference/frontend-stack.md` (optional) |
| **lucide-icons/lucide** | github.com/lucide-icons/lucide | 1500+ MIT icons. Claude's default icon library in React artifacts (`lucide-react`). | `.claude/reference/frontend-stack.md` |
| **recharts/recharts** | github.com/recharts/recharts | React charts on D3. Claude's default for data viz in artifacts. | `.claude/reference/frontend-stack.md` |
| **v0 by Vercel** | https://v0.dev | Vercel's AI UI generator. Outputs shadcn/ui + Tailwind React. | `.claude/reference/external-resources.md` |

### 2.6 Learning and Reference

| Resource | URL | Purpose | Wire into |
|---|---|---|---|
| **Anthropic Documentation** | https://docs.claude.com & https://code.claude.com/docs | Official docs. Claude.ai features, API reference, Claude Code, skill authoring. | `.claude/reference/external-resources.md` — bookmark both. |
| **Anthropic Blog: Skills Explained** | https://claude.com/blog/skills-explained | Definitive post on Skills vs Projects vs Prompts vs MCP vs Subagents. Includes decision matrices. | `.claude/reference/external-resources.md` — read first when confused. |

### 2.7 The 60/30/10 Lens (from §8 of the index)

The index closes with a quick reference for which layer each resource serves:

| Category | What it helps build | Layer |
|---|---|---|
| Official Skills (docx, xlsx, etc.) | File creation, document processing | 30% Rules |
| Claude Code + Plugins | Code generation, project automation | All |
| MCP Servers | External tool integration, data access | Infrastructure |
| Remotion | Programmatic video rendering | 60% Code |
| Frontend / UI Libraries | Interface components, visualizations | 30% Rules |
| Learning / Reference | Understanding the tools | Foundation |
| Community Skills | Specialized workflows, custom processes | 30% Rules |

**Closing principle (manual + index agree):** "Knowing what tools exist and when to reach for them is worth more than getting better at raw prompting. A mediocre prompt aimed at the right skill outperforms a brilliant prompt aimed at nothing."

---

## Part 3 — Implementation Checklist (for the redesign)

Order of operations after the new directory structure lands:

1. **Move PDFs** → `docs/teaching/clief-notes/{skills_field_manual.pdf,resource_index.pdf}` and this inventory → `docs/teaching/clief-notes/inventory.md`.
2. **Decompose `claude-office-skills-ref/`:**
   - `public/{docx,pptx,xlsx,pdf}/` → `.claude/skills/{docx,pptx,xlsx,pdf}/` (these become installed skills)
   - `skills-system.md` → `.claude/reference/skills-system.md`
   - `README.md`, `CLAUDE.md`, `package*.json` → `docs/teaching/office-skills-source/`
   - Then remove the now-empty `claude-office-skills-ref/` directory.
3. **Populate `.claude/reference/`:**
   - `claude-platform-capabilities.md` — Skills 1, 5 (Projects, Memory) + decision sequence (Manual §4.1)
   - `mcp-servers.md` — curated catalog from §2.3 (the lists; not the configured-in-settings.json ones)
   - `external-resources.md` — links from §2.1, §2.2, §2.6
   - `frontend-stack.md` — `<!-- REPLACE -->` placeholder for §2.5 (consumer fills in)
   - `iteration-pattern.md` — portable description of `lab/` and `build/` iteration shapes
4. **Wire trigger phrasing** for code execution and web search into:
   - `.claude/skills/data-analysis/SKILL.md` (Skill 6)
   - `.claude/skills/spec-authoring/SKILL.md` (Skill 9)
   - `.claude/skills/spike-protocol/SKILL.md` (Skill 9)
5. **Wire built-in file creation skills** (Skill 8 / now installed as `.claude/skills/{docx,pptx,xlsx,pdf}/`) into `ship/CONTEXT.md` skills table.
6. **Embed the decision sequence** (Manual §4.1) into the top-level `CONTEXT.md` routing logic.
7. **Wire plugins in `.claude/settings.json`:**
   - `obra/superpowers` — Jesse Vincent's superpowers (TDD, brainstorming, planning skills)
   - `affaan-m/everything-claude-code` — production Claude Code setup, hook patterns
8. **Wire MCP servers in `.claude/settings.json`:**
   - **Credential-free, configured directly:** `filesystem` (repo-scoped), `git`, `fetch`
   - **Credential-required, placeholder env var:** `github` with `${GITHUB_TOKEN}` (read-only first)
9. **Write `.claude/MCP-SETUP.md`** — plugin install commands, MCP credential setup, verification commands.

---

*Generated: 2026-05-10. Source PDFs: Clief Notes v1.0, March 2026, Jake Van Clief / Eduba.*
