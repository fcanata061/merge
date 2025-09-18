import os
import yaml
from .config import cfg

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"


def recipe_dir():
    """Retorna o caminho do diretório de receitas a partir do repo_path configurado"""
    repo_path = cfg.get("global", "repo_path", fallback="/var/lib/merge/repo")
    recipes_path = os.path.join(repo_path, "recipes")
    if not os.path.exists(recipes_path):
        print(f"{RED}[RECIPE] Diretório de receitas não encontrado: {recipes_path}{RESET}")
    return recipes_path


def recipe_path(pkg_name):
    """Retorna o caminho absoluto da receita de um pacote"""
    recipes_path = recipe_dir()
    return os.path.join(recipes_path, f"{pkg_name}.yaml")


def load_recipe(pkg_name):
    """Carrega o arquivo YAML da receita"""
    path = recipe_path(pkg_name)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Receita não encontrada para {pkg_name}: {path}")

    with open(path, "r") as f:
        return yaml.safe_load(f)


def get_commands(pkg_name, section="install"):
    """Retorna os comandos definidos em uma seção da receita"""
    recipe = load_recipe(pkg_name)
    return recipe.get(section, [])
