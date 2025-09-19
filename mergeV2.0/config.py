import os
from pathlib import Path

# ============================================
# Diretórios principais
# ============================================

BASE_DIR = Path(__file__).parent.resolve()

# Diretório de downloads temporários
DOWNLOADS_DIR = BASE_DIR / "downloads"

# Diretório para logs
LOGS_DIR = BASE_DIR / "logs"

# Diretório temporário
TEMP_DIR = BASE_DIR / "temp"

# Diretório para patches
PATCHES_DIR = BASE_DIR / "patches"

# ============================================
# Repositório local de receitas
# ============================================

LOCAL_REPO_DIR = BASE_DIR / "local_repo"  # Pasta para receitas locais (YAML)

# ============================================
# Repositórios remotos
# ============================================

REPO_URL = "https://example.com/merge/recipes/"  # URL base para receitas remotas
PATCH_URL = "https://example.com/merge/patches/"  # URL base para patches remotos

# Lista de URLs remotas opcionais (pode ter múltiplos)
REMOTE_REPO_URLS = [
    REPO_URL
]

# ============================================
# Flags e opções gerais
# ============================================

VERBOSE = True          # Mostrar logs detalhados
DRY_RUN = False         # Não executar ações, apenas simular
ENABLE_COLOR_LOGS = True  # Logs coloridos
ENABLE_NOTIFY = True      # Notificações desktop via notify-send
HTTP_TIMEOUT = 10         # Tempo limite para requisições HTTP em segundos
MAKE_THREADS = 4          # Threads para make -j
DEFAULT_USE_FLAGS = []    # Flags de compilação padrão
DEFAULT_HOOKS = {}        # Hooks globais padrão

# ============================================
# Diretórios de build e instalação
# ============================================

BUILD_DIR = BASE_DIR / "build"      # Pasta de builds temporários
INSTALL_PREFIX = "/usr/local"      # Prefixo de instalação padrão
