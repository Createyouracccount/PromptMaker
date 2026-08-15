# PromptTailor

> Model-aware prompt rewriting for Claude Code. Write a rough request — get it rewritten the way your current Claude model works best.

[한국어 README](README.ko.md)

## Why

Claude Fable 5, Opus 5, Sonnet 5, and Haiku respond best to *different* prompt styles — Fable wants goals and constraints in prose (no step lists), Opus over-verifies if you tell it to double-check, Haiku wants small numbered steps. PromptTailor keeps these differences as data ([model profiles](prompt_tailor/profiles/)), detects which model you're running, and rewrites your rough request to match — also routing by task intent (fix / build / research / refactor / docs).

Your input language is preserved: English in → English out, Korean in → Korean out.

## Example

```
$ prompt-tailor "fix the login bug asap, users keep getting logged out" --model fable-5
```

> Users are repeatedly logging out unexpectedly. Before fixing, investigate: exact
> reproduction steps (when and under what conditions does this happen?), when this
> started, relevant error logs or console messages, and the login/session management
> code structure.
>
> Once you've identified the reproduction path and root cause, apply the minimum fix
> to prevent unintended logouts. Scope: session and login logic only — do not modify
> other features.
>
> Validation: confirm the issue no longer reproduces through direct testing, or verify
> that related tests pass.

Notice what happened: vague urgency ("asap") became an investigation directive, a scope boundary, and a validation criterion — and nothing was invented. Unknowns become investigation steps; any added specifics are tagged as assumptions.

## Install

**As a Claude Code plugin (recommended):**

```
/plugin marketplace add Createyouracccount/PromptTailor
/plugin install prompt-tailor@prompt-tailor
```

This gives you the `/pm` command with no path setup.

**As a CLI / MCP server:**

```bash
git clone https://github.com/Createyouracccount/PromptTailor.git
cd PromptTailor
pip install .            # installs `prompt-tailor` and `prompt-tailor-mcp`
```

Requirements: Python 3.10+, the `claude` CLI installed and logged in (no separate API key). Verified on macOS/Linux; Windows untested.

## Usage

```bash
prompt-tailor "rough request" --model fable-5    # rewrite for a target model
prompt-tailor "rough request" --json             # JSON output
prompt-tailor "rough request" --concise          # faster, condensed meta-prompt
```

**Inside Claude Code** — `/pm rough request`: rewrites for your session's detected model, shows a one-line change summary, then executes the rewritten request. In auto mode, add the permission rule printed by `claude-code/install.sh` so prompts containing risky-looking words (e.g. "docker prune") aren't false-positive blocked — the backend only rewrites text.

**Hook auto mode (opt-in)** — rewrite every prompt automatically via a `UserPromptSubmit` hook. Run `bash claude-code/install.sh` for the settings snippet. Escape hatch: include `#raw` in a prompt to pass it through untouched. Prompts under 6 tokens or over 800 chars are skipped; if a rewrite doesn't finish within 28s it fails open (your original prompt goes through).

**Cursor / any MCP client** — a built-in stdio MCP server exposes `refine_prompt(raw, target_model, concise)`:

```jsonc
// ~/.cursor/mcp.json
{ "mcpServers": { "prompt-tailor": { "command": "prompt-tailor-mcp" } } }
```

```bash
claude mcp add prompt-tailor -- prompt-tailor-mcp   # register in Claude Code
```

## How it's validated

Every design decision in this repo is backed by measured experiments (blind pairwise LLM judging, ledgered in [LOOP_LOG.md](LOOP_LOG.md)):

- Golden set of 20 rough prompts: **20/20 judged better than the original** (clarity 5.0, fidelity 4.8, actionability 5.0) — [EVAL.md](EVAL.md)
- Model profiles produce structurally different rewrites: 5/5
- Intent routing beat profile-only rewriting 4–1–1 in pairwise comparison
- Latency: ~15–30s per rewrite via `claude -p` (the price of needing no API key)

Honest caveats live in [EVAL.md](EVAL.md): small n, single LLM judge, "better prompt" ≠ proven higher task success rate.

## Development

```bash
python3 -m unittest discover tests   # 37 offline tests, no LLM calls
python3 eval/run_eval.py             # golden-set evaluation (spawns claude)
```

Project docs (Korean): [PLAN.md](PLAN.md) · [ARCHITECTURE.md](ARCHITECTURE.md) · [RESEARCH.md](RESEARCH.md) · gate criteria in [GATES.md](GATES.md).

## License

[MIT](LICENSE)
