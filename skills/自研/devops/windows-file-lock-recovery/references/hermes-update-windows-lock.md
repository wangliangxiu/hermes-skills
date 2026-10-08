# `hermes update` on Windows: venv launcher lock (依赖装不进去)

Verified 2026-09-14, Hermes 0.20.1 → 0.21.2, CN-mirror install (`cnb.cool/hermesagent-cn`).

## Symptom chain

1. `hermes update -y` fetches and swaps code fine, then prints
   `⚠ Could not quarantine hermes.exe (PermissionError: another process is holding it open).`
2. After a long stall it dies with
   `⚠ Git update failed: Command '[..., 'uv.exe', 'pip', 'install', '-e', '.']' returned non-zero exit status 2.`
   and falls back to `→ Falling back to ZIP download...` — it downloads
   `https://github.com/NousResearch/hermes-agent/archive/refs/heads/main.zip` (40 MB+, slow).
3. A direct uv run shows the real error:
   ```
   error: failed to remove file ...\hermes-agent\venv\Lib\site-packages\../../Scripts/hermes.exe:
   另一个程序正在使用此文件，进程无法访问。 (os error 32)
   ```

## Root cause

Any process launched from `venv\Scripts\hermes.exe` holds the image file. Windows refuses
BOTH delete and rename on a running exe (`mv` and PowerShell `Rename-Item` both return
「另一个程序正在使用此文件」), so `uv pip install -e .` cannot replace the console-script stub.
The updater's own quarantine step hits the same wall (its own launcher + any other REPL count).

**Only that one file is blocked** — every other package installs normally. Don't conclude the
venv is broken.

## Working workarounds (all verified)

A. Finish the sync from a process that is NOT that exe — the reliable route:
   ```bash
   cd "$LOCALAPPDATA/hermes/hermes-agent"
   venv/Scripts/python.exe -m hermes_cli.main update -y   # run with all hermes.exe closed
   ```
   `python -m hermes_cli.main <subcommand>` is equivalent to the `hermes` CLI and locks nothing.

B. While Hermes is still running, install only the third-party deps (skips the project
   reinstall, so it never touches the locked stub):
   ```bash
   uv pip install -e ".[all]" --dry-run                              # exact list of what is missing
   uv pip install --python venv/Scripts/python.exe <pkg==ver ...>    # everything except hermes-agent
   ```
   Verified: 33 packages (fastapi, mcp 2.0, snowballstemmer, pillow-heif, cryptography 50, …)
   installed in under a second from cache with the CLI still up. What remains is only the
   project stub / dist-info refresh, done via route (A).

C. One-click repair script for the user — see `references/windows-bat-from-bash.md`.

D. After a successful install, clear the marker Hermes itself would clear:
   `del .update-incomplete`, then verify
   `venv/Scripts/python.exe -c "import importlib.metadata as m; print(m.version('hermes-agent'))"`.

## Markers and retry ceilings (don't burn them)

- A failed dep sync leaves `hermes-agent/.update-incomplete` containing `{"attempts": N}`.
- The next launches run early-recovery BEFORE importing native modules; **3 attempts max**, then
  it stops auto-retrying and only prints the manual command. Launching the CLI "just to check"
  consumes an attempt — and each probe still fails while the launching shim is itself the holder.
- `_venv_core_imports_healthy()` can report **True** while the editable dist-info is stale
  (e.g. 0.19.1 vs tree 0.21.2). In that state `hermes update` prints "Already up to date" and
  does NOT repair deps. Probe it explicitly:
  ```bash
  venv/Scripts/python.exe -c "from hermes_cli.update_cmd import _venv_core_imports_healthy as h; print(h())"
  ```
- The update also restores a second launcher at `AppData/Local/hermes/bin/hermes.exe`; only the
  *running* file is locked, so a launcher in another directory never blocks an install.
- Shallow mirror clone: `merge --ff-only origin/main` cannot fast-forward (no merge base), so the
  updater falls through to `git reset --hard origin/main` — expected, not damage.
  `git status` stays clean afterwards; the version banner comes from the tree
  (`grep -m1 '^version' pyproject.toml`), not from venv dist-info.

## Pitfall: never export a dead proxy into the persistent shell

The terminal tool's shell keeps env vars across calls. `export https_proxy=http://127.0.0.1:17890`
(proxy not actually running) made every later `curl` return `000` AND poisoned the update:
hermes' own downloader ignores the env proxy while `uv` honours it, so the dependency sync failed
while the GitHub ZIP still downloaded happily — a very confusing split. Before blaming the network:
`env | grep -i proxy`, then `unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY`.
On this machine PyPI and api.github.com are directly reachable, and `codeload.github.com` serves
the archive even when `github.com` itself returns nothing.

## Verify the new code actually runs (don't trust the version banner)

```bash
venv/Scripts/python.exe -m hermes_cli.main doctor                            # tool inventory
venv/Scripts/python.exe -m hermes_cli.main chat -q "只回复：更新测试通过"     # real round-trip
```
Both were run after the swap; doctor listed the tool inventory and the chat returned in ~4 s —
that is the proof the swapped-in tree works, not the version string.
