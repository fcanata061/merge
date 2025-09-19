import os
from pathlib import Path

class Config:
    """
    Classe para armazenar e gerenciar as configurações do gerenciador de programas.
    """

    # ============================
    # Diretórios principais
    # ============================
    BASE_DIR = Path(__file__).parent.resolve()
    DOWNLOAD_DIR = BASE_DIR / "downloads"
    LOG_DIR = BASE_DIR / "logs"
    TEMP_DIR = BASE_DIR / "temp"
    PATCH_DIR = BASE_DIR / "patches"
    LOCAL_REPO_DIR = "/usr/merge/repo"

    # ============================
    # URLs e repositórios
    # ============================
    REPO_URL = "https://github.com/fcanata061/merge"
    PATCH_URL = "https://github.com/fcanata061/merge/patches"

    # ============================
    # Flags de execução
    # ============================
    VERBOSE = True
    DRY_RUN = False

    # ============================
    # Métodos de inicialização
    # ============================
    @classmethod
    def ensure_directories(cls):
        """
        Cria diretórios essenciais se não existirem.
        """
        for path in [cls.DOWNLOAD_DIR, cls.LOG_DIR, cls.TEMP_DIR, cls.PATCH_DIR]:
            os.makedirs(path, exist_ok=True)
            if cls.VERBOSE:
                print(f"[Config] Diretório garantido: {path}")

    # ============================
    # Métodos para alterar flags
    # ============================
    @classmethod
    def set_verbose(cls, value: bool):
        """
        Ativa ou desativa mensagens detalhadas.
        """
        cls.VERBOSE = bool(value)
        print(f"[Config] Verbose setado para: {cls.VERBOSE}")

    @classmethod
    def set_dry_run(cls, value: bool):
        """
        Ativa ou desativa o modo de simulação (dry-run).
        """
        cls.DRY_RUN = bool(value)
        if cls.VERBOSE:
            print(f"[Config] Dry-run setado para: {cls.DRY_RUN}")

    # ============================
    # Validação de paths e URLs
    # ============================
    @classmethod
    def validate_directories(cls):
        """
        Verifica se os diretórios existem e são graváveis.
        """
        for path in [cls.DOWNLOAD_DIR, cls.LOG_DIR, cls.TEMP_DIR, cls.PATCH_DIR]:
            if not path.exists():
                raise FileNotFoundError(f"Diretório não encontrado: {path}")
            if not os.access(path, os.W_OK):
                raise PermissionError(f"Sem permissão de escrita no diretório: {path}")

    @classmethod
    def validate_urls(cls):
        """
        Verifica se as URLs estão bem formadas.
        """
        from urllib.parse import urlparse
        for url in [cls.REPO_URL, cls.PATCH_URL]:
            result = urlparse(url)
            if not all([result.scheme, result.netloc]):
                raise ValueError(f"URL inválida: {url}")

# ============================
# Inicialização automática
# ============================
Config.ensure_directories()
Config.validate_urls()
