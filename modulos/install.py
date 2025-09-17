from .config import cfg
from .repository import package_exists
from .recipe import get_dependencies, get_commands
from .sandbox import run_in_sandbox
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
    for dep in get_dependencies(package_name):
        if not install_package(dep, installed):
            print(f"Falha ao instalar dependência: {dep}")
            return False

    # Executar comandos dentro do sandbox
    commands = get_commands(package_name)
    if run_in_sandbox(commands, package_name):
        installed.add(package_name)
        print(f"Pacote '{package_name}' instalado com sucesso.")
        log(f"Pacote '{package_name}' instalado com sucesso.")
        return True
    else:
        print(f"Falha ao instalar pacote '{package_name}'")
        return False
