---
name: data-analysis
description: Use when the work involves analyzing data, computing statistics, or producing visualizations from data files. Encodes the trigger phrasing for code-execution that yields better results.
---

# Data Analysis

Code execution (the Python sandbox in Claude.ai, or local execution via Claude Code) is the right tool for any computation that needs a real answer rather than a confident guess. The trigger phrasing matters.

## The phrasing rule

**Tell Claude what you want to know, not what code to write.**

Better: *"What's the average deal size by quarter from this spreadsheet?"*
Worse: *"Write a pandas script to calculate quarterly deal-size averages."*

Why: Claude knows several ways to compute the answer (pandas, numpy, raw Python, sqlite-in-memory). Letting Claude choose produces shorter, more reliable code. The "write a pandas script" framing forces a specific implementation path that may not be the best fit for the data.

## When to use

- Precise calculations (statistics, financial math, anything where rounding matters)
- Verification work (running the code rather than reasoning about it)
- Charts and visualizations from real data
- File processing (parsing CSVs, transforming JSON, batch-renaming images)
- Numeric checks during code review (does this benchmark actually show what the PR claims?)

## When to skip

- Conceptual questions ("should we use Postgres or MySQL?")
- Quick lookups that don't need real data
- Cases where the computation is simple enough to do mentally and the data is in front of you

## In `lab/` iterations

Data-heavy spikes often live entirely in code execution: load the data, compute, plot, decide. The prototype/ folder may have nothing more than a script (or a notebook export) and the VERIFY.md captures the numbers.

## In `build/` iterations

Code execution is for one-off questions during implementation, not for production code. Production data-processing code lives in `src/` and goes through TDD. If the implementer finds themselves running the same computation manually three times, that's a signal to lift it into `src/` with tests.
