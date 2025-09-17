import os
from .config import cfg
from .repository import package_exists, get_dependencies
from .ebuild import run_ebuild
from .logs import log

def install_package(package_name, installed=None):
    if installed is None:
        installed = set()

    if package_name in installed:
        return True  # já instalado

    if not package_exists(package_name):
        print(f"Erro: Pacote '{package_name}' não encontrado no repositório.")
        log(f"Erro: Pacote '{package_name}' não encontrado.")
        return False

    # Instalar dependências primeiro
    dependencies = get_dependencies(package_name)
    for dep in dependencies:
        if not install_package(dep, installed):
            print(f"Falha ao instalar dependência: {dep}")
            return False

    # Executar script de instalação (ebuild)
    if run_ebuild(package_name):
        installed.add(package_name)
        print(f"Pacote '{package_name}' instalado com sucesso.")
        return True
    else:
        return False
