"""Instalação e manutenção dos serviços launchd."""

import subprocess
import sys
from pathlib import Path
from xml.sax.saxutils import escape

from .common import erro, launchctl, log
from .config import (
    ARQUIVO, DASHBOARD, LABEL_SERVIDOR, LABEL_WATCHER, LAUNCH_AGENTS,
    LOG_DIR, PLIST_SERVIDOR, PLIST_WATCHER,
)
from .watcher import resolver_pasta

# ════════════════════════════════════════════════════════════════

def gerar_plist(label: str, argumentos: list, nome_log: str, throttle: int) -> str:
    itens = "\n".join(f"        <string>{escape(str(a))}</string>" for a in argumentos)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{label}</string>

    <key>ProgramArguments</key>
    <array>
{itens}
    </array>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>{escape(str(LOG_DIR))}/{nome_log}.log</string>
    <key>StandardErrorPath</key>
    <string>{escape(str(LOG_DIR))}/{nome_log}-erro.log</string>

    <key>ThrottleInterval</key>
    <integer>{throttle}</integer>
</dict>
</plist>"""


def registrar(plist: Path, conteudo: str, nome: str):
    plist.write_text(conteudo)
    launchctl("unload", plist)
    r = launchctl("load", plist)
    if r.returncode != 0:
        erro(f"Erro ao registrar {nome}:\n       {r.stderr}")


def instalar(args):

    print()
    print("  GloboAds Service Map · Instalador Mac")
    print()
    print("  Serão instalados dois serviços (ambos rodam ESTE arquivo):")
    print("  🌐 Servidor HTTP  — serve o dashboard (sempre ativo)")
    print("  👁  Watcher        — monitora repos e atualiza dados")
    print()

    pasta = resolver_pasta(args)
    python3 = sys.executable

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LAUNCH_AGENTS.mkdir(parents=True, exist_ok=True)

    args_srv = [python3, ARQUIVO, "--servidor", "--port", str(args.port)]
    args_wat = [python3, ARQUIVO, "--watcher", "--pasta", str(pasta),
                "--interval", str(args.interval), "--output", str(args.output)]
    if args.depth is not None:
        args_wat += ["--depth", str(args.depth)]
    for p in args.include:
        args_wat += ["--include", p]
    for p in args.exclude:
        args_wat += ["--exclude", p]

    registrar(PLIST_SERVIDOR, gerar_plist(LABEL_SERVIDOR, args_srv, "servidor", 5),
              "servidor HTTP")
    registrar(PLIST_WATCHER, gerar_plist(LABEL_WATCHER, args_wat, "watcher", 10),
              "watcher")

    print()
    log("Instalado com sucesso!", "🎉")
    log(f"Pasta monitorada : {pasta}", "📁")
    log(f"Dashboard        : http://localhost:{args.port}/{DASHBOARD}", "🌐")
    log(f"Logs watcher     : {LOG_DIR}/watcher.log", "📄")
    log(f"Logs servidor    : {LOG_DIR}/servidor.log", "📄")
    print()
    log("Servidor HTTP e Watcher iniciam automaticamente com o Mac.", "✅")
    log("O dashboard fica disponível mesmo quando o Watcher estiver offline.", "💡")
    print()
    print("  Comandos úteis:")
    print(f"    Ver logs do watcher:  tail -f {LOG_DIR}/watcher.log")
    print(f"    Ver logs do servidor: tail -f {LOG_DIR}/servidor.log")
    print( "    Parar só o watcher:   python3 instalar_servico.py --desinstalar")
    print( "    Remover tudo:         python3 instalar_servico.py --desinstalar-tudo")
    print()


def desinstalar(tudo: bool = False):
    """--desinstalar remove só o watcher; --desinstalar-tudo remove os dois."""
    removidos = []

    if tudo:
        if PLIST_SERVIDOR.exists():
            launchctl("unload", PLIST_SERVIDOR)
            PLIST_SERVIDOR.unlink()
            removidos.append("servidor HTTP")
        else:
            log("Servidor HTTP não estava instalado.")

    if PLIST_WATCHER.exists():
        launchctl("unload", PLIST_WATCHER)
        PLIST_WATCHER.unlink()
        removidos.append("watcher")
    else:
        log("Watcher não estava instalado.")

    print()
    if removidos:
        log(f"Removido: {', '.join(removidos)}", "✅")
    else:
        log("Nenhum serviço encontrado para remover.")

    if not tudo:
        print()
        log("O servidor HTTP continua rodando — dashboard ainda acessível em:", "💡")
        log(f"http://localhost:8080/{DASHBOARD}", "🌐")
        log("Os dados do último snapshot foram preservados.", "💾")
        print()
        log("Para remover também o servidor HTTP:")
        log("python3 instalar_servico.py --desinstalar-tudo")
    print()


def status():
    print()
    print("  GloboAds Service Map · Status")
    print()
    for label, plist, nome in [
        (LABEL_SERVIDOR, PLIST_SERVIDOR, "Servidor HTTP"),
        (LABEL_WATCHER, PLIST_WATCHER, "Watcher"),
    ]:
        if not plist.exists():
            log(f"{nome:14}  → NÃO instalado", "⚪")
            continue
        r = subprocess.run(["launchctl", "list", label], capture_output=True, text=True)
        if label in r.stdout:
            log(f"{nome:14}  → RODANDO ✅", "🟢")
        else:
            log(f"{nome:14}  → instalado mas PARADO ⚠️", "🟡")
    print()
    log(f"Plist servidor : {PLIST_SERVIDOR}", "📄")
    log(f"Plist watcher  : {PLIST_WATCHER}", "📄")
    log(f"Logs           : {LOG_DIR}/", "📋")
    print()


# ════════════════════════════════════════════════════════════════
#  CLI
# ════════════════════════════════════════════════════════════════
