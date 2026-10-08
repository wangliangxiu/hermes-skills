"""
TapTap Maker Cloud Build Trigger

Usage: python trigger-build.py <project_dir>

Triggers a remote cloud build via MCP for the Maker project at <project_dir>.
Handles Chinese paths via subst S: drive mapping on Windows.

Prerequisites:
  - npx (Node.js) installed
  - Project has been git-committed
  - Project has .maker-mcp/config.json

Output: prints the build result JSON (maker_url with preview link)
"""

import subprocess, json, sys, os, time, threading

def trigger_build(project_dir: str) -> dict:
    """Trigger a Maker cloud build and return the result."""
    
    # Resolve absolute path
    project_dir = os.path.abspath(project_dir)
    
    # On Windows with Chinese paths, use subst drive S:
    subst_drive = "S:"
    if any(ord(c) > 127 for c in project_dir):
        subprocess.run(
            ["cmd.exe", "/c", f"subst {subst_drive} /d 2>nul & subst {subst_drive} {project_dir}"],
            capture_output=True, text=True
        )
        cwd = f"{subst_drive}\\\\"
    else:
        cwd = project_dir
    
    # Read project_id from config
    config_path = os.path.join(project_dir, ".maker-mcp", "config.json")
    if os.path.exists(config_path):
        with open(config_path) as f:
            config = json.load(f)
        project_id = config.get("project_id", "unknown")
    else:
        project_id = "unknown"
    
    # Start MCP server
    proc = subprocess.Popen(
        ["cmd.exe", "/c", "npx.cmd -y @taptap/maker"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        cwd=cwd, text=True, bufsize=0
    )
    
    # Background reader
    received = []
    lock = threading.Lock()
    
    def reader(stream):
        while True:
            line = stream.readline()
            if not line:
                break
            with lock:
                received.append(line.strip())
    
    t = threading.Thread(target=reader, args=(proc.stdout,), daemon=True)
    t.start()
    err_thread = threading.Thread(target=reader, args=(proc.stderr,), daemon=True)
    err_thread.start()
    
    time.sleep(2)
    
    # MCP initialize
    proc.stdin.write(json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "hermes-agent-build-bot", "version": "1.0"}
        }
    }) + "\n")
    proc.stdin.flush()
    time.sleep(3)
    
    # Send initialized notification
    proc.stdin.write(json.dumps({
        "jsonrpc": "2.0", "method": "notifications/initialized", "params": {}
    }) + "\n")
    proc.stdin.flush()
    time.sleep(0.5)
    
    # Call maker_build_current_directory
    proc.stdin.write(json.dumps({
        "jsonrpc": "2.0", "id": 2, "method": "tools/call",
        "params": {
            "name": "maker_build_current_directory",
            "arguments": {
                "target_dir": cwd,
                "entry": "main.lua",
                "scriptsPath": "scripts",
                "timeout_ms": 600000
            }
        }
    }) + "\n")
    proc.stdin.flush()
    
    # Wait for build to finish
    time.sleep(60)
    
    with lock:
        all_responses = list(received)
    
    proc.stdin.close()
    proc.terminate()
    
    # Parse the last JSON result
    for line in reversed(all_responses):
        try:
            data = json.loads(line)
            if "result" in data:
                return data["result"]
        except json.JSONDecodeError:
            continue
    
    return {"raw_responses": all_responses}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python trigger-build.py <project_dir>")
        sys.exit(1)
    
    result = trigger_build(sys.argv[1])
    
    # Extract and print useful info
    if "content" in result:
        for item in result["content"]:
            if item.get("type") == "text":
                print(item["text"])
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))
