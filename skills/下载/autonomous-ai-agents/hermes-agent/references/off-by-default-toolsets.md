# Off-By-Default Toolsets: MoA & RL

Two advanced toolsets exist in the Hermes codebase but are **disabled by default**:
`moa` (Mixture of Agents) and `rl` (Reinforcement Learning / Tinker-Atropos).
They must be explicitly enabled via `hermes tools enable <name>` followed by `/reset`.

---

## MoA (Mixture of Agents)

**Status:** ✅ Active, maintained, fully functional.

**What it does:** Queries N advisor models in parallel, then an aggregator model
synthesizes their responses into a single answer. Configurable presets in
`config.yaml` under `moa.presets.*`.

**Enabling:**

```bash
hermes tools enable moa       # register the toolset
# then /reset to apply
```

**Config keys (in config.yaml):**

```yaml
moa:
  default_preset: "default"
  active_preset: ""
  save_traces: false          # set to true to log full turns to JSONL
  trace_dir: ""               # override output directory
  presets:
    default:
      reference_models:
        - provider: "openai-codex"
          model: "gpt-5.5"
        - provider: "openrouter"
          model: "deepseek/deepseek-v4-pro"
      aggregator:
        provider: "openrouter"
        model: "anthropic/claude-opus-4.8"
        max_tokens: 4096
      enabled: true
```

Auxiliary timeouts for MoA reference calls (in config.yaml):

```yaml
auxiliary:
  moa_reference:
    provider: "auto"
    timeout: 900        # 15 minutes — advisors can be slow
  moa_aggregator:
    provider: "auto"
    timeout: 900
```

**Pitfalls:**

- **Needs >=2 distinct provider API keys** to make a useful preset.
- **~5-10x cost** per MoA turn (N advisors + 1 aggregator).
- **Requires `/reset`** after enabling the toolset.
- **Default preset** ships hardcoded to `openai-codex` + `openrouter` model IDs
  that may not exist. Always review before use.
- **User_turn cadence** (since PR #57591): MoA advisors run once per user turn
  by default.
- **Prompt caching** applied to advisor and aggregator calls (PR #57675).
- **Slow advisor delays all** — fan-out waits for the slowest.

**Slash command:** `/moa` in-session toggles MoA for current turn. Set
`moa.active_preset` in config.yaml to default all turns to MoA.

---

## RL (Reinforcement Learning / Tinker-Atropos)

**Status:** ❌ **Removed from main branch.** Full feature
(`tools/rl_training_tool.py`, `environments/` directory, `tinker-atropos`
submodule, `rl_cli.py`) deleted in commit `5af672c75` (PR #26106, May 2026).

**Code recovery:** Last intact version at `5af672c75^` under
`tools/rl_training_tool.py` (1396 lines). Submodule pointed to
`github.com/nousresearch/tinker-atropos`.

**What it was:** Client-side toolset connecting to Tinker API (Nous Research's
internal RL training service) for GRPO/PPO model fine-tuning.

**Requirements (when it existed):**
- `TINKER_API_KEY` — Tinker remote service
- `WANDB_API_KEY` — Weights & Biases
- `tinker-atropos` git submodule (environments/, configs/, scripts/)
- vLLM or SGLang inference server running locally
- GPU cluster / Slurm for actual training

**Removal reasons:**
1. External dependency on Tinker API
2. ~50 files including environments, benchmarks, tool call parsers
3. Tight coupling to Nous Research's internal training infra
4. Cannot run on personal hardware without GPU cluster

**Attempt to revive (July 2026):** Recovering `tools/rl_training_tool.py`
compiles but:
- `tinker-atropos` submodule removed from `.gitmodules`
- `environments/` directory (43 files) gone — no training targets
- Still needs Tinker API + GPU infra to actually run

**Conclusion:** Not usable on a personal laptop. Alternatives: OpenRouter
fine-tuning API, local LoRA via `unsloth`/`axolotl`, or HuggingFace TRL.
