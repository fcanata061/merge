import os
import yaml
from .config import cfg

def load_recipe(package_name):
    repo_path = cfg.get("global", "repository_path")
    recipe_file = os.path.join(repo_path, package_name, "recipe.yaml")
    if not os.path.exists(recipe_file):
        return None

    with open(recipe_file, "r") as f:
        return yaml.safe_load(f)

def get_dependencies(package_name):
    recipe = load_recipe(package_name)
    if recipe:
        return recipe.get("dependencies", [])
    return []

def get_commands(package_name):
    recipe = load_recipe(package_name)
    if recipe:
        return recipe.get("commands", [])
    return []
