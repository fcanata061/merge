import os

# Diretórios padrões
BASE_DIR = os.path.expanduser('~/.merge')
REPO_DIR = os.path.join(BASE_DIR, 'repo')
BUILD_DIR = os.path.join(BASE_DIR, 'build')
STATE_FILE = os.path.join(BASE_DIR, 'state.json')
LOG_FILE = os.path.join(BASE_DIR, 'merge.log')

# Prefix de instalação padrão
PREFIX = '/usr/local'

# Número padrão de jobs para build paralelo
DEFAULT_JOBS = os.cpu_count() or 1

# Cria diretórios necessários
for directory in [BASE_DIR, REPO_DIR, BUILD_DIR]:
    os.makedirs(directory, exist_ok=True)

# Funções de configuração extras
def set_prefix(path: str):
    global PREFIX
    PREFIX = path

def set_state_file(path: str):
    global STATE_FILE
    STATE_FILE = path

def set_log_file(path: str):
    global LOG_FILE
    LOG_FILE = path
