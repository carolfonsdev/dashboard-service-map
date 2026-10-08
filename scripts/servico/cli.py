"""Ponto de entrada e modos de execução da aplicação."""

import argparse
import threading

from .common import checar_mac
from .installer import desinstalar, instalar, status
from .server import rodar_servidor
from .watcher import resolver_pasta, rodar_tudo, rodar_watcher


def parse_args():
    ap = argparse.ArgumentParser(
        description="GloboAds Service Map — instalador, servidor e watcher em um só arquivo.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    # ações
    ap.add_argument("--desinstalar", action="store_true",
                    help="Remove só o Watcher (servidor HTTP continua rodando)")
    ap.add_argument("--desinstalar-tudo", action="store_true",
                    help="Remove o Watcher E o servidor HTTP")
    ap.add_argument("--status", action="store_true",
                    help="Mostra o status dos dois serviços")
    ap.add_argument("--rodar", action="store_true",
                    help="Roda servidor + watcher neste terminal, sem instalar (qualquer SO)")
    ap.add_argument("--servidor", action="store_true",
                    help="Roda só o servidor HTTP (modo usado pelo launchd)")
    ap.add_argument("--watcher", action="store_true",
                    help="Roda só o watcher (modo usado pelo launchd)")
    # opções
    ap.add_argument("--pasta", metavar="CAMINHO",
                    help="Pasta de repos. Se omitido, pergunta interativamente.")
    ap.add_argument("--port", type=int, default=8080, metavar="N",
                    help="Porta do servidor HTTP (padrão: 8080)")
    ap.add_argument("--interval", type=int, default=30, metavar="SEGUNDOS",
                    help="Intervalo de verificação do watcher (padrão: 30s)")
    ap.add_argument("--depth", type=int, default=None,
                    help="Limita a profundidade da busca (padrão: todas as subpastas)")
    ap.add_argument("--include", action="append", default=[])
    ap.add_argument("--exclude", action="append", default=[])
    ap.add_argument("--output", default="dashboard/js/repos_analise.csv")
    return ap.parse_args()


def main():
    args = parse_args()

    # modos de execução (funcionam em qualquer SO)
    if args.servidor:
        rodar_servidor(args.port)
        return
    if args.watcher:
        rodar_watcher(resolver_pasta(args), args.interval, args)
        return
    if args.rodar:
        rodar_tudo(args)
        return

    # instalação / manutenção (só Mac)
    checar_mac()
    if args.status:
        status()
    elif args.desinstalar_tudo:
        desinstalar(tudo=True)
    elif args.desinstalar:
        desinstalar(tudo=False)
    else:
        instalar(args)

