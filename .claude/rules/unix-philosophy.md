# Rule: Unix philosophy (when applicable)

**Make each program do one thing well. Make programs compose via plain-text interfaces. Prefer small, focused tools over monoliths.**

**Why:** Decades of Unix demonstrate that small composable tools age better than monoliths. A pipeline of focused programs is easier to test, debug, replace, and understand than one program that tries to do everything. The same shape applies inside a codebase: small modules with clear interfaces compose into systems humans can hold in their head. Files that "do one thing" survive refactoring; files that do five things accrete bugs at every seam.

**How to apply:**

- **One responsibility per unit.** A script, module, or function should have one reason to exist. If you can't describe its purpose in one sentence without "and", split it.
- **Plain text first.** Choose human-readable, line-oriented formats (JSON, Markdown, key=value) over binary blobs unless there is a measured reason not to. Plain text is greppable, diffable, and pipe-friendly.
- **Composition over completeness.** Two 50-line tools that pipe together beat one 200-line tool with a flag for every behavior. Push optionality to the caller.
- **Avoid hidden state.** A program that reads input and writes output is easier to compose than one that mutates globals. Prefer pure functions where the problem allows.
- **Fail clearly to stderr; succeed quietly to stdout.** Errors go to stderr. Successful results go to stdout. Don't mix.

**When NOT to apply:**

- **Interactive applications.** A GUI or REPL is not naturally a pipeline. Forcing pipeline shapes onto them hurts UX without payoff.
- **Genuinely indivisible operations.** Some problems do not factor cleanly. Don't fracture them artificially to look "Unix-y."
- **When integration overhead dominates.** If composing five small tools costs more in glue and setup than the function value, write the one tool.
- **Performance-critical paths.** Pipeline overhead (forking, IPC, serialization) can dominate. Sometimes an in-process call is correct even if the conceptual shape is a pipeline.

**Heuristic for reaching for it:** When designing the boundary between two pieces of code, ask "could these be two separate programs that communicate via stdin/stdout?" If yes, that's a strong signal the interface should be small and the contract should be plain text. The actual implementation can still be in-process — Unix philosophy describes the *shape* of the contract, not necessarily the deployment model.

**Heuristic for skipping it:** If applying the principle would require building plumbing that doesn't have an independent reason to exist, the cost has exceeded the benefit. Stop and write the monolith. Re-evaluate when the monolith starts to creak.
