import os
import yaml
from .config import cfg

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"


def recipe_dir():
    """Retorna o diretório local das receitas sincronizadas"""
    recipes_dir = cfg.get("global", "recipes_dir", fallback="/var/lib/merge/recipes")
    if not os.path.exists(recipes_dir):
        print(f"{RED}[RECIPE] Diretório de receitas não encontrado: {recipes_dir}{RESET}")
    return recipes_dir


def recipe_path(pkg_name):
    """Retorna o caminho absoluto do YAML da receita"""
    return os.path.join(recipe_dir(), f"{pkg_name}.yaml")


def load_recipe(pkg_name):
    """Carrega uma receita YAML a partir do diretório local"""
    path = recipe_path(pkg_name)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Receita não encontrada para {pkg_name}: {path}")

    with open(path, "r") as f:
        return yaml.safe_load(f)


def get_commands(pkg_name, section="install"):
    """Retorna comandos definidos na seção da receita"""
    recipe = load_recipe(pkg_name)
    return recipe.get(section, [])
