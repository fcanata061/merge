import os
from .config import cfg
from .repository import package_exists

def install_package(package_name):
    if not package_exists(package_name):
        print(f"Erro: Pacote '{package_name}' não encontrado no repositório.")
        return False

    install_path = cfg.get("global", "install_path")
    os.makedirs(install_path, exist_ok=True)
    
    package_path = os.path.join(install_path, package_name)
    os.makedirs(package_path, exist_ok=True)
    print(f"Pacote '{package_name}' instalado em {package_path}")
    return True
