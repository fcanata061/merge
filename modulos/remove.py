import os
from .config import cfg
from .logs import log

def remove_package(package_name):
    install_path = cfg.get("global", "install_path")
    package_path = os.path.join(install_path, package_name)
    if os.path.exists(package_path):
        os.rmdir(package_path)
        log(f"Pacote '{package_name}' removido.")
        print(f"Pacote '{package_name}' removido.")
        return True
    else:
        print(f"Pacote '{package_name}' não está instalado.")
        log(f"Falha ao remover '{package_name}': não instalado.")
        return False
