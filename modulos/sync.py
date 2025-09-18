import os
import subprocess
from .config import cfg
from .logs import log

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def sync_recipes():
    """Sincroniza todas as receitas do repositório Git para um diretório local"""
    repo_url = cfg.get("global", "repo_url", fallback=None)
    recipes_dir = cfg.get("global", "recipes_dir", fallback="/var/lib/merge/recipes")

    if not repo_url:
        print(f"{RED}Nenhum repositório Git definido em /etc/merge.conf (repo_url).{RESET}")
        return False

    os.makedirs(recipes_dir, exist_ok=True)

    try:
        if not os.path.exists(os.path.join(recipes_dir, ".git")):
            print(f"{YELLOW}[SYNC]{RESET} Clonando repositório de receitas para {recipes_dir} ...")
            subprocess.run(
                ["git", "clone", repo_url, recipes_dir],
                check=True
            )
        else:
            print(f"{YELLOW}[SYNC]{RESET} Atualizando repositório de receitas em {recipes_dir} ...")
            subprocess.run(
                ["git", "-C", recipes_dir, "pull", "--rebase"],
                check=True
            )
        print(f"{GREEN}[SYNC]{RESET} Repositório sincronizado com sucesso.")
        log(f"Sync concluído com {repo_url}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"{RED}[SYNC] Falha ao sincronizar: {e}{RESET}")
        log(f"Erro de sync: {e}")
        return False
