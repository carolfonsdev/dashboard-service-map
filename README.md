# GloboAds Service Map

Dashboard local para analisar os repositórios do GloboAds e visualizar serviços, endpoints, integrações, fluxo de dados, runtime e informações do Git.

O Service Map percorre a pasta de repositórios de forma recursiva, entrando em subpastas e subpastas sem limite fixo de profundidade, até identificar a raiz de um projeto.

## Estrutura

```text
globoads-service-map/
├── README.md
│
├── dashboard/
│   ├── index.html
│   │
│   ├── css/
│   │   ├── style.css
│   │   └── modules/
│   │       ├── cards.css
│   │       ├── details-content.css
│   │       ├── details.css
│   │       ├── foundation.css
│   │       ├── header.css
│   │       ├── infra.css
│   │       ├── server-panel.css
│   │       └── toolbar.css
│   │
│   └── js/
│       ├── app.js
│       ├── dados.js
│       ├── repos_analise.csv
│       │
│       └── modules/
│           ├── bootstrap.js
│           ├── cards.js
│           ├── core.js
│           ├── data.js
│           ├── filters.js
│           ├── panels.js
│           ├── server-panel.js
│           └── service-details.js
│
└── scripts/
    ├── instalar_servico.py
    │
    └── servico/
        ├── __init__.py
        ├── analyzer.py
        ├── cli.py
        ├── common.py
        ├── config.py
        ├── installer.py
        ├── server.py
        └── watcher.py
```

Os arquivos dentro de `dashboard/css/modules/`, `dashboard/js/modules/` e `scripts/servico/` são módulos internos da ferramenta.

No uso normal, o principal arquivo executado pelo usuário é:

```text
scripts/instalar_servico.py
```

---

## Como o Service Map encontra os projetos

O Service Map percorre a pasta dos repositórios de forma recursiva.

Não existe uma profundidade fixa de pastas.

Por exemplo:

```text
Repos/
└── equipe/
    └── sistemas/
        └── projetos/
            └── backend/
                └── meu-projeto/
                    ├── .git/
                    ├── src/
                    └── pom.xml
```

O analisador continua entrando nas subpastas até encontrar um indicador de projeto.

### Repositórios Git

O principal indicador utilizado é a pasta:

```text
.git/
```

Quando o analisador encontra `.git`, aquela pasta é considerada a raiz do repositório.

Depois disso, ele não continua procurando novos projetos dentro daquela árvore.

Isso evita que pastas internas como:

```text
src/
dev/
stg/
prod/
modules/
```

sejam identificadas como projetos separados.

### Projetos sem `.git`

Quando não existe `.git`, o analisador também consegue identificar projetos através de arquivos característicos.

Alguns exemplos:

```text
pom.xml                  → Java / Maven
build.gradle             → Java / Gradle
build.gradle.kts         → Java / Gradle
package.json             → Node.js
pyproject.toml           → Python
requirements.txt         → Python
setup.py                 → Python
go.mod                   → Go
Cargo.toml               → Rust
Gemfile                  → Ruby
composer.json            → PHP
Dockerfile               → Docker
docker-compose.yml       → Docker
docker-compose.yaml      → Docker
Chart.yaml               → Helm
ansible.cfg              → Ansible
Jenkinsfile              → Jenkins
*.tf                     → Terraform
```

Se a tecnologia não for reconhecida, o projeto ainda pode aparecer no dashboard como:

```text
Desconhecido
```

O objetivo é primeiro encontrar a raiz do projeto e depois identificar sua tecnologia.

---

## Instalação e execução

### macOS

No macOS, o instalador configura o servidor HTTP e o watcher como serviços do sistema utilizando `launchd`.

Eles podem iniciar automaticamente com o Mac, sem a necessidade de manter um terminal aberto.

Entre na pasta do projeto:

```bash
cd ~/Documents/globoads-service-map
```

Execute:

```bash
python3 scripts/instalar_servico.py
```

O instalador solicitará a pasta onde estão os repositórios.

Exemplo:

```text
~/Documents/Repos
```

Depois da instalação, o dashboard estará disponível em:

