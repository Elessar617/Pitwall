# Rule: NASA Power of 10 (when applicable)

**Apply the relevant subset of Gerard Holzmann's "Power of 10" rules for safety-critical code. Reason about applicability per-task rather than applying universally.**

**Why:** The Power of 10 rules were authored for JPL flight software where bugs literally crash spacecraft. They are *deliberately conservative*: each rule trades developer productivity for verifiability. Most code we write does NOT need flight-software discipline. But several of the rules encode universally-good practice that costs nothing to follow. The trick is knowing which to apply when, rather than applying them all by default or ignoring them entirely.

**The 10 rules (summary):**

1. **Restrict to simple control flow.** No `goto`, no recursion, no `setjmp`/`longjmp`.
2. **All loops have fixed upper bounds.** Bounds must be statically verifiable.
3. **No dynamic memory allocation after initialization.** Eliminates leaks and fragmentation.
4. **No function longer than ~60 lines.** Must fit on one printed page.
5. **At least two assertions per function on average.** Assertions must be side-effect-free and boolean.
6. **Restrict data scope to the smallest possible.** Minimize globals; declare close to use.
7. **Check return values of non-trivial functions; validate arguments.** No silent ignoring.
8. **Restrict preprocessor use.** Header inclusion + simple macros only; no token-pasting, no varargs.
9. **Restrict pointer use to one level of dereferencing; no function pointers.**
10. **All warnings enabled at maximum strictness; warnings as errors; static analysis must pass.**

**How to apply (per rule):**

- **Universal subset (always relevant; cost-free):**
  - **#2** — every loop should have a clear, statically-known upper bound on iterations. Use a counter + guard when the language allows truly unbounded loops (`while true`).
  - **#7** — every non-trivial call's return should be checked, including in tests. Suppress with intent (e.g., `void _ = foo()` or destructure-and-ignore), never silently.
  - **#10** — lint and static analysis pass before commit. Warnings are unfinished bugs; treat them as errors.
- **Often relevant (apply unless the cost is real):**
  - **#4** — aim for short functions; ~60 lines is a soft cap. Long functions are usually doing too much. Refactor when a function won't fit in your head.
  - **#6** — declare variables in the narrowest scope; avoid module-level mutable state unless it represents genuine identity.
- **Language-dependent (mostly C/C++ specific):**
  - **#1, #3, #8, #9** — these address C/C++ failure modes (manual memory, preprocessor abuse, raw pointers). In Node.js, Python, Go, Rust, etc., the runtime/compiler handles most of what these rules guard against. Skip unless you're writing C/C++.
- **Domain-dependent:**
  - **#5** — assertion density matters for safety-critical code, less so for application code. Use judgment; a 5-line helper does not need 2 assertions. Aim for assertion *where it would catch the bug you fear*.

**When to apply the FULL set:**

- Firmware, drivers, kernel modules.
- Real-time systems with hard deadlines.
- Code controlling physical actuators, financial transactions, or anything irreversible.
- Long-lived daemons where any bug means downtime.

**When to apply ONLY the universal subset (#2, #4, #6, #7, #10):**

- Most application code, CLI tools, services, glue scripts.
- Anything in a high-level language with managed memory.

**When to skip almost entirely:**

- Throwaway prototypes, spikes, one-off scripts.
- Exploratory data analysis where the goal is *learning*, not *correctness under stress*.

**Heuristic for reaching for it:** Ask "if this code silently misbehaves, what's the worst that happens?" If the worst is "a confused user re-runs the command," apply the universal subset only. If the worst is "data loss, financial loss, safety incident, or production outage," apply the full set — and consider testing accordingly.

**Heuristic for picking ad-hoc rules:** Even outside safety-critical work, when you find yourself writing a long function (rule #4) or an unbounded loop (rule #2), pause and ask whether the structure is hiding a complexity you should address rather than tolerate.
