#!/usr/bin/env python3
import sys
import os
from modulos.install import install_with_resolver, build_package, fetch_package, extract_package, compile_package
from modulos.sync import sync_recipes
from modulos.recipe import load_recipe
from modulos.logs import log
from modulos.config import cfg
from modulos.repository import package_exists, is_installed

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"
CHECK = f"{GREEN}✓{RESET}"
UNCHECK = f"{RED}✗{RESET}"


def print_help():
    print(f"""
{CYAN}Merge - Gerenciador de pacotes estilo Portage{RESET}

Comandos:
  i <pacote>        Instalar pacote (com dependências)
  b <pacote>        Build: download, extract, patch, compile (não instala)
  f <pacote>        Somente baixar pacote (fetch)
  x <pacote>        Somente extrair pacote
  c <pacote>        Somente compilar pacote
  sync              Sincronizar receitas do Git
  info <pacote>     Mostrar informações detalhadas do pacote
  status            Mostrar status de instalação de todos os pacotes
  help              Mostrar esta ajuda
""")


def cmd_install(pkg_name):
    install_with_resolver(pkg_name, mode="recipe")


def cmd_build(pkg_name):
    build_package(pkg_name)


def cmd_fetch(pkg_name):
    fetch_package(pkg_name)


def cmd_extract(pkg_name):
    extract_package(pkg_name)


def cmd_compile(pkg_name):
    compile_package(pkg_name)


def cmd_sync():
    sync_recipes()


def cmd_info(pkg_name):
    if not package_exists(pkg_name):
        print(f"{RED}Pacote {pkg_name} não encontrado.{RESET}")
        return
    try:
        recipe = load_recipe(pkg_name)
        print(f"{CYAN}Informações de {pkg_name}:{RESET}")
        print(f"  Nome: {recipe.get('name', pkg_name)}")
        print(f"  Versão: {recipe.get('version', 'desconhecida')}")
        print(f"  Descrição: {recipe.get('description', '')}")
        print(f"  Fonte: {recipe.get('src_uri', '')}")
        print(f"  Dependências: {', '.join(recipe.get('dependencies', []))}")
        status = CHECK if is_installed(pkg_name) else UNCHECK
        print(f"  Status: {status}")
    except Exception as e:
        print(f"{RED}Erro ao carregar receita: {e}{RESET}")


def cmd_status():
    from modulos.recipe import recipe_dir
    recipes = [f[:-5] for f in os.listdir(recipe_dir()) if f.endswith(".yaml")]
    print(f"{CYAN}Status dos pacotes:{RESET}")
    for pkg in recipes:
        status = CHECK if is_installed(pkg) else UNCHECK
        print(f"  {pkg}: {status}")


def main():
    if len(sys.argv) < 2:
        print_help()
        sys.exit(0)

    cmd = sys.argv[1]
    pkg = sys.argv[2] if len(sys.argv) >= 3 else None

    if cmd in ["help", "h"]:
        print_help()
    elif cmd in ["i"]:
        if pkg: cmd_install(pkg)
    elif cmd in ["b"]:
        if pkg: cmd_build(pkg)
    elif cmd in ["f"]:
        if pkg: cmd_fetch(pkg)
    elif cmd in ["x"]:
        if pkg: cmd_extract(pkg)
    elif cmd in ["c"]:
        if pkg: cmd_compile(pkg)
    elif cmd in ["sync", "y"]:
        cmd_sync()
    elif cmd in ["info"]:
        if pkg: cmd_info(pkg)
    elif cmd in ["status", "s"]:
        cmd_status()
    else:
        print(f"{RED}Comando desconhecido: {cmd}{RESET}")
        print_help()


if __name__ == "__main__":
    main()
