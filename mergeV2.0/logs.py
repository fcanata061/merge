import sys
import datetime
import logging
import os

# ==============================
# Configuração de cores (ANSI)
# ==============================
RESET = '\033[0m'
CYAN = '\033[36m'
GREEN = '\033[32m'
YELLOW = '\033[33m'
RED = '\033[31m'
MAGENTA = '\033[35m'

# Níveis de log e cores
LEVELS = {
    'INFO': CYAN,
    'SUCCESS': GREEN,
    'WARN': YELLOW,
    'ERROR': RED,
    'STAGE': MAGENTA
}

# ==============================
# Configuração padrão
# ==============================
LOG_FILE = "system.log"  # Arquivo de log padrão (drop-in)
LOG_LEVEL = logging.DEBUG  # Mostra tudo por padrão

# ==============================
# Funções de configuração
# ==============================
def set_log_file(path: str):
    """Define arquivo de log."""
    global LOG_FILE
    LOG_FILE = path

def set_log_level(level: str):
    """Define nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)."""
    global LOG_LEVEL
    mapping = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    LOG_LEVEL = mapping.get(level.upper(), logging.DEBUG)

# ==============================
# Função interna de escrita
# ==============================
def _write(message: str):
    """Escreve mensagem no terminal e no arquivo de log."""
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    full_message = f'[{timestamp}] {message}'
    print(full_message)
    if LOG_FILE:
        try:
            with open(LOG_FILE, 'a') as f:
                f.write(full_message + '\n')
        except Exception as e:
            print(f"[ERROR] Não foi possível escrever no arquivo de log: {e}")

# ==============================
# Função genérica de log (compatível)
# ==============================
def log(message: str, level: str = 'INFO'):
    """Função de log genérica compatível com sistema antigo."""
    level = level.upper()
    if level not in LEVELS:
        level = 'INFO'
    color = LEVELS.get(level, '')
    _write(f'{color}{level:<7}{RESET} {message}')

# ==============================
# Funções antigas mantidas
# ==============================
def info(message: str):
    if LOG_LEVEL <= logging.INFO:
        log(message, 'INFO')

def success(message: str):
    if LOG_LEVEL <= logging.INFO:
        log(message, 'SUCCESS')

def warn(message: str):
    if LOG_LEVEL <= logging.WARNING:
        log(message, 'WARN')

def error(message: str):
    if LOG_LEVEL <= logging.ERROR:
        log(message, 'ERROR')

def stage(message: str):
    if LOG_LEVEL <= logging.DEBUG:
        log(message, 'STAGE')

# ==============================
# Inicialização automática
# ==============================
# Se desejar, você pode ativar logs coloridos e arquivo sem mexer no sistema antigo
if not os.path.exists(LOG_FILE):
    try:
        open(LOG_FILE, 'w').close()
    except Exception:
        pass

# ==============================
# Teste rápido (quando chamado diretamente)
# ==============================
if __name__ == '__main__':
    info("Mensagem de info")
    success("Mensagem de sucesso")
    warn("Mensagem de aviso")
    error("Mensagem de erro")
    stage("Mensagem de estágio")
