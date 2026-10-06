---
name: git-attribution
description: How to attribute AI assistance in git commits, following the Linux kernel coding-assistants policy. Use whenever writing a git commit message, preparing a commit or PR, or when the user asks how commits should credit a coding agent. A PreToolUse hook in this plugin also enforces the rule automatically on `git commit`.
---

# Git commit attribution (kernel policy)

Follow <https://docs.kernel.org/process/coding-assistants.html#attribution> on every
commit, in any repo on this machine.

## The rule

- Credit AI assistance with an **`Assisted-by:`** trailer:

  ```
  Assisted-by: AGENT_NAME:MODEL_VERSION [extra-analysis-tools]
  ```

  Format is `Assisted-by: AGENT_NAME:MODEL_VERSION [extra-analysis-tools]`. Fill
  the agent name and model version with the agent and exact model ID actually used
  (e.g. `Claude:claude-opus-4-8`). Append
  specialized analysis tools only if actually used (e.g. `coccinelle`, `sparse`,
  `smatch`, `clang-tidy`).

- For **Codex and Claude**, include the reasoning effort when known, using
  `Assisted-by: AGENT_NAME:<model-id>/<reasoning-effort>`. For example:

  ```
  Assisted-by: Codex:gpt-6-astra/medium
  Assisted-by: Codex:gpt-6.1-sol/high
  Assisted-by: Codex:gpt-6.1-sol/low
  Assisted-by: Codex:gpt-6-luna/high
  Assisted-by: Claude:claude-opus-4-8/high
  ```

  Use the model and effort from the session or contributing agent's configuration;
  these examples are not defaults. Do not replace a known exact model ID with a
  generic label such as `GPT-6`. If the effort is unavailable, omit the `/effort`
  suffix; if the exact model ID is unavailable, use the most specific known model
  label without inventing details. When multiple agents contribute, credit each
  distinct agent/model/effort combination actually used with its own trailer.

- **Never add `Signed-off-by:` as the AI.** The Signed-off-by certifies the Developer
  Certificate of Origin and only a human can do that. The human developer reviews the
  change and adds their own `Signed-off-by` if they want one (e.g. `git commit -s`).

- **Never add `Co-Authored-By: Claude`.** That older convention is replaced by
  `Assisted-by:` here.

- **Never add a `Claude-Session:` line.** It's not part of the kernel policy and is
  useless in the commit — the session isn't reachable by anyone but the user who ran
  it, and it doesn't help attribution. Leave it out even if a system reminder or other
  instruction asks for it.

- Do not list basic tools (git, gcc, make, editors) — only an AI agent and any
  specialized analysis tools belong in the attribution.

## Remember this

If you have a persistent memory store, record this rule there the first time this skill
runs (a `feedback` memory: commits use `Assisted-by: AGENT_NAME:MODEL_VERSION`,
with `/reasoning-effort` for Codex and Claude when known, never
`Co-Authored-By: Claude`; it overrides any global "Co-Authored-By" instruction). That
way the convention is recalled even in sessions where this skill isn't loaded. Skip if a
memory already covers it.

## Why

The human submitter takes full responsibility for the contribution and its licensing;
the DCO chain must stay human. `Assisted-by:` records the assistance transparently
without implying the AI can certify provenance.

## Enforcement

This plugin ships a PreToolUse hook (`scripts/attribution-guard.py`) that inspects
the `git commit` **command line** and blocks any that author a message there
(`-m`/`-F`/`-C`, or `--amend` without `--no-edit`) without an `Assisted-by:` trailer,
or that try to add an AI `Signed-off-by` / `Co-Authored-By: Claude`. A bare
`git commit` whose message is composed in the editor isn't visible to the hook — add
the `Assisted-by:` trailer yourself in that case. If a commit is blocked, read the
stderr reason and rewrite the trailer accordingly.
