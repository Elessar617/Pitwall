# Rule: Portability discipline

**Files in `.claude/rules/` and `.claude/skills/` must stay domain-agnostic. Project-specific facts live only in `.claude/reference/`. Enforced by `enforce-portability.sh`.**

**Why:** The whole repo is the canonical scaffold for OTHER repos. If a project-specific term ("our database is Postgres", "we use Stripe for billing") leaks into a rule or skill, that file becomes useless when copied into a project where the assumption is false. The hook catches drift mechanically.

**How to apply:**
- Anything specific to THIS repo's project, OR specific to the consumer repo at the time of bootstrap (vendor names, table names, internal endpoints, brand terms, compliance requirements), goes in `.claude/reference/` — never in `rules/` or `skills/`.
- Add new project-specific terms to `.claude/.portability-deny.txt` (one per line, case-insensitive grep). The hook fails any Edit/Write to `rules/` or `skills/` whose new content contains a denied term.
- When writing a rule or skill, reach for generic phrasing: "the project's lint command" not "`npm run lint`"; "the typed-language coverage threshold" not "70% line coverage".
- If you need a project-specific example to illustrate a rule, link to a file under `.claude/reference/` or `docs/` rather than inlining it.
- The deny list is a per-consumer artifact: each repo using this scaffold edits `.portability-deny.txt` to add its own terms. The base list shipped from this repo contains only generic placeholders the consumer should replace.
- Office skills under `.claude/skills/{docx,pptx,xlsx,pdf}/` are vendored from `anthropics/skills` and are exempt from portability scanning by path (the hook excludes them) — they're already generic.
