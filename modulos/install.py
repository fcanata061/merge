import os
import shutil
import subprocess
from .config import cfg
from .repository import package_exists, get_dependencies
from .recipe import get_commands
from .sandbox import run_in_sandbox
from .dependency import DependencyResolver
from .logs import log


def install_package(package_name, installed=None, mode="recipe", source_path=None):
    """
    Instala um pacote em três modos:
    - recipe: executa comandos do recipe.yaml em sandbox
    - binary: instala binário pré-compilado (tar.gz)
    - dir   : copia diretório local para install_path usando fakeroot
    """

    if installed is None:
        installed = set()

    if package_name in installed:
        return True  # já instalado neste ciclo

    if not package_exists(package_name):
        print(f"Erro: Pacote '{package_name}' não encontrado no repositório.")
        log(f"Erro: Pacote '{package_name}' não encontrado.")
        return False

    install_path = cfg.get("global", "install_path")
    os.makedirs(install_path, exist_ok=True)
    dest_dir = os.path.join(install_path, package_name)

    try:
        if mode == "recipe":
            commands = get_commands(package_name)
            if not run_in_sandbox(commands, package_name):
                print(f"Falha ao instalar pacote '{package_name}' via recipe.")
                return False

        elif mode == "binary":
            if not source_path or not os.path.exists(source_path):
                print("Erro: caminho do binário inválido")
                return False
            # Exemplo simples: tar.gz
            subprocess.run(f"tar -xzf {source_path} -C {install_path}",
                           shell=True, check=True)
            log(f"Pacote '{package_name}' instalado via binário em {install_path}")

        elif mode == "dir":
            if not source_path or not os.path.exists(source_path):
                print("Erro: diretório de origem inválido")
                return False
            # Usa fakeroot para copiar para install_path
            subprocess.run(f"fakeroot cp -r {source_path} {dest_dir}",
                           shell=True, check=True)
            log(f"Pacote '{package_name}' instalado via diretório em {dest_dir}")

        else:
            print(f"Modo de instalação '{mode}' não suportado")
            return False

        installed.add(package_name)
        print(f"Pacote '{package_name}' instalado com sucesso.")
        log(f"Pacote '{package_name}' instalado com sucesso no modo '{mode}'")
        return True

    except subprocess.CalledProcessError as e:
        print(f"Erro ao instalar pacote '{package_name}': {e}")
        log(f"Erro ao instalar pacote '{package_name}' no modo '{mode}': {e}")
        return False


def install_with_resolver(package_name, mode="recipe", source_path=None):
    """
    Resolve dependências com ordenação topológica e instala na ordem correta
    """
    resolver = DependencyResolver()
    try:
        order = resolver.resolve([package_name])
    except RuntimeError as e:
        print(f"Erro de dependência: {e}")
        log(f"Erro de dependência: {e}")
        return False

    print(f"Ordem de instalação calculada: {order}")
    log(f"Plano de instalação para '{package_name}': {order}")

    installed = set()
    for pkg in order:
        print(f"> Instalando {pkg} ...")
        success = install_package(pkg, installed=installed, mode=mode, source_path=source_path)
        if not success:
            print(f"Falha ao instalar {pkg}")
            log(f"Falha ao instalar {pkg}")
            return False

    return True
