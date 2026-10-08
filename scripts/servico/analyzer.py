"""Descoberta e análise dos repositórios."""

import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from .config import (
    EXT_FONTE, EXTENSOES_CODIGO, EXTENSOES_PROJETO, IGNORAR_DIRS,
    MARCADORES_PROJETO, PADROES_DIRECAO, PADROES_ENDPOINT, PADROES_TESTE,
    PASTAS_TESTE, SINAIS_CONEXAO,
)

# ============================================================
# UTILITÁRIOS
# ============================================================

def tamanho_pasta(caminho: Path) -> int:
    total = 0
    for raiz, dirs, arquivos in os.walk(caminho):
        dirs[:] = [d for d in dirs if d not in IGNORAR_DIRS]
        for f in arquivos:
            try:
                total += (Path(raiz) / f).stat().st_size
            except OSError:
                pass
    return total


def formatar_tamanho(num_bytes: int) -> str:
    for unidade in ["B", "KB", "MB", "GB"]:
        if num_bytes < 1024:
            return f"{num_bytes:.1f} {unidade}"
        num_bytes /= 1024
    return f"{num_bytes:.1f} TB"


def eh_arquivo_teste(caminho_arquivo: Path) -> bool:
    partes = {p.lower() for p in caminho_arquivo.parts}
    if partes & PASTAS_TESTE:
        return True
    nome = caminho_arquivo.name.lower()
    return "test" in nome or "spec" in nome


# ============================================================
# ANÁLISE
# ============================================================

def detectar_tipo(caminho: Path) -> str:
    # Mantém .git como principal indicador de REPOSITÓRIO, mas a
    # tecnologia é determinada pelos arquivos presentes nele.
    for marcador, tipo in MARCADORES_PROJETO.items():
        if (caminho / marcador).is_file():
            return tipo

    try:
        for entrada in caminho.iterdir():
            if entrada.is_file() and entrada.suffix.lower() in EXTENSOES_PROJETO:
                return EXTENSOES_PROJETO[entrada.suffix.lower()]
    except (PermissionError, OSError):
        pass

    return "Desconhecido"


def volume_da_app(caminho: Path) -> dict:
    num_arquivos = num_linhas = num_endpoints = num_testes = 0

    for raiz, dirs, arquivos in os.walk(caminho):
        dirs[:] = [d for d in dirs if d not in IGNORAR_DIRS]

        for f in arquivos:
            caminho_arquivo = Path(raiz) / f

            if caminho_arquivo.suffix not in EXT_FONTE:
                continue

            eh_teste = eh_arquivo_teste(caminho_arquivo)

            try:
                conteudo = caminho_arquivo.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue

            if eh_teste:
                for padrao in PADROES_TESTE:
                    num_testes += len(re.findall(padrao, conteudo))
                continue

            num_arquivos += 1
            num_linhas += conteudo.count("\n") + 1

            for padrao in PADROES_ENDPOINT:
                num_endpoints += len(re.findall(padrao, conteudo))

    return {
        "num_arquivos": num_arquivos,
        "num_linhas": num_linhas,
        "num_endpoints": num_endpoints,
        "num_testes": num_testes,
    }


def detectar_direcoes(caminho: Path) -> str:
    encontrados = []
    tem_endpoint = False

    for raiz, dirs, arquivos in os.walk(caminho):
        dirs[:] = [d for d in dirs if d not in IGNORAR_DIRS]

        for f in arquivos:
            caminho_arquivo = Path(raiz) / f
            if caminho_arquivo.suffix not in EXTENSOES_CODIGO:
                continue

            try:
                conteudo = caminho_arquivo.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue

            for padrao in PADROES_ENDPOINT:
                if re.search(padrao, conteudo):
                    tem_endpoint = True

            for nome_direcao, padroes in PADROES_DIRECAO.items():
                if nome_direcao in encontrados:
                    continue
                for padrao in padroes:
                    if re.search(padrao, conteudo, re.IGNORECASE):
                        encontrados.append(nome_direcao)
                        break

    passos = []
    if tem_endpoint:
        passos.append("recebe requisição REST")

    for consumo in ("consome Kafka", "consome Pub/Sub"):
        if consumo in encontrados:
            passos.append(consumo)

    for meio in (
        "persiste em banco relacional", "persiste no MongoDB",
        "usa cache Redis", "chama API externa (Feign)",
        "chama API externa (RestTemplate)", "chama API externa (WebClient)",
        "chama API externa (Axios)", "envia/lê arquivo (Cloud Storage)",
        "persiste no DynamoDB",
    ):
        if meio in encontrados:
            passos.append(meio)

    for saida in ("publica no Kafka", "publica no Pub/Sub"):
        if saida in encontrados:
            passos.append(saida)

    return " -> ".join(passos)


