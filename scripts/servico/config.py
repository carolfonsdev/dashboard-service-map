"""Configurações e padrões usados pela aplicação."""

from pathlib import Path

# ════════════════════════════════════════════════════════════════

PASTA = Path(__file__).resolve().parent.parent.parent
ARQUIVO = PASTA / "scripts" / "instalar_servico.py"
STATUS = PASTA / "status.json"

LABEL_SERVIDOR = "com.globoads.servicemap.servidor"
LABEL_WATCHER = "com.globoads.servicemap.watcher"

LAUNCH_AGENTS = Path.home() / "Library" / "LaunchAgents"
PLIST_SERVIDOR = LAUNCH_AGENTS / f"{LABEL_SERVIDOR}.plist"
PLIST_WATCHER = LAUNCH_AGENTS / f"{LABEL_WATCHER}.plist"
LOG_DIR = Path.home() / "Library" / "Logs" / "globoads-service-map"

DASHBOARD = "dashboard/index.html"

EXTENSOES = {
    ".java", ".kt", ".ts", ".js", ".mjs", ".cjs", ".py", ".go", ".rb", ".rs",
    ".php", ".tf", ".scala", ".swift", ".cs", ".c", ".cpp", ".h", ".hpp",
    ".xml", ".gradle", ".kts", ".json", ".yml", ".yaml", ".properties", ".proto",
}
MARCADORES = {
    "pom.xml", "build.gradle", "build.gradle.kts", "package.json",
    "requirements.txt", "pyproject.toml", "setup.py", "go.mod", "Gemfile",
    "Cargo.toml", "composer.json", "Dockerfile", "docker-compose.yml",
    "docker-compose.yaml", "Chart.yaml", "ansible.cfg", "Jenkinsfile",
}
IGNORAR = {
    ".git", "node_modules", "target", "build", "dist", ".idea", ".venv",
    "venv", "__pycache__", ".gradle", "out", ".next", ".nuxt", "coverage",
}

DEBOUNCE = 5  # segundos mínimos entre análises

IGNORAR_DIRS = {
    ".git", "node_modules", "target", "build", "dist",
    ".idea", ".venv", "venv", "__pycache__", ".gradle",
    "out", ".next", ".nuxt", "coverage", ".nyc_output",
}

EXT_FONTE = {".java", ".ts", ".js", ".py", ".go", ".kt"}

EXTENSOES_CODIGO = {
    ".java", ".ts", ".js", ".py", ".yml", ".yaml",
    ".properties", ".xml", ".go", ".kt", ".toml",
}

# ════════════════════════════════════════════════════════════════
#  UTILITÁRIOS
# ════════════════════════════════════════════════════════════════
# Pastas/nomes que indicam arquivo de teste
PASTAS_TESTE = {"test", "tests", "__tests__", "spec", "specs"}

# ============================================================
# PADRÕES DE DETECÇÃO
# ============================================================

PADROES_ENDPOINT = [
    r"@GetMapping", r"@PostMapping", r"@PutMapping",
    r"@DeleteMapping", r"@PatchMapping", r"@RequestMapping",
    r"router\.(get|post|put|delete|patch)\(",
    r"app\.(get|post|put|delete|patch)\(",
    r"@app\.(get|post|put|delete|patch)\(",
    r"@router\.(get|post|put|delete|patch)\(",     # FastAPI
    r"@(Get|Post|Put|Delete|Patch)\(",             # NestJS
]

PADROES_TESTE = [
    r"@Test\b",               # JUnit
    r"\bit\(\s*['\"]",        # Jest/Mocha
    r"\btest\(\s*['\"]",      # Jest
    r"\bdescribe\(\s*['\"]",  # Jest describe
    r"\bdef\s+test_\w+",      # Pytest
    r"@ParameterizedTest",    # JUnit 5
]

PADROES_DIRECAO = {
    "consome Kafka":                    [r"@KafkaListener"],
    "publica no Kafka":                 [r"KafkaTemplate"],
    "consome Pub/Sub":                  [r"@ServiceActivator.*[Pp]ub[Ss]ub", r"PubSubInboundChannelAdapter"],
    "publica no Pub/Sub":               [r"PubSubTemplate", r"\.publish\("],
    "chama API externa (Feign)":        [r"@FeignClient"],
    "chama API externa (RestTemplate)": [r"RestTemplate"],
    "chama API externa (WebClient)":    [r"WebClient"],
    "chama API externa (Axios)":        [r"axios\.(get|post|put|delete|patch)\("],
    "persiste em banco relacional":     [r"@Entity", r"jdbc:"],
    "persiste no MongoDB":              [r"MongoRepository", r"mongoose"],
    "usa cache Redis":                  [r"RedisTemplate", r"@Cacheable", r"createClient\(\)", r"ioredis"],
    "envia/lê arquivo (Cloud Storage)": [r"google\.cloud\.storage", r"@google-cloud/storage"],
    "persiste no DynamoDB":             [r"DynamoDB", r"dynamodb"],
}

SINAIS_CONEXAO = {
    "Kafka":                       [r"kafka", r"KafkaTemplate", r"@KafkaListener"],
    "Pub/Sub (GCP)":               [r"pubsub", r"PubSub", r"com\.google\.cloud\.pubsub"],
    "Feign Client (REST síncrono)":[r"@FeignClient", r"FeignClient"],
    "RestTemplate (REST síncrono)":[r"RestTemplate"],
    "WebClient (REST reativo)":    [r"WebClient"],
    "Axios (REST)":                [r"axios"],
    "gRPC":                        [r"grpc", r"\.proto\b"],
    "Redis":                       [r"redis", r"Redis", r"ioredis"],
    "BigQuery":                    [r"bigquery", r"BigQuery"],
    "Cloud Storage (GCS)":         [r"google\.cloud\.storage", r"@google-cloud/storage"],
    "Banco relacional (JDBC/JPA)": [r"jdbc:", r"@Entity", r"spring-boot-starter-data-jpa", r"sequelize", r"typeorm"],
    "MongoDB":                     [r"mongodb", r"MongoRepository", r"mongoose"],
    "Elasticsearch":               [r"elasticsearch", r"ElasticsearchRepository"],
    "RabbitMQ":                    [r"rabbitmq", r"RabbitTemplate", r"@RabbitListener"],
    "DynamoDB":                    [r"DynamoDB", r"dynamodb"],
}

# não foi identificada como um repositório Git.
MARCADORES_PROJETO = {
    # JVM
    "pom.xml": "Java/Maven",
    "build.gradle": "Java/Gradle",
    "build.gradle.kts": "Java/Gradle",

    # JavaScript / TypeScript
    "package.json": "Node.js",

    # Python
    "pyproject.toml": "Python",
    "requirements.txt": "Python",
    "setup.py": "Python",

    # Go / Rust / Ruby / PHP
    "go.mod": "Go",
    "Cargo.toml": "Rust",
    "Gemfile": "Ruby",
    "composer.json": "PHP",

    # Infra / DevOps
    "Dockerfile": "Docker",
    "docker-compose.yml": "Docker Compose",
    "docker-compose.yaml": "Docker Compose",
    "Chart.yaml": "Helm",
    "ansible.cfg": "Ansible",
    "Jenkinsfile": "Jenkins",
}

# Arquivos que podem aparecer em qualquer lugar do projeto.
# Terraform é intencionalmente baseado em extensão: uma pasta com
# pelo menos um .tf é suficiente para ser considerada um projeto
# quando não existe um .git acima dela.
EXTENSOES_PROJETO = {
    ".tf": "Terraform",
}