```text
http://localhost:8080/dashboard/
```

### Status

Para verificar o estado do serviço:

```bash
python3 scripts/instalar_servico.py --status
```

### Remover somente o watcher

```bash
python3 scripts/instalar_servico.py --desinstalar
```

### Remover tudo

```bash
python3 scripts/instalar_servico.py --desinstalar-tudo
```

### Logs do watcher

```bash
tail -f ~/Library/Logs/globoads-service-map/watcher.log
```

### Logs do servidor

```bash
tail -f ~/Library/Logs/globoads-service-map/servidor.log
```

---

## Linux

No Linux, o script não instala um serviço automático do sistema.

Para executar o servidor e o watcher juntos no terminal:

```bash
cd ~/globoads-service-map
python3 scripts/instalar_servico.py --rodar --pasta ~/Repos
```

O processo permanecerá rodando no terminal.

Para parar:

```text
Ctrl+C
```

O último snapshot válido continua disponível no dashboard.

---

## Windows

No Windows, o script não instala um serviço automático do sistema.

Abra o PowerShell e execute:

```powershell
cd C:\Users\usuario\globoads-service-map
python scripts\instalar_servico.py --rodar --pasta "C:\Repos"
```

Para parar:

```text
Ctrl+C
```

O último snapshot válido continua disponível no dashboard.

---

## Dashboard

Com o servidor em execução, acesse:

```text
http://localhost:8080/dashboard/
```

O dashboard apresenta os projetos encontrados pelo analisador e suas informações.

---

## Atualização dos dados

O watcher verifica periodicamente a pasta monitorada.

Quando identifica alterações, como:

- criação de arquivos;
- alteração de arquivos;
- remoção de arquivos;
- criação de diretórios;
- remoção de diretórios;

ele inicia uma nova análise.

O fluxo é:

```text
Pasta dos repositórios
        ↓
Watcher
        ↓
Detecta alterações
        ↓
Analyzer
        ↓
Encontra e analisa os projetos
        ↓
repos_analise.csv
        ↓
dados.js
        ↓
Servidor HTTP
        ↓
Dashboard
```

Durante uma nova análise, o dashboard mantém o último resultado válido.

Quando a análise termina, os novos dados são publicados e o dashboard pode carregá-los.

As publicações são feitas de forma atômica para evitar que o dashboard leia um arquivo incompleto durante uma atualização.

---

## Verificação do servidor

### macOS / Linux

Para verificar se o servidor está funcionando:

```bash
curl http://localhost:8080/ping
```

Para consultar o status do watcher:

```bash
curl http://localhost:8080/status.json
```

### Windows PowerShell

```powershell
Invoke-RestMethod http://localhost:8080/ping
```

```powershell
Invoke-RestMethod http://localhost:8080/status.json
```

---

## Porta

Por padrão, o servidor utiliza a porta:

```text
8080
```

O dashboard fica disponível em:

```text
http://localhost:8080/dashboard/
```

Se a porta estiver ocupada, o servidor pode utilizar outra porta disponível conforme a configuração da ferramenta.

No macOS/Linux, para verificar quem está utilizando a porta 8080:

```bash
lsof -i :8080
```

---

## Resumo dos componentes

```text
Analyzer
→ encontra e analisa os projetos

Watcher
→ monitora alterações e dispara novas análises

repos_analise.csv
→ armazena os dados analisados

dados.js
→ mantém um snapshot dos dados

Servidor HTTP
→ disponibiliza o dashboard e os arquivos localmente

Dashboard
→ apresenta os resultados visualmente

Installer
→ configura e inicia os componentes da ferramenta
```

---

## Checklist

```text
[ ] Clonei/copiei o projeto globoads-service-map
[ ] Informei a pasta dos meus repositórios
[ ] Iniciei o Service Map
[ ] Acessei o dashboard
[ ] O dashboard carregou
[ ] Os repositórios foram encontrados
[ ] O Watcher está funcionando
[ ] Os dados estão sendo atualizados
```

> **O GloboAds Service Map encontra projetos independentemente da profundidade das pastas e reconhece diferentes tipos de aplicações, serviços e infraestrutura.**