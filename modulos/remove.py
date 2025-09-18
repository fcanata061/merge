import os
import subprocess
import sys
import time
from .config import cfg
from .logs import log
from .repository import is_installed, get_reverse_dependencies
from .sandbox import run_in_sandbox

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

ANIMATION = ["|", "/", "-", "\\"]


def spinner(duration=2):
    """Animação simples estilo Portage"""
    end_time = time.time() + duration
    i = 0
    while time.time() < end_time:
        sys.stdout.write(f"\r{CYAN}Removendo... {ANIMATION[i % len(ANIMATION)]}{RESET}")
        sys.stdout.flush()
        time.sleep(0.1)
        i += 1
    sys.stdout.write("\r")  # Limpa linha


def remove_package(pkg_name, force=False):
    """
    Remove um pacote instalado
    force: ignora dependências
    """
    if not is_installed(pkg_name):
        print(f"{YELLOW}Pacote {pkg_name} não está instalado.{RESET}")
        return False

    # Verifica se outros pacotes dependem deste
    reverse_deps = get_reverse_dependencies(pkg_name)
    if reverse_deps and not force:
        print(f"{RED}Não é possível remover {pkg_name}: outros pacotes dependem dele: {', '.join(reverse_deps)}{RESET}")
        return False

    install_path = cfg.get("global", "install_path")
    pkg_path = os.path.join(install_path, pkg_name)
    if not os.path.exists(pkg_path):
        print(f"{RED}Diretório de instalação não encontrado: {pkg_path}{RESET}")
        return False

    try:
        # Animação estilo Portage
        spinner(duration=1.5)

        # Remove dentro de sandbox para segurança
        cmd = [f"rm -rf {pkg_path}"]
        if not run_in_sandbox(cmd, pkg_name):
            print(f"{RED}Falha ao remover {pkg_name} em sandbox{RESET}")
            log(f"Falha ao remover {pkg_name}")
            return False

        print(f"{GREEN}Pacote {pkg_name} removido com sucesso{RESET}")
        log(f"Pacote {pkg_name} removido")
        return True

    except Exception as e:
        print(f"{RED}Erro ao remover {pkg_name}: {e}{RESET}")
        log(f"Erro ao remover {pkg_name}: {e}")
        return False


def remove_with_dependencies(pkg_name, force=False):
    """
    Remove pacote e dependências órfãs
    """
    if not is_installed(pkg_name):
        print(f"{YELLOW}Pacote {pkg_name} não está instalado.{RESET}")
        return False

    # Primeiro remove dependências órfãs
    reverse_deps = get_reverse_dependencies(pkg_name)
    if reverse_deps and not force:
        print(f"{RED}Não é possível remover {pkg_name}: outros pacotes dependem dele: {', '.join(reverse_deps)}{RESET}")
        return False

    # Remover pacote principal
    return remove_package(pkg_name, force=force)
