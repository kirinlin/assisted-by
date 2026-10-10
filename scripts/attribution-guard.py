#!/usr/bin/env python3
"""PreToolUse guard: enforce Linux-kernel AI attribution on git commits.

Reads a Claude Code or Codex PreToolUse payload on stdin. If the command creates a
commit message, require an `Assisted-by:` trailer and forbid the AI adding a
`Signed-off-by:` (DCO is human-only), the old `Co-Authored-By: Claude` line,
or a `Claude-Session:` line (not part of kernel policy, and useless in the
commit). Blocks by exiting 2 with the reason on stderr, which the agent
feeds back to the model so it can rewrite the commit.

For Codex, use the model identifier string from the session configuration.
For Claude, use the exact model ID. Include reasoning effort when known. Omit the effort suffix when unavailable. The command-only
guard cannot determine the session configuration, so it does not require it.

Ref: https://docs.kernel.org/process/coding-assistants.html#attribution
"""
import json
import re
import sys


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0  # never block on a parse failure

    if not isinstance(payload, dict):
        return 0
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return 0
    # Codex normalizes shell calls to Bash/command. Also accept raw exec input.
    cmd = tool_input.get("command", tool_input.get("cmd", ""))
    if not isinstance(cmd, str):
        return 0
    if "git commit" not in cmd:
        return 0

    # Commits that don't author a new message (no -m / -F / -C and not amending
    # the message) carry no message to check.
    creates_message = bool(re.search(r"-m\b|--message|-F\b|--file|-C\b|--reuse-message", cmd))
    amends = "--amend" in cmd and "--no-edit" not in cmd
    if not (creates_message or amends):
        return 0

    problems = []
    if "Assisted-by:" not in cmd:
        problems.append(
            "missing `Assisted-by:` trailer; for Codex, use "
            "`Assisted-by: Codex:<model identifier string>/<reasoning-effort>`; "
            "for Claude, use `Assisted-by: Claude:<model-id>/<reasoning-effort>` "
            "when the reasoning effort is known"
        )
    if re.search(r"Co-Authored-By:\s*(Claude|Codex)\b", cmd, re.IGNORECASE):
        problems.append(
            "remove the AI `Co-Authored-By:` line — kernel policy uses "
            "`Assisted-by:` instead"
        )
    if re.search(r"Signed-off-by:.*(claude|anthropic|codex|openai)", cmd, re.IGNORECASE):
        problems.append(
            "AI must NOT add a Signed-off-by line — only the human developer "
            "can certify the DCO"
        )
    if re.search(r"Claude-Session:", cmd, re.IGNORECASE):
        problems.append(
            "remove the `Claude-Session:` line — it's not part of kernel "
            "attribution policy and is useless in the commit"
        )

    if problems:
        sys.stderr.write(
            "Commit blocked by git-attribution guard (kernel attribution policy):\n"
            + "\n".join(f"  - {p}" for p in problems)
            + "\n\nFor Codex and Claude, use:\n"
            "  Assisted-by: Codex:<model identifier string>/<reasoning-effort>\n"
            "  Assisted-by: Claude:<model-id>/<reasoning-effort>\n"
            "Use the model and effort from the session or contributing agent's "
            "configuration. These examples are not defaults:\n"
            "  Assisted-by: Codex:gpt-6-astra/medium\n"
            "  Assisted-by: Codex:gpt-6.1-sol/high\n"
            "  Assisted-by: Codex:gpt-6.1-sol/low\n"
            "  Assisted-by: Codex:gpt-6-luna/high\n"
            "  Assisted-by: Claude:claude-opus-4-8/high\n"
            "Omit /reasoning-effort if unavailable. Use the exact model identifier string for Codex or model ID for Claude when "
            "known; otherwise use the most specific known model label. Do not "
            "invent model or effort details. Add one trailer for each distinct "
            "agent/model/effort combination that contributed. Let the human add "
            "their own Signed-off-by if they want one.\n"
        )
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
