# assisted-by

> Credit AI in git the way the Linux kernel says to — an **`Assisted-by:`** trailer, enforced.

A Claude Code and Codex plugin (and portable agent skill) that makes coding agents attribute
their help correctly on every commit, following the kernel's
[coding-assistants policy](https://docs.kernel.org/process/coding-assistants.html#attribution):

```
Assisted-by: Claude:claude-opus-4-8
Assisted-by: Codex:gpt-6.1-sol/high
```

It ships two things:

- **`git-attribution` skill** — teaches the agent the rule, so it writes the right trailer
  on its own.
- **`attribution-guard.py` hook** — a Claude Code and Codex `PreToolUse` hook that *blocks* a
  `git commit` if the agent gets it wrong, and tells it how to fix the message.

## The rule

- ✅ Credit AI with an **`Assisted-by:`** trailer:
  `Assisted-by: AGENT_NAME:MODEL_VERSION [extra-analysis-tools]`
  (e.g. `Assisted-by: Claude:claude-opus-4-8`).
- 🚫 **No `Signed-off-by:` from the AI** — the Signed-off-by certifies the Developer
  Certificate of Origin, and only a human can do that.
- 🚫 **No `Co-Authored-By: Claude`** — that older convention is replaced by `Assisted-by:`.
- 🚫 Don't list basic tools (git, gcc, editors) — only the AI agent and any specialized
  analysis tools (`coccinelle`, `sparse`, `smatch`, …).

For Codex and Claude, record the exact model ID and reasoning effort from the session
when known as `Assisted-by: AGENT_NAME:<model-id>/<reasoning-effort>`, for example:

```text
Assisted-by: Codex:gpt-6-astra/medium
Assisted-by: Codex:gpt-6.1-sol/high
Assisted-by: Codex:gpt-6.1-sol/low
Assisted-by: Codex:gpt-6-luna/high
Assisted-by: Claude:claude-opus-4-8/high
```

Use the configuration actually used, rather than a generic `Codex:GPT-6` label
when the exact model is known. Omit the effort suffix if unavailable and never
guess unknown model details. If multiple agents contribute, add a trailer for each
distinct agent/model/effort combination used. The hook accepts these formats.

## Install

### Claude Code — skill **+** enforcing hook (recommended)

```bash
claude plugin marketplace add bcmyguest/assisted-by
claude plugin install assisted-by@assisted-by
```

That registers this repo as a plugin marketplace and installs the plugin (skill + hook).
Restart Claude Code to load the hook.

### Codex — skill + enforcing hook

Register this checkout as a local marketplace:

```bash
codex plugin marketplace add .
```

Restart the desktop app. Open the Plugins Directory, select **Assisted-by**, and
install the plugin. In Codex CLI, use `/hooks` to review and trust the hook before
use. Codex skips new or changed hooks until you trust their current definition.
See the official [plugin setup](https://developers.openai.com/plugins/build/plugins)
and [hook trust](https://learn.chatgpt.com/docs/hooks) instructions.

The Codex manifest loads `hooks/codex.json`. On macOS and Linux, the command needs
`python3` on `PATH`. On Windows, it uses `uv run --no-project python`; install `uv`
and a uv-managed Python first. Codex supplies `PLUGIN_ROOT`, so the script path
works when you start a session in a subdirectory.

Installing the portable skill alone does not install the hook.

### opencode / Cursor / any skills-aware agent — skill only

The skill is in the portable [skills](https://skills.sh) format, so any agent that reads
`SKILL.md` can use the guidance:

```bash
npx skills add bcmyguest/assisted-by
```

> The portable skill carries the guidance. Native hook enforcement is available
> through the Claude Code and Codex plugins. Support for opencode is on the [roadmap](#roadmap).

## How the hook decides

The guard inspects the `git commit` **command line** on the `Bash` PreToolUse event
in Claude Code and Codex. Codex maps shell and `exec_command` calls to this event.
The guard reads `tool_input.command` and also accepts `tool_input.cmd`. It
only acts when a message is being authored there — `-m` / `--message`, `-F` / `--file`,
`-C` / `--reuse-message`, or `--amend` without `--no-edit`. It blocks (exit 2, reason on
stderr, fed back to the agent) when the command:

- lacks an `Assisted-by:` trailer, or
- adds `Co-Authored-By:` naming Claude or Codex, or
- adds a `Signed-off-by:` naming Claude, Anthropic, Codex, or OpenAI.

A bare `git commit` whose message is composed in the editor isn't visible to the hook —
add the trailer yourself in that case. The guard never blocks on a parse failure or on
commits that don't author a message (`--amend --no-edit`, plain `git commit`).

The guard checks command text only. It does not read files passed with `-F`, reused
messages passed with `-C`, or commands sent later through `write_stdin`. An
`Assisted-by:` string anywhere in the command passes the presence check; the guard
does not validate the final commit message or its trailer format.

## Why

The human submitter takes full responsibility for a contribution and its licensing, so
the DCO chain (`Signed-off-by:`) must stay human. `Assisted-by:` records the assistance
transparently without implying the AI can certify provenance.

## Layout

```
.claude-plugin/
  plugin.json        # plugin manifest (name, version, keywords, skills)
  marketplace.json   # single-plugin marketplace (source ".") for `claude plugin marketplace add`
.codex-plugin/plugin.json  # Codex skill and hook manifest
.agents/plugins/marketplace.json  # Codex marketplace (source "./")
hooks/hooks.json     # registers the PreToolUse Bash guard
hooks/codex.json     # Codex guard with a Windows command override
scripts/attribution-guard.py
skills/git-attribution/SKILL.md
skills.sh.json       # grouping for `npx skills`
```

## Roadmap

- Native hook enforcement for **opencode** (the portable skill already works there).

## License

See [LICENSE](LICENSE). All rights reserved; in particular, the contents may **not** be
used as training, fine-tuning, or evaluation data for machine-learning or AI systems.
