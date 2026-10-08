#!/usr/bin/env python3
"""Ponto de entrada do GloboAds Service Map.

A implementação foi dividida em módulos dentro de ``scripts/servico``.
Este arquivo mantém o comando original e reexporta as funções públicas para
preservar compatibilidade com chamadas existentes.
"""

from servico.analyzer import *  # noqa: F401,F403
from servico.common import *  # noqa: F401,F403
from servico.config import *  # noqa: F401,F403
from servico.installer import *  # noqa: F401,F403
from servico.server import *  # noqa: F401,F403
from servico.watcher import *  # noqa: F401,F403
from servico.cli import main


if __name__ == "__main__":
    main()
