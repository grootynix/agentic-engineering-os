---
name: threat-model
description: Produce a lightweight threat model before changing auth, crypto, network, or data stores. Use when the user mentions threats, STRIDE, attack surface, or security design.
---

# Threat model

Do this **before** implementation for new or changed trust boundaries.

1. Assets and data classes (what you protect).
2. Trust boundaries and actors.
3. STRIDE-style threats that apply; skip empty categories.
4. Mitigations already in the code vs still needed.
5. Residual risk and who must accept it.

Write evidence to `sdlc/review.md` or a `threat-model` section in `sdlc/plan.md`. Do not treat this note as a control; SAST/hooks/CI are later.