def detectar_conexoes(caminho: Path) -> str:
    encontrados = set()

    for raiz, dirs, arquivos in os.walk(caminho):
        dirs[:] = [d for d in dirs if d not in IGNORAR_DIRS]

        for f in arquivos:
            if Path(f).suffix not in EXTENSOES_CODIGO:
                continue

            caminho_arquivo = Path(raiz) / f
            try:
                conteudo = caminho_arquivo.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue

            for nome_sinal, padroes in SINAIS_CONEXAO.items():
                if nome_sinal in encontrados:
                    continue
                for padrao in padroes:
                    if re.search(padrao, conteudo, re.IGNORECASE):
                        encontrados.add(nome_sinal)
                        break

    return ", ".join(sorted(encontrados)) if encontrados else ""


def principais_dependencias(caminho: Path, tipo: str, limite: int = 12) -> str:
    if tipo in ("Java/Maven",):
        pom = caminho / "pom.xml"
        if not pom.exists():
            return ""
        try:
            texto = pom.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return ""
        artefatos = re.findall(r"<artifactId>([^<]+)</artifactId>", texto)
        vistos = list(dict.fromkeys(artefatos))  # deduplica mantendo ordem
        return ", ".join(vistos[:limite])

    elif tipo == "Java/Gradle":
        gradle = caminho / "build.gradle"
        if not gradle.exists():
            gradle = caminho / "build.gradle.kts"
        if not gradle.exists():
            return ""
        try:
            texto = gradle.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return ""
        deps = re.findall(r"['\"]([a-zA-Z0-9._-]+:[a-zA-Z0-9._-]+)", texto)
        return ", ".join(deps[:limite])

    elif tipo == "Node.js":
        pkg = caminho / "package.json"
        if not pkg.exists():
            return ""
        try:
            data = json.loads(pkg.read_text(encoding="utf-8", errors="ignore"))
            todas = list(data.get("dependencies", {}).keys()) + list(data.get("devDependencies", {}).keys())
            return ", ".join(todas[:limite])
        except Exception:
            return ""

    elif tipo == "Python":
        req = caminho / "requirements.txt"
        if req.exists():
            try:
                linhas = req.read_text(encoding="utf-8", errors="ignore").splitlines()
                pacotes = []
                for linha in linhas:
                    linha = linha.strip()
                    if not linha or linha.startswith("#"):
                        continue
                    pacote = re.split(r"[=><!~]", linha)[0].strip()
                    if pacote:
                        pacotes.append(pacote)
                return ", ".join(pacotes[:limite])
            except OSError:
                return ""

        pyproject = caminho / "pyproject.toml"
        if pyproject.exists():
            try:
                texto = pyproject.read_text(encoding="utf-8", errors="ignore")
                deps = re.findall(r'["\']([a-zA-Z0-9_.-]+)', texto)
                return ", ".join(deps[:limite])
            except OSError:
                return ""

    elif tipo == "Go":
        gomod = caminho / "go.mod"
        if not gomod.exists():
            return ""
        try:
            texto = gomod.read_text(encoding="utf-8", errors="ignore")
            deps = re.findall(r"^\s+(\S+)\s+v", texto, re.MULTILINE)
            return ", ".join(deps[:limite])
        except OSError:
            return ""

    return ""


