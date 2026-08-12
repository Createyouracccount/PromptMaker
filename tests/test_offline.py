"""Offline unit tests — no `claude` calls, no network.

Run: python3 -m unittest discover tests -v
"""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from promptmaker.detect import (  # noqa: E402
    _model_from_settings,
    _model_from_transcript,
    detect_model,
    normalize_model,
)
from promptmaker.engine import (  # noqa: E402
    build_meta_prompt,
    parse_json_output,
    resolve_profile,
)


def _load_pm_hook():
    """pm_hook.py lives in a hyphenated dir (claude-code/hooks) — load by path."""
    path = ROOT / "claude-code" / "hooks" / "pm_hook.py"
    spec = importlib.util.spec_from_file_location("pm_hook", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


pm_hook = _load_pm_hook()


class TestParseJsonOutput(unittest.TestCase):
    def test_plain_json(self):
        self.assertEqual(parse_json_output('{"a": 1}'), {"a": 1})

    def test_fenced_json(self):
        text = 'result:\n```json\n{"intent": "fix"}\n```\ndone'
        self.assertEqual(parse_json_output(text), {"intent": "fix"})

    def test_json_with_surrounding_text(self):
        self.assertEqual(parse_json_output('note {"a": "b"} trailing'), {"a": "b"})

    def test_no_json_raises(self):
        with self.assertRaises(ValueError):
            parse_json_output("no json here")


class TestResolveProfile(unittest.TestCase):
    def test_aliases(self):
        self.assertEqual(resolve_profile("fable"), "fable-5")
        self.assertEqual(resolve_profile("claude-opus-5"), "opus-5")
        self.assertEqual(resolve_profile("HAIKU-4-5"), "haiku-4-5")

    def test_unknown_raises(self):
        with self.assertRaises(ValueError):
            resolve_profile("gpt-4")


class TestBuildMetaPrompt(unittest.TestCase):
    def test_full_contains_raw_and_rules(self):
        meta = build_meta_prompt("로그인 버그 고쳐줘", "fable-5")
        self.assertIn("로그인 버그 고쳐줘", meta)
        self.assertIn("[가정", meta)

    def test_concise_is_much_shorter(self):
        raw = "로그인 버그 고쳐줘"
        full = build_meta_prompt(raw, "fable-5")
        concise = build_meta_prompt(raw, "fable-5", concise=True)
        self.assertIn(raw, concise)
        # Latency gate relies on the condensed meta staying small (LOOP_LOG R7).
        self.assertLess(len(concise), 700)
        self.assertLess(len(concise), len(full) / 3)

    def test_concise_exists_for_all_profiles(self):
        for stem in ("fable-5", "opus-5", "sonnet-5", "haiku-4-5"):
            meta = build_meta_prompt("x" * 20, stem, concise=True)
            self.assertIn(stem, meta)


class TestRewriteRetry(unittest.TestCase):
    """Retry loop must treat timeouts as attempt failures, not crash through."""

    def _patch_call_claude(self, side_effects):
        import promptmaker.engine as engine
        calls = {"n": 0}

        def fake(prompt, model, timeout=180):
            effect = side_effects[min(calls["n"], len(side_effects) - 1)]
            calls["n"] += 1
            if isinstance(effect, Exception):
                raise effect
            return effect

        self._orig = engine.call_claude
        engine.call_claude = fake
        self.addCleanup(lambda: setattr(engine, "call_claude", self._orig))
        return calls

    def test_timeout_is_retried(self):
        import subprocess as sp

        from promptmaker.engine import rewrite

        ok = '{"intent": "fix", "rewritten_prompt": "다시 쓴 프롬프트", "changes": ["c"]}'
        calls = self._patch_call_claude([sp.TimeoutExpired(cmd="claude", timeout=1), ok])
        result = rewrite("로그인 버그 고쳐줘", "fable-5", retries=1)
        self.assertEqual(calls["n"], 2)
        self.assertEqual(result.rewritten_prompt, "다시 쓴 프롬프트")

    def test_exhausted_retries_raise_runtime_error(self):
        import subprocess as sp

        from promptmaker.engine import rewrite

        self._patch_call_claude([sp.TimeoutExpired(cmd="claude", timeout=1)])
        with self.assertRaises(RuntimeError):
            rewrite("로그인 버그 고쳐줘", "fable-5", retries=1)


class TestNormalizeModel(unittest.TestCase):
    def test_strips_suffix(self):
        self.assertEqual(normalize_model("claude-fable-5[1m]"), "fable-5")

    def test_families(self):
        self.assertEqual(normalize_model("mythos"), "fable-5")
        self.assertEqual(normalize_model("claude-opus-5"), "opus-5")
        self.assertEqual(normalize_model("claude-sonnet-5"), "sonnet-5")
        self.assertEqual(normalize_model("claude-haiku-4-5-20251001"), "haiku-4-5")

    def test_unknown_and_empty(self):
        self.assertIsNone(normalize_model("gpt-4"))
        self.assertIsNone(normalize_model(None))
        self.assertIsNone(normalize_model(""))


class TestDetection(unittest.TestCase):
    def test_transcript_last_assistant_wins(self):
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as f:
            f.write(json.dumps({"type": "assistant", "message": {"model": "claude-opus-5"}}) + "\n")
            f.write("not json\n")
            f.write(json.dumps({"type": "user", "message": {}}) + "\n")
            f.write(json.dumps({"type": "assistant", "message": {"model": "claude-sonnet-5"}}) + "\n")
            path = f.name
        self.assertEqual(_model_from_transcript(path), "claude-sonnet-5")

    def test_transcript_missing_file(self):
        self.assertIsNone(_model_from_transcript("/nonexistent/path.jsonl"))
        self.assertIsNone(_model_from_transcript(None))

    def test_settings_local_priority(self):
        with tempfile.TemporaryDirectory() as cwd:
            claude_dir = Path(cwd) / ".claude"
            claude_dir.mkdir()
            (claude_dir / "settings.json").write_text('{"model": "claude-opus-5"}')
            (claude_dir / "settings.local.json").write_text('{"model": "claude-haiku-4-5"}')
            self.assertEqual(_model_from_settings(cwd), "claude-haiku-4-5")

    def test_detect_model_transcript_beats_settings(self):
        with tempfile.TemporaryDirectory() as cwd:
            claude_dir = Path(cwd) / ".claude"
            claude_dir.mkdir()
            (claude_dir / "settings.json").write_text('{"model": "claude-opus-5"}')
            transcript = Path(cwd) / "t.jsonl"
            transcript.write_text(
                json.dumps({"type": "assistant", "message": {"model": "claude-sonnet-5"}}) + "\n"
            )
            got = detect_model({"transcript_path": str(transcript), "cwd": cwd})
            self.assertEqual(got, "sonnet-5")


class TestHookSkipRules(unittest.TestCase):
    def test_slash_command(self):
        self.assertEqual(pm_hook.should_skip("/help me"), "slash-command")

    def test_raw_tag(self):
        self.assertEqual(pm_hook.should_skip("#raw 그대로 보내줘 이 프롬프트를 절대 바꾸지 마라"), "raw-tag")
        self.assertEqual(pm_hook.should_skip("앞말 #raw 그대로 보내줘 절대 바꾸지 말고 진행해라"), "raw-tag")

    def test_rawdata_is_not_raw_tag(self):
        # "#rawdata ..." must not match the opt-out tag (measured false positive, R5)
        self.assertNotEqual(
            pm_hook.should_skip("#rawdata 처리하는 코드 만들어줘 데이터 파이프라인으로 구성해서"),
            "raw-tag",
        )

    def test_too_short(self):
        self.assertEqual(pm_hook.should_skip("짧음"), "too-short")
        self.assertEqual(pm_hook.should_skip("hi there"), "too-short")

    def test_seven_token_target_prompt_not_skipped(self):
        # "배포 자동화 하고싶어 도와줘" = ~7 tokens; was skipped under the old
        # <10 threshold — must pass through after the approved amendment (<6).
        self.assertIsNone(pm_hook.should_skip("배포 자동화 하고싶어 도와줘"))

    def test_already_detailed(self):
        self.assertEqual(pm_hook.should_skip("가" * 801), "already-detailed")

    def test_normal_prompt_not_skipped(self):
        self.assertIsNone(pm_hook.should_skip("로그인 버그 고쳐줘 재현 방법은 잘 모르겠는데 자꾸 세션이 끊겨"))


class TestEstimateTokens(unittest.TestCase):
    def test_korean_uses_half_chars(self):
        text = "가나다라마바사아자차"  # 10 Korean chars -> ~5 tokens
        self.assertEqual(pm_hook.estimate_tokens(text), 5)

    def test_english_uses_quarter_chars(self):
        text = "abcdefgh" * 5  # 40 ASCII chars, one word -> 10
        self.assertEqual(pm_hook.estimate_tokens(text), 10)

    def test_word_count_floor(self):
        self.assertGreaterEqual(pm_hook.estimate_tokens("a b c d e f g h i j k l"), 12)


if __name__ == "__main__":
    unittest.main()
