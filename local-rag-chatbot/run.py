#!/usr/bin/env python3
"""
One-command runner for Local RAG Chatbot.
Starts the FastAPI server accessible from localhost and other devices on the local network.
"""

import sys
import time
import socket
import webbrowser
import threading
import uvicorn
import urllib.request
import json
from pathlib import Path

# Fix Windows console UTF-8 output encoding
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

BANNER = r"""
========================================================================
   ____  _             _         ____            _      _             _     ___ 
  / ___|| |_ _   _  __| |_   _  | __ ) _   _  __| |  __| |_   _      / \   |_ _|
  \___ \| __| | | |/ _` | | | | |  _ \| | | |/ _` | / _` | | | |    / _ \   | | 
   ___) | |_| |_| | (_| | |_| | | |_) | |_| | (_| || (_| | |_| |   / ___ \  | | 
  |____/ \__|\__,_|\__,_|\__, | |____/ \__,_|\__,_(_)__,_|\__, |  /_/   \_\|___|
                         |___/                            |___/                 
========================================================================
     Collaborative AI Study Partner & Shared Document Vault for Everyone
"""

def get_local_ip() -> str:
    """Detect the machine's primary local network IP address."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"

def get_public_ip() -> str:
    """Detect the machine's external public WAN IP address."""
    try:
        req = urllib.request.Request("https://api.ipify.org?format=json", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=2.5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("ip", "")
    except Exception:
        return ""

def check_ollama(url="http://localhost:11434"):
    try:
        req = urllib.request.Request(f"{url}/api/tags", headers={"User-Agent": "StudyBuddyAI"})
        with urllib.request.urlopen(req, timeout=2.0) as res:
            if res.status == 200:
                data = json.loads(res.read().decode("utf-8"))
                models = [m.get("name") for m in data.get("models", [])]
                return True, models
    except Exception:
        pass
    return False, []

def open_browser(url: str, delay: float = 1.2):
    time.sleep(delay)
    try:
        webbrowser.open(url)
    except Exception:
        pass

def main():
    print(BANNER)
    host = "0.0.0.0"
    port = 8000
    local_ip = get_local_ip()

    print("[*] Checking local AI services...")
    ollama_ok, models = check_ollama()
    if ollama_ok:
        print("  [+] Local Ollama detected at http://localhost:11434")
        if models:
            print(f"      Available models: {', '.join(models)}")
        else:
            print("      [!] No models currently installed. Pull one with: ollama pull qwen2.5:3b")
    else:
        print("  [!] Ollama is not detected at http://localhost:11434.")
        print("      Make sure Ollama is running ('ollama serve') to enable AI chat.")

    public_ip = get_public_ip()
    print(f"\n[+] StudyBuddy AI is live & ready to collaborate!")
    print(f"  > On this PC (Localhost):   http://localhost:{port}")
    print(f"  > Share on Local Wi-Fi:     http://{local_ip}:{port}")
    if public_ip:
        print(f"  > Share Worldwide (Public): http://{public_ip}:{port}")
        print(f"                              (Note: Forward Port 8000 on your router to {local_ip})")
    print(f"  > Instant Public Tunnel:    ssh -p 443 -R0:localhost:{port} a.pinggy.io")
    print("                              (Generates free public HTTPS link with zero router setup)")
    print("    Press Ctrl+C to terminate\n")

    # Launch browser locally
    browser_thread = threading.Thread(target=open_browser, args=(f"http://localhost:{port}", 1.2), daemon=True)
    browser_thread.start()

    # Run Uvicorn binding to 0.0.0.0 so all interfaces can access
    uvicorn.run(
        "backend.app:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()
