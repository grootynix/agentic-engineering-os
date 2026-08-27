# ADR 0002 — Harness and graph engineering

**Status:** Accepted

**Date:** 2026-08-27

## Context

The original brief forbids “another collection of prompts.” Global files like `AGENTS.md` tend to accrete workflow, policy, and procedure until they are both token-expensive and unenforceable. Linear chat is a poor model of SDLC: artifacts, required evidence, and fail/skip rules are graphs.

Cursor and Claude Code already provide **host harnesses** (context, tools, permissions, some hooks). This project must add a **portable harness layer** and an explicit work graph without pretending prompts are the OS.

## Decision

1. **Harness engineering (principle 11).** The OS is the runtime around the model: context assembly, tool/permission policy, hooks, verify loops, retries, stop conditions. Prompts, rules, and skills are inputs. Security and quality boundaries live in the harness (CLI, later policy engine, CI), not in instruction text. Adapters project harness *bindings*; they do not own workflow logic.

2. **Graph engineering (principle 12).** Work is a typed DAG. Nodes are steps; artifacts ride on edges; skills and specialized agents are node implementations. Packs and verification checks are the same pattern at other scales. Graphs are declarative data in `catalog/graphs/` (e.g. `sdlc.yaml`: intent → spec → plan → implementation → verification → review → PR). Do not encode the whole graph in `AGENTS.md`.

3. **Sequencing.** Milestone 1 shipped the harness **skeleton** and **validated** graph YAML. M2 walks the artifact chain (`agentic-sdlc graph`). M3 is verify-as-graph plus hooks. Evals (M5) score graph traces, not only final text.

## Consequences

- `agentic-sdlc verify` is a walk over discovered checks, not a permanent one-liner.
- Specialized agents have contracts (inputs, outputs, evidence), not generic personas.
- Token strategy: always-on files stay small; the graph discloses the next node’s context.
- M1 must not execute graphs or claim a harness loop that does not exist.

## Alternatives rejected

- **Prompt collections / mega-AGENTS.md as the product.** Violates least context, is untestable as a workflow, and is not a security boundary.
- **Walker in M1.** Init/doctor must land first; walking an empty or stub graph adds no consumer value.
- **Host-specific workflow only (Cursor rules vs Claude skills as the DAG).** Diverges hosts; workflow belongs in shared catalog data.
