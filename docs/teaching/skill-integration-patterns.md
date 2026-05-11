# Skill Integration Patterns

Skills aren't just .md files. The CONTEXT routing tells the agent WHEN to invoke a skill. Below are the four patterns this scaffold uses, with examples from the current setup.

## 1. The pipeline gate

A skill that MUST run at a specific stage transition.

```markdown
<!-- In .claude/rules/testing-discipline.md -->
TDD is mandatory. The implementer agent invokes .claude/skills/tdd-loop/SKILL.md every cycle.
The pre-commit-tdd.sh hook enforces this by blocking commits without test files.
```

The combination of rule + skill + hook is the gate: the rule states the discipline, the skill encodes the procedure, the hook enforces by construction.

## 2. The stage specialist

A skill that activates only at one specific stage.

```markdown
<!-- In build/workflows/CONTEXT.md routing table -->
| Plan iteration   | Source artifact, .claude/agents/planner-agent.md          |
| Implement cycle  | SPEC.md, .claude/skills/tdd-loop/SKILL.md                 |
| Review cycle     | SPEC.md, .claude/agents/reviewer-agent.md                 |
```

The implementer cycle never loads the planner agent. The reviewer never sees the implementer's reasoning. Skills + agents are contextual, not global.

## 3. The format trigger

A skill that activates based on the OUTPUT FORMAT.

```markdown
<!-- In ship/CONTEXT.md -->
| /docx | Word deliverables   | From anthropics/skills |
| /pdf  | PDF deliverables    | From anthropics/skills |
| /pptx | Slide decks         | From anthropics/skills |
| /xlsx | Spreadsheets        | From anthropics/skills |
```

The `ship/` workspace has no pipeline; the OUTPUT FORMAT determines which skill loads.

## 4. The cross-workspace skill

A skill referenced from multiple workspaces with different triggers.

```markdown
<!-- The data-analysis skill -->
- In lab/CONTEXT.md: triggered when running data-heavy spikes
- In .claude/skills/spike-protocol/: cross-referenced as "use this when computing"
```

Same skill, different trigger conditions per workspace.

## When to add a skill

- You repeat the same multi-step procedure across iterations → make it a skill.
- Agents make the same mistake repeatedly → add a skill that documents the right procedure.
- A built-in or community skill (`obra/superpowers`, `anthropics/skills`) already does what you need → enable it via plugin or vendor it; don't reinvent.

## When NOT to add a skill

- Single-use procedure → just prompt directly.
- Procedure that varies wildly per call → write the variations into the rule, not the skill.
- The skill would just be "be careful" → that's not a procedure; either add a hook (enforces by construction) or accept that some judgment is irreducible.
