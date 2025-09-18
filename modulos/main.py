#!/usr/bin/env python3
import sys
import os
from modulos.install import install_with_resolver, build_package, fetch_package, extract_package, compile_package
from modulos.sync import sync_recipes
from modulos.recipe import load_recipe, recipe_dir
from modulos.logs import log
from modulos.repository import package_exists, is_installed
from modulos.remove import remove_with_dependencies, remove_package, GREEN, RED, YELLOW, CYAN, RESET, CHECK, UNCHECK

def print_help():
    print(f"""
{CYAN}Merge - Gerenciador de pacotes estilo Portage{RESET}

Comandos:
  i <pacote>           Instalar pacote (com dependências)
  b <pacote>           Build: download, extract, patch, compile (não instala)
  f <pacote>           Somente baixar pacote (fetch)
  x <pacote>           Somente extrair pacote
  c <pacote>           Somente compilar pacote
  r <pacote> [--force] Remover pacote (opcional força)
  search <nome>        Procurar pacote por nome e status
  sync                 Sincronizar receitas do Git
  info <pacote>        Mostrar informações detalhadas do pacote
  status               Mostrar status de instalação de todos os pacotes
  help                 Mostrar esta ajuda
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
        status = CHECK if is_installed(pkg_name) else UNCHECK
        print(f"{CYAN}Informações de {pkg_name}:{RESET}")
        print(f"  Nome: {recipe.get('name', pkg_name)}")
        print(f"  Versão: {recipe.get('version', 'desconhecida')}")
        print(f"  Descrição: {recipe.get('description', '')}")
        print(f"  Fonte: {recipe.get('src_uri', '')}")
        print(f"  Dependências: {', '.join(recipe.get('dependencies', []))}")
        print(f"  Status: {status}")
    except Exception as e:
        print(f"{RED}Erro ao carregar receita: {e}{RESET}")


def cmd_status():
    recipes = [f[:-5] for f in os.listdir(recipe_dir()) if f.endswith(".yaml")]
    print(f"{CYAN}Status dos pacotes:{RESET}")
    for pkg in recipes:
        status = CHECK if is_installed(pkg) else UNCHECK
        print(f"  {pkg}: {status}")


def cmd_search(query):
    recipes = [f[:-5] for f in os.listdir(recipe_dir()) if f.endswith(".yaml")]
    results = [pkg for pkg in recipes if query.lower() in pkg.lower()]
    if not results:
        print(f"{YELLOW}Nenhum pacote encontrado para '{query}'{RESET}")
        return
    print(f"{CYAN}Pacotes encontrados para '{query}':{RESET}")
    for pkg in results:
        status = CHECK if is_installed(pkg) else UNCHECK
        print(f"  {pkg}: {status}")


def cmd_remove(pkg_name, force=False):
    remove_with_dependencies(pkg_name, force=force)


def main():
    if len(sys.argv) < 2:
        print_help()
        sys.exit(0)

    cmd = sys.argv[1]
    pkg = sys.argv[2] if len(sys.argv) >= 3 else None
    force_flag = "--force" in sys.argv

    if cmd in ["help", "h"]:
        print_help()
    elif cmd == "i" and pkg:
        cmd_install(pkg)
    elif cmd == "b" and pkg:
        cmd_build(pkg)
    elif cmd == "f" and pkg:
        cmd_fetch(pkg)
    elif cmd == "x" and pkg:
        cmd_extract(pkg)
    elif cmd == "c" and pkg:
        cmd_compile(pkg)
    elif cmd == "r" and pkg:
        cmd_remove(pkg, force=force_flag)
    elif cmd == "sync":
        cmd_sync()
    elif cmd == "info" and pkg:
        cmd_info(pkg)
    elif cmd == "status":
        cmd_status()
    elif cmd == "search" and pkg:
        cmd_search(pkg)
    else:
        print(f"{RED}Comando desconhecido ou parâmetro faltando: {cmd}{RESET}")
        print_help()


if __name__ == "__main__":
    main()