def ler_primeiro_paragrafo_readme(caminho: Path) -> str:
    for nome in ["README.md", "readme.md", "README.MD", "Readme.md", "README.rst", "README.txt"]:
        readme = caminho / nome
        if not readme.exists():
            continue
        try:
            texto = readme.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        linhas = [l.strip() for l in texto.splitlines()]
        paragrafo = []
        comecou = False

        for linha in linhas:
            if not linha:
                if comecou:
                    break
                continue
            if linha.startswith("#") or linha.startswith("![") or linha.startswith("[!["):
                continue
            comecou = True
            paragrafo.append(linha)

        if paragrafo:
            return " ".join(paragrafo)[:400]

    return ""


def ler_imagem_base_dockerfile(caminho: Path) -> str:
    for nome in ["Dockerfile", "dockerfile", "Dockerfile.prod"]:
        dockerfile = caminho / nome
        if not dockerfile.exists():
            continue
        try:
            texto = dockerfile.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        froms = re.findall(r"^FROM\s+(\S+)", texto, re.MULTILINE)
        if froms:
            return " -> ".join(froms)
    return ""



# ============================================================
# INFORMAÇÕES EXTRAS POR APP (endpoints, versões, porta, quem chama quem, Kafka, Git)
# ============================================================

def _ler(caminho_arquivo: Path) -> str:
    try:
        return caminho_arquivo.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _arquivos(caminho: Path, sufixos: set):
    for raiz, dirs, arquivos in os.walk(caminho):
        dirs[:] = [d for d in dirs if d not in IGNORAR_DIRS]
        for f in arquivos:
            p = Path(raiz) / f
            if p.suffix in sufixos:
                yield p


def _juntar(prefixo: str, sub: str) -> str:
    return ("/" + prefixo.strip("/") + "/" + sub.strip("/")).replace("//", "/").rstrip("/") or "/"


def listar_endpoints(caminho: Path, limite: int = 200) -> str:
    """Ex.: 'GET /reservas/{id} | POST /reservas'. Spring: prefixo da classe + método. Node: router/app."""
    achados = []
    re_metodo = re.compile(r"@(Get|Post|Put|Delete|Patch)Mapping\s*(?:\(([^)]*)\))?")
    re_prefixo = re.compile(r"@RequestMapping\s*\(([^)]*)\)")
    re_string = re.compile(r'"([^"]*)"')
    re_node = re.compile(r"""\b(?:router|app)\.(get|post|put|delete|patch)\(\s*['"`]([^'"`]+)['"`]""")
    for arq in _arquivos(caminho, {".java", ".kt", ".js", ".ts"}):
        if eh_arquivo_teste(arq):
            continue
        txt = _ler(arq)
        if arq.suffix in (".java", ".kt"):
            if "Mapping" not in txt:
                continue
            m_cls = re.search(r"\b(?:class|interface)\s+\w+", txt)
            topo = txt[:m_cls.start()] if m_cls else ""
            m_pre = re_prefixo.search(topo)
            prefixo = ""
            if m_pre:
                sm = re_string.search(m_pre.group(1))
                prefixo = sm.group(1) if sm else ""
            for m in re_metodo.finditer(txt[m_cls.start():] if m_cls else txt):
                sm = re_string.search(m.group(2) or "")
                achados.append(f"{m.group(1).upper()} {_juntar(prefixo, sm.group(1) if sm else '')}")
        else:
            for m in re_node.finditer(txt):
                achados.append(f"{m.group(1).upper()} {m.group(2)}")
    unicos = list(dict.fromkeys(achados))
    return " | ".join(unicos[:limite])


