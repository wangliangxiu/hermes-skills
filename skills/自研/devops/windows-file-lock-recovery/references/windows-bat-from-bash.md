# Authoring AND testing a user-facing .bat from git-bash (Chinese Windows)

Deliverable pattern: a 一键 `.bat` on the desktop that repairs/updates something the user
cannot type himself. It must be generated, encoded, and self-tested from the bash tool.

## Encoding and line endings (the part that actually breaks)

- Write the `.bat` as **GBK (cp936) with CRLF**.
  - UTF-8 content renders as mojibake in the console.
  - LF-only endings make cmd mis-parse the file — the symptom is
    `'ho' 不是内部或外部命令`, i.e. `@echo off` got cut in half.
- Control both from Python:
  ```python
  io.open(path, "w", encoding="gbk", newline="\r\n").write(text)
  ```
- Put `chcp 936 >nul` at the top (default console codepage on Chinese Windows).
  Do NOT pair `chcp 65001` with GBK bytes.

## Reading the output back

cmd's redirect writes GBK, so decode explicitly:
`open(out, "rb").read().decode("gbk", errors="replace")`.

## Pitfalls

- `cmd //c "<path>"` from MSYS bash frequently loses its arguments (cmd just prints its banner and
  exits). Reliable form:
  `powershell -NoProfile -Command "cmd /c 'C:\native\path\x.bat'"`
- Inside the .bat prefer **`findstr`** over `find`: an inherited bash-style PATH lets MSYS's
  `find.exe` shadow Windows `find`, which then parses `/I` as a filename
  (`find: '/I': No such file or directory`) and silently sends a "is X running?" guard down the
  *not running* branch — the dangerous direction.
- Process guard that works:
  ```bat
  tasklist /FI "IMAGENAME eq hermes.exe" /NH 2>nul | findstr /I "hermes.exe" >nul
  if not errorlevel 1 ( ...refuse and explain... )
  ```
- Unattended testing: generate a copy with `pause` → `rem pause`, otherwise the test hangs on the
  keypress. Test the guard by generating a second copy with the guard lines stripped, so you
  exercise the work path too — expect the environment-specific failure there and confirm the
  `:fail` branch prints correctly, then hand the real file to the user.
- Chinese filenames/paths in the .bat are fine (the user double-clicks it); the quoting failures
  above are bash→cmd issues, not the filename.
- Keep the script self-diagnosing: check the marker/lock file it is supposed to clear afterwards,
  print the resolved version, and `pause` at the end so the user can read or screenshot it.

## Layout that worked

`[1/4] guard → [2/4] the exact repair command → [3/4] clear markers + verify → [4/4] result`,
with a `:fail` label that echoes the manual command to paste, then `pause` on both exits.
