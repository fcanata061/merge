import os
import subprocess
from .config import cfg
from .logs import log

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def sync_recipes():
    repo_url = cfg.get("global", "repo_url", fallback=None)
    repo_path = cfg.get("global", "repo_path", fallback="/var/lib/merge/repo")

    if not repo_url:
        print(f"{RED}Nenhum repositório Git definido em /etc/merge.conf (repo_url).{RESET}")
        return False

    os.makedirs(repo_path, exist_ok=True)

    try:
        if not os.path.exists(os.path.join(repo_path, ".git")):
            print(f"{YELLOW}[SYNC]{RESET} Clonando repositório de receitas...")
            subprocess.run(
                ["git", "clone", repo_url, repo_path],
                check=True
            )
        else:
            print(f"{YELLOW}[SYNC]{RESET} Atualizando repositório de receitas...")
            subprocess.run(
                ["git", "-C", repo_path, "pull", "--rebase"],
                check=True
            )
        print(f"{GREEN}[SYNC]{RESET} Repositório sincronizado com sucesso.")
        log(f"Sync concluído com {repo_url}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"{RED}[SYNC] Falha ao sincronizar: {e}{RESET}")
        log(f"Erro de sync: {e}")
        return False
