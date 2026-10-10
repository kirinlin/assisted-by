"""Exercise the hook stdin/stderr contract without creating commits."""
import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "scripts" / "attribution-guard.py"


class AttributionGuardTests(unittest.TestCase):
    def run_guard(self, payload):
        return subprocess.run(
            [sys.executable, str(GUARD)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            check=False,
        )

    def test_shell_payloads(self):
        for field in ("command", "cmd"):
            for agent in ("Claude", "Codex"):
                with self.subTest(field=field, agent=agent):
                    denied = self.run_guard({
                        "tool_name": "Bash",
                        "tool_input": {field: 'git commit -m "feat: update"'},
                    })
                    self.assertEqual(denied.returncode, 2)
                    self.assertIn("AGENT_NAME:<model-id>", denied.stderr)
                    self.assertIn("AGENT_NAME:<model-id>/<reasoning-effort>", denied.stderr)
                    self.assertIn("Omit /reasoning-effort if unavailable", denied.stderr)
                    self.assertEqual(denied.stdout, "")
                    allowed = self.run_guard({
                        "tool_name": "Bash",
                        "tool_input": {field: f'git commit -m "feat: update\n\nAssisted-by: {agent}:model/high"'},
                    })
                    self.assertEqual(allowed.returncode, 0)
                    self.assertEqual(allowed.stderr, "")

    def test_skill_attribution_formats_are_allowed(self):
        for trailer in (
            "Codex:gpt-6-astra/medium",
            "Codex:gpt-6.1-sol/high",
            "Codex:gpt-6.1-sol/low",
            "Codex:gpt-6-luna/high",
            "Claude:claude-opus-4-8/high",
            "Codex:gpt-6.1-sol",
            "Claude:claude-opus-4-8",
        ):
            with self.subTest(trailer=trailer):
                result = self.run_guard({"tool_input": {
                    "command": f'git commit -m "fix: update\n\nAssisted-by: {trailer}"',
                }})
                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stderr, "")

    def test_ai_trailers_are_denied(self):
        for trailer in (
            "Co-Authored-By: Codex <bot@example.com>",
            "Co-Authored-By: Claude <bot@example.com>",
            "Signed-off-by: Codex <bot@example.com>",
            "Signed-off-by: OpenAI <bot@example.com>",
            "Signed-off-by: Claude <bot@example.com>",
            "Signed-off-by: Anthropic <bot@example.com>",
            "Claude-Session: private-session",
        ):
            with self.subTest(trailer=trailer):
                result = self.run_guard({"tool_input": {
                    "command": f'git commit -m "feat: update\n\nAssisted-by: Codex:model\n{trailer}"',
                }})
                self.assertEqual(result.returncode, 2)

    def test_human_signoff_is_allowed(self):
        result = self.run_guard({"tool_input": {
            "command": 'git commit -m "feat: update\n\nAssisted-by: Codex:model\nSigned-off-by: Developer <dev@example.com>"',
        }})
        self.assertEqual(result.returncode, 0)

    def test_commands_without_authored_message_are_allowed(self):
        for command in ("git status", "git commit", "git commit --amend --no-edit"):
            with self.subTest(command=command):
                self.assertEqual(self.run_guard({"tool_input": {"command": command}}).returncode, 0)

    def test_message_options_are_checked(self):
        for option in ('--message "update"', '-F message.txt', '-C HEAD', '--amend'):
            with self.subTest(option=option):
                self.assertEqual(self.run_guard({"tool_input": {"command": f"git commit {option}"}}).returncode, 2)

    def test_invalid_payloads_do_not_block(self):
        for payload in (None, [], {}, {"tool_input": []}, {"tool_input": {"command": None}}):
            with self.subTest(payload=payload):
                self.assertEqual(self.run_guard(payload).returncode, 0)
        result = subprocess.run(
            [sys.executable, str(GUARD)], input="invalid JSON", text=True,
            capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0)

    def test_codex_packaging(self):
        manifest = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text())
        config = json.loads((ROOT / manifest["hooks"]).read_text())
        group = config["hooks"]["PreToolUse"][0]
        self.assertEqual(group["matcher"], "^Bash$")
        handler = group["hooks"][0]
        self.assertIn('${PLUGIN_ROOT}/scripts/attribution-guard.py', handler["command"])
        self.assertTrue(handler["commandWindows"].startswith("uv run --no-project python "))
        self.assertTrue((ROOT / manifest["skills"] / "git-attribution" / "SKILL.md").is_file())
        marketplace = json.loads((ROOT / ".agents" / "plugins" / "marketplace.json").read_text())
        entry = marketplace["plugins"][0]
        self.assertEqual(entry["name"], manifest["name"])
        self.assertEqual(entry["source"]["path"], "./")


if __name__ == "__main__":
    unittest.main()
