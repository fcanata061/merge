import os
from .config import cfg

def list_packages():
    repo_path = cfg.get("global", "repository_path")
    if not os.path.exists(repo_path):
        return []
    return [pkg for pkg in os.listdir(repo_path) if os.path.isdir(os.path.join(repo_path, pkg))]

def package_exists(package_name):
    return package_name in list_packages()

def get_dependencies(package_name):
    """
    Lê um arquivo de dependências dentro do pacote no repositório.
    Exemplo: /var/lib/merge/repo/<pacote>/depends.txt
    """
    repo_path = cfg.get("global", "repository_path")
    depends_file = os.path.join(repo_path, package_name, "depends.txt")
    if os.path.exists(depends_file):
        with open(depends_file, "r") as f:
            return [line.strip() for line in f if line.strip()]
    return []
