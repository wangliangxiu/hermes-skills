# Chinese Windows Path Workarounds (Hermes Agent)

## Context

On Windows 11 with a Chinese username (e.g. 使用者), git-bash's `$HOME` environment variable resolves to garbage bytes (`/c/Users/������`). This breaks:

- `ls ~/some/path` — resolves to nonexistent directory
- `find /c/Users/使用者/...` — Chinese chars in the MSYS2 path may fail
- Any shell command using `$HOME`, `~/`, or the user's full name in the path
- `python -c "..."` with inline scripts that reference `os.path.expanduser('~')` — works in some contexts but quoting hell with nested quotes

## The Reliable Workaround: write_file + python full-path

### Step 1: Write a script file to disk

```python
# NEVER use inline python -c with complex scripts — nested quotes WILL break
write_file("C:\\Users\\使用者\\Desktop\\_task_script.py", '''
import os
# os.path.expanduser('~') WORKS in full .py files (not in -c inline)
home = os.path.expanduser("~")
# ... your code here
''')
```

### Step 2: Run with FULL Windows path

```python
# Use the full Windows path wrapped in double quotes
terminal(f'python "C:\\Users\\使用者\\Desktop\\_task_script.py"')
```

This works because `python "C:\full\path\script.py"` is:
1. Passed to cmd.exe (not git-bash path resolver)
2. Windows native path handling handles Chinese characters correctly
3. No git-bash `$HOME` resolution involved

### Step 3: Clean up temporary scripts

```python
import os
os.remove("C:\\Users\\使用者\\Desktop\\_task_script.py")
```

## Alternative: Using `execute_code` (Preferred When Possible)

The `execute_code` tool runs Python directly without going through git-bash's terminal at all — it uses the Hermes agent's own Python process. This avoids ALL path resolution issues:

```python
from hermes_tools import terminal, write_file, read_file, search_files

# This runs in the agent's own Python — paths work normally
home = os.path.expanduser("~")
skills_dir = os.path.join(home, "AppData", "Local", "hermes", "skills")
files = os.listdir(skills_dir)

# Terminal commands still need workaround
r = terminal(f'python "C:\\Users\\使用者\\Desktop\\_helper.py"')
```

## Patterns That DON'T Work

| Attempt | Result |
|---------|--------|
| `ls ~/AppData/Local/...` | Fails — `~` resolves to garbage |
| `ls /c/Users/使用者/...` | Unreliable — MSYS2 path encoding |
| `cmd /c "echo %USERPROFILE%"` | Chinese chars garbled in output |
| `powershell -Command "dir $env:USERPROFILE\..."` | Fails — `$env:USERPROFILE` contains garbled Chinese chars when captured by git-bash |
| `python -c "import os; os.listdir('...')"` | Works for simple commands but nested quotes/strings break |

## When to Use Each Approach

1. **Simple single-file ops (write_file, read_file, search_files, patch):** Use the tool directly with `C:\Users\使用者\...` full path — no workaround needed.
2. **Python logic + terminal (script generation):** Use `write_file` to desktop + `terminal(f'python "full_path"')`.
3. **Complex multi-step Python processing:** Use `execute_code` (it's the agent's own Python — no terminal involvement).
4. **Only when you MUST run bash commands that reference user paths:** Use the full Windows path in the command string, wrapped in double quotes for safety.
