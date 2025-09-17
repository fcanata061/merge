import os
from .config import cfg

def remove_package(package_name):
    install_path = cfg.get("global", "install_path")
    package_path = os.path.join(install_path, package_name)
    if os.path.exists(package_path):
        os.rmdir(package_path)
        print(f"Pacote '{package_name}' removido.")
        return True
    else:
        print(f"Pacote '{package_name}' não está instalado.")
        return False
