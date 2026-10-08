# GloboAds Service Map

Dashboard local para analisar os repositórios do GloboAds e visualizar serviços, endpoints, integrações, fluxo de dados, runtime e informações do Git.

## Estrutura

```text
globoads-service-map/
├── README.md
├── dashboard/
│   ├── index.html
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── app.js
│       └── dados.js
└── scripts/
    └── instalar_servico.py
```

## Instalação e execução

### macOS

No macOS, o instalador configura o servidor HTTP e o watcher como serviços do sistema. Eles iniciam automaticamente com o Mac.

```bash
cd ~/Documents/globoads-service-map
python3 scripts/instalar_servico.py
```

O instalador pergunta qual é a pasta dos repositórios.

Para manutenção:

```bash
python3 scripts/instalar_servico.py --status
python3 scripts/instalar_servico.py --desinstalar
python3 scripts/instalar_servico.py --desinstalar-tudo
```

### Linux

No Linux, o script não instala serviço automático. Para executar o servidor e o watcher juntos no terminal:

```bash
cd ~/globoads-service-map
python3 scripts/instalar_servico.py --rodar --pasta ~/Repos
```

Para parar, use `Ctrl+C` no terminal onde o processo está rodando. O último snapshot continua salvo.

### Windows

No Windows, o script não instala serviço automático. No PowerShell:

```powershell
cd C:\Users\voce\globoads-service-map
python scripts\instalar_servico.py --rodar --pasta "C:\Repos"
```

Para parar, use `Ctrl+C` no PowerShell onde o processo está rodando. O último snapshot continua salvo.

### Dashboard e verificação

Com o servidor rodando, o dashboard fica em:

```text
http://localhost:8080/dashboard/
```

No Linux/macOS:

```bash
curl http://localhost:8080/ping
curl http://localhost:8080/status.json
```

No Windows PowerShell:

```powershell
Invoke-RestMethod http://localhost:8080/ping
Invoke-RestMethod http://localhost:8080/status.json
```

## Dashboard

```text
http://localhost:8080/dashboard/
```
x
O watcher verifica a pasta monitorada periodicamente e atualiza o CSV e o
snapshot offline após criações, alterações ou remoções de arquivos e
diretórios. As publicações são atômicas, então o dashboard não lê um arquivo
incompleto durante uma análise.