def detectar_runtime(caminho: Path) -> str:
    """Ex.: 'Java 21 · Spring Boot 3.2.1' ou 'Node 20'."""
    partes = []
    pom = caminho / "pom.xml"
    if pom.exists():
        t = _ler(pom)
        j = re.search(r"<(?:java\.version|maven\.compiler\.release|maven\.compiler\.source|release)>\s*(\d+(?:\.\d+)?)", t)
        if j:
            partes.append(f"Java {j.group(1)}")
        b = re.search(r"<artifactId>spring-boot-starter-parent</artifactId>\s*<version>([^<$]+)</version>", t)
        if b:
            partes.append(f"Spring Boot {b.group(1).strip()}")
    for g in ("build.gradle", "build.gradle.kts"):
        if (caminho / g).exists():
            t = _ler(caminho / g)
            b = re.search(r"org\.springframework\.boot['\"]?\)?\s*version\s*['\"]([^'\"]+)", t)
            if b:
                partes.append(f"Spring Boot {b.group(1)}")
            j = re.search(r"JavaVersion\.VERSION_(\d+)|languageVersion.*?(\d+)", t)
            if j:
                partes.insert(0, f"Java {j.group(1) or j.group(2)}")
    pj = caminho / "package.json"
    if pj.exists():
        m = re.search(r'"node"\s*:\s*"([^"]+)"', _ler(pj))
        if m:
            partes.append(f"Node {m.group(1)}")
    nvm = caminho / ".nvmrc"
    if nvm.exists() and not any(p.startswith("Node") for p in partes):
        partes.append("Node " + _ler(nvm).strip().lstrip("v"))
    return " · ".join(partes)


def detectar_porta(caminho: Path) -> str:
    for arq in _arquivos(caminho, {".properties", ".yml", ".yaml"}):
        if not arq.name.startswith("application") or eh_arquivo_teste(arq):
            continue
        t = _ler(arq)
        m = re.search(r"(?m)^\s*server\.port\s*[=:]\s*([^\s#]+)", t)
        if not m:
            m = re.search(r"(?m)^server:\s*\n(?:[ \t]+.*\n)*?[ \t]+port:\s*([^\s#]+)", t)
        if m:
            return m.group(1)
    df = caminho / "Dockerfile"
    if df.exists():
        m = re.search(r"(?mi)^\s*EXPOSE\s+(\d+)", _ler(df))
        if m:
            return m.group(1)
    return ""


def detectar_chama_apps(caminho: Path) -> str:
    """Nomes dos @FeignClient — o dashboard cruza com os nomes dos repos para mostrar quem chama quem."""
    nomes = []
    for arq in _arquivos(caminho, {".java", ".kt"}):
        if eh_arquivo_teste(arq):
            continue
        for m in re.finditer(r"@FeignClient\s*\(([^)]*)\)", _ler(arq)):
            args = m.group(1)
            n = re.search(r'\b(?:name|value)\s*=\s*"([^"]+)"', args) or re.match(r'\s*"([^"]+)"', args)
            if n:
                nomes.append(n.group(1))
    return ", ".join(dict.fromkeys(nomes))


def detectar_topicos_kafka(caminho: Path) -> str:
    consome, publica = [], []
    for arq in _arquivos(caminho, {".java", ".kt", ".js", ".ts"}):
        if eh_arquivo_teste(arq):
            continue
        t = _ler(arq)
        if "afka" not in t:
            continue
        for m in re.finditer(r"@KafkaListener\s*\(([^)]*)\)", t):
            consome += re.findall(r'"([^"]+)"', m.group(1).split("groupId")[0]) if "topics" in m.group(1) else []
        publica += re.findall(r'(?:kafkaTemplate|KafkaTemplate)\w*\.send\(\s*"([^"]+)"', t)
    partes = []
    if consome:
        partes.append("consome: " + ", ".join(dict.fromkeys(consome)))
    if publica:
        partes.append("publica: " + ", ".join(dict.fromkeys(publica)))
    return " | ".join(partes)


def info_git(caminho: Path) -> dict:
    def git(*args):
        try:
            r = subprocess.run(["git", "-C", str(caminho), *args], capture_output=True, text=True, timeout=5)
            return r.stdout.strip() if r.returncode == 0 else ""
        except (OSError, subprocess.SubprocessError):
            return ""
    if not (caminho / ".git").exists():
        return {"Git_branch": "", "Git_ultimo_commit": "", "Git_url": ""}
    ult = git("log", "-1", "--date=format:%d/%m/%Y", "--format=%cd · %an · %s").replace('"', "'")
    url = git("config", "--get", "remote.origin.url")
    m = re.match(r"git@([^:]+):(.+?)(?:\.git)?$", url)
    if m:
        url = f"https://{m.group(1)}/{m.group(2)}"
    url = re.sub(r"^(https?://)[^@/]+@", r"\1", url)   # nunca guardar token na URL
    url = re.sub(r"\.git$", "", url)
    return {"Git_branch": git("rev-parse", "--abbrev-ref", "HEAD"), "Git_ultimo_commit": ult, "Git_url": url}


