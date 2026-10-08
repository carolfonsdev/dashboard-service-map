"""Funções comuns aos modos de execução."""

import platform
import subprocess
import sys
from datetime import datetime


def log(msg, emoji="·"):
    print(f"  {emoji}  {msg}", flush=True)


def log_ts(msg):
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def erro(msg):
    print(f"\n  ❌  {msg}\n")
    sys.exit(1)


def checar_mac():
    if platform.system() != "Darwin":
        print()
        print("  ⚠️   A instalação como serviço é exclusiva do Mac (launchd).")
        print()
        print("  Em Windows/Linux, rode servidor + watcher com um comando só:")
        print("    python3 instalar_servico.py --rodar --pasta ~/Repos")
        print()
        sys.exit(0)


def launchctl(cmd, plist):
    return subprocess.run(
        ["launchctl", cmd, str(plist)], capture_output=True, text=True
    )


# ════════════════════════════════════════════════════════════════
#  SERVIDOR HTTP  (ex-servidor_http.py)
# ════════════════════════════════════════════════════════════════
