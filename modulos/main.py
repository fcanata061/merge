import sys
import shutil
from .install import (
    install_with_resolver,
    fetch_package,
    extract_package,
    patch_package,
    compile_package,
    build_package,
)
from .remove import remove_package
from .repository import list_packages, package_exists
from .recipe import load_recipe
from .logs import log
from .sync import sync_recipes

# Cores para saída
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def print_help():
    print(f"""
{YELLOW}merge - Gerenciador de pacotes inspirado no Portage{RESET}

Comandos:
  install (i) <pacote>     Instala pacote e dependências
  build (b) <pacote>       Baixa, extrai, aplica patch e compila (não instala)
  fetch (f) <pacote>       Apenas baixa
  extract (x) <pacote>     Apenas extrai
  patch (p) <pacote>       Apenas aplica patches
  compile (c) <pacote>     Apenas compila
  remove (r) <pacote>      Remove pacote
  list (l)                 Lista pacotes disponíveis
  search (s) <nome>        Procura pacotes
  info (nfo) <pacote>      Mostra informações do pacote
  sync (y)                 Sincroniza receitas do repositório Git
  help (h)                 Mostra esta ajuda
""")


def check_installed(pkg_name, install_path):
    """Verifica se o pacote já está instalado"""
    if shutil.which(pkg_name) or (shutil.which(f"/usr/local/merge/{pkg_name}")):
        return f"[{GREEN}✔{RESET}]"
    return f"[{RED}✘{RESET}]"


def cmd_info(pkg):
    if not package_exists(pkg):
        print(f"{RED}Pacote '{pkg}' não encontrado no repositório.{RESET}")
        return
    recipe = load_recipe(pkg)
    print(f"{YELLOW}Informações de {pkg}:{RESET}")
    print(f"  Dependências: {recipe.get('dependencies', [])}")
    print(f"  Comandos: {recipe.get('commands', [])}")
    print(f"  Descrição: {recipe.get('description', 'N/A')}")
    print(f"  Versão: {recipe.get('version', 'N/A')}")


def main():
    if len(sys.argv) < 2:
        print_help()
        return

    cmd = sys.argv[1]
    args = sys.argv[2:]

    # Aliases
    if cmd in ["install", "i"]:
        if len(args) < 1:
            print_help(); return
        install_with_resolver(args[0])

    elif cmd in ["build", "b"]:
        if len(args) < 1:
            print_help(); return
        build_package(args[0])

    elif cmd in ["fetch", "f"]:
        if len(args) < 1:
            print_help(); return
        fetch_package(args[0])

    elif cmd in ["extract", "x"]:
        if len(args) < 1:
            print_help(); return
        extract_package(args[0])

    elif cmd in ["patch", "p"]:
        if len(args) < 1:
            print_help(); return
        patch_package(args[0])

    elif cmd in ["compile", "c"]:
        if len(args) < 1:
            print_help(); return
        compile_package(args[0])

    elif cmd in ["remove", "r"]:
        if len(args) < 1:
            print_help(); return
        remove_package(args[0])

    elif cmd in ["list", "l"]:
        for pkg in list_packages():
            status = check_installed(pkg, "/usr/local/merge")
            print(f"{status} {pkg}")

    elif cmd in ["search", "s"]:
        if len(args) < 1:
            print_help(); return
        term = args[0].lower()
        found = [p for p in list_packages() if term in p.lower()]
        for p in found:
            status = check_installed(p, "/usr/local/merge")
            print(f"{status} {p}")
        if not found:
            print(f"{RED}Nenhum pacote encontrado para '{term}'.{RESET}")

    elif cmd in ["info", "nfo"]:
        if len(args) < 1:
            print_help(); return
        cmd_info(args[0])

    elif cmd in ["help", "h"]:
        print_help()

    elif cmd in ["sync", "y"]:
    sync_recipes()

    else:
        print_help()


if __name__ == "__main__":
    main()