def extras_do_repo(caminho: Path) -> dict:
    return {
        "Endpoints_lista":   listar_endpoints(caminho),
        "Runtime":           detectar_runtime(caminho),
        "Porta":             detectar_porta(caminho),
        "Chama_apps":        detectar_chama_apps(caminho),
        "Topicos_kafka":     detectar_topicos_kafka(caminho),
        **info_git(caminho),
    }


def analisar_repo(caminho: Path) -> dict:
    tipo = detectar_tipo(caminho)
    volume = volume_da_app(caminho)
    return {
        "Nome":                    caminho.name,
        "Tipo":                    tipo,
        "Num_arquivos_producao":   volume["num_arquivos"],
        "Num_linhas_codigo":       volume["num_linhas"],
        "Num_endpoints":           volume["num_endpoints"],
        "Num_testes":              volume["num_testes"],
        "Fluxo_simples":           detectar_direcoes(caminho),
        "Tamanho_disco":           formatar_tamanho(tamanho_pasta(caminho)),
        "README_resumo":           ler_primeiro_paragrafo_readme(caminho),
        "Dockerfile_base":         ler_imagem_base_dockerfile(caminho),
        "Conexoes_detectadas":     detectar_conexoes(caminho),
        "Principais_dependencias": principais_dependencias(caminho, tipo),
        "Descricao_simples":       "",
        "Analogia":                "",
        **extras_do_repo(caminho),
    }


# ============================================================
# DESCOBERTA DE REPOSITÓRIOS
# ============================================================

# Marcadores de projeto. São usados SOMENTE quando a pasta ainda
    """
    Detecta a raiz real de um repositório Git.

    `.git` normalmente é um diretório, mas pode ser um arquivo em
    worktrees/submódulos, por isso aceitamos os dois formatos.
    """
    git = caminho / ".git"
    return git.is_dir() or git.is_file()


def eh_git_repo(caminho: Path) -> bool:
    """Detecta a raiz real de um repositório Git."""
    git = caminho / ".git"
    return git.is_dir() or git.is_file()


def marcador_projeto(caminho: Path) -> Optional[str]:
    """
    Retorna a tecnologia indicada pelos marcadores da própria pasta.

    A ordem é determinística e privilegia arquivos mais específicos.
    Não procura dentro das subpastas: a decisão pertence à pasta
    atualmente visitada.
    """
    # Primeiro os marcadores com nome exato.
    for marcador, tipo in MARCADORES_PROJETO.items():
        if (caminho / marcador).is_file():
            return tipo

    # Depois marcadores por extensão (principalmente Terraform).
    try:
        for entrada in caminho.iterdir():
            if not entrada.is_file() or entrada.is_symlink():
                continue
            tipo = EXTENSOES_PROJETO.get(entrada.suffix.lower())
            if tipo:
                return tipo
    except (PermissionError, OSError):
        pass

    return None


def eh_repo(caminho: Path) -> bool:
    """
    Compatibilidade com chamadas antigas: uma pasta é projeto se tiver
    .git ou um marcador de projeto conhecido.
    """
    return eh_git_repo(caminho) or marcador_projeto(caminho) is not None


