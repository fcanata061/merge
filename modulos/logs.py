import os
from datetime import datetime
from .config import cfg

# Diretório e arquivo de logs
LOG_DIR = cfg.get("global", "log_dir", fallback="/var/log/merge")
LOG_FILE = os.path.join(LOG_DIR, "merge.log")

# Cria diretório se não existir
os.makedirs(LOG_DIR, exist_ok=True)


def log(message, level="INFO"):
    """
    Registra uma mensagem de log com timestamp e nível.
    level: INFO, WARN, ERROR
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] [{level}] {message}\n"

    try:
        with open(LOG_FILE, "a") as f:
            f.write(line)
    except Exception as e:
        # Caso não consiga escrever no log, imprime na tela
        print(f"Erro ao escrever log: {e}")
