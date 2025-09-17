import os
from .config import cfg

def list_packages():
    repo_path = cfg.get("global", "repository_path")
    if not os.path.exists(repo_path):
        return []
    return [pkg for pkg in os.listdir(repo_path) if os.path.isdir(os.path.join(repo_path, pkg))]

def package_exists(package_name):
    return package_name in list_packages()