def descobrir_repos(base: Path, depth: Optional[int], includes: list, excludes: set) -> list:
    """
    Descobre projetos em qualquer profundidade, sem limite por padrão.

    REGRA FUNDAMENTAL:
      1. .git tem prioridade absoluta.
      2. Ao encontrar .git, registra a pasta e NÃO entra nela.
      3. Sem .git, um marcador de projeto pode registrar a pasta e
         interromper a descida, evitando que src/modules/dev/prod sejam
         tratados como projetos independentes.
      4. Sem marcador, continua descendo até o fim da árvore.

    Isso permite encontrar:
        Repos/equipe/projeto/.../servico

    mesmo que o projeto esteja 5, 10 ou 20 níveis abaixo.
    """
    base = Path(base).expanduser().resolve()
    repos = []
    vistos = set()

    if not base.exists() or not base.is_dir():
        return repos

    def adicionar(caminho: Path):
        chave = str(caminho.resolve())
        if chave not in vistos:
            vistos.add(chave)
            repos.append(caminho)

    # Caso a própria pasta informada já seja um repositório/projeto.
    if eh_git_repo(base):
        adicionar(base)
        return sorted(repos, key=lambda p: str(p).lower())

    # --include continua funcionando como filtro do primeiro nível.
    # Quando usado, só as pastas nomeadas diretamente dentro da base
    # são pontos iniciais da busca.
    try:
        iniciais = sorted(
            (p for p in base.iterdir() if p.is_dir() and not p.is_symlink()),
            key=lambda p: p.name.lower(),
        )
    except (PermissionError, OSError):
        return repos

    pilha = []
    for entry in iniciais:
        if entry.name.startswith(".") or entry.name in IGNORAR_DIRS:
            continue
        if entry.name in excludes:
            continue
        if includes and entry.name not in includes:
            continue
        pilha.append((entry, 1))

    while pilha:
        pasta, nivel = pilha.pop()

        try:
            # .git SEMPRE ganha de qualquer marcador.
            if eh_git_repo(pasta):
                adicionar(pasta)
                continue

            # Se não há Git, um marcador identifica a pasta como projeto.
            # Não descemos depois disso.
            if marcador_projeto(pasta) is not None:
                adicionar(pasta)
                continue

            if depth is not None and nivel >= depth:
                continue

            try:
                filhos = sorted(
                    (p for p in pasta.iterdir() if p.is_dir() and not p.is_symlink()),
                    key=lambda p: p.name.lower(),
                    reverse=True,
                )
            except (PermissionError, OSError):
                continue

            for filho in filhos:
                if filho.name.startswith("."):
                    continue
                if filho.name in IGNORAR_DIRS:
                    continue
                if filho.name in excludes:
                    continue
                pilha.append((filho, nivel + 1))

        except (PermissionError, OSError):
            continue

    return sorted(repos, key=lambda p: str(p).lower())


COLUNAS = [
    "Nome", "Tipo", "Num_arquivos_producao", "Num_linhas_codigo",
    "Num_endpoints", "Num_testes", "Fluxo_simples", "Tamanho_disco",
    "README_resumo", "Dockerfile_base", "Conexoes_detectadas",
    "Principais_dependencias", "Descricao_simples", "Analogia",
    "Endpoints_lista", "Runtime", "Porta", "Chama_apps", "Topicos_kafka",
    "Git_branch", "Git_ultimo_commit", "Git_url",
]

def gerar_dados_js(resultados: list, pasta: Path):
    """
    Gera dados.js na mesma pasta do CSV.
    O HTML importa esse arquivo — funciona offline, sem servidor.
    """
    import json
    from datetime import datetime

    dados = {
        "gerado_em": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "total": len(resultados),
        "servicos": resultados,
    }

    js = (
        f"// Gerado automaticamente pelo GloboAds Service Map em {dados['gerado_em']}\n"
        f"// NAO edite manualmente — rode o script novamente para atualizar.\n"
        f"window.GLOBOADS_SERVICE_MAP_DADOS = {json.dumps(dados, ensure_ascii=False, indent=2)};\n"
    )

    saida_js = pasta / "dados.js"
    fd, nome_tmp = tempfile.mkstemp(
        prefix=f".{saida_js.name}.", suffix=".tmp", dir=saida_js.parent
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as arquivo:
            arquivo.write(js)
            arquivo.flush()
            os.fsync(arquivo.fileno())
        os.replace(nome_tmp, saida_js)
    finally:
        try:
            os.unlink(nome_tmp)
        except FileNotFoundError:
            pass
    print(f"dados.js gerado:     {saida_js.resolve()}")
