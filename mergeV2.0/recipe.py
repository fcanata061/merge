import os
import yaml
from config import LOCAL_REPO_DIR
from logs import info, warn

class Recipe:
    """Representa uma receita individual"""
    def __init__(self, data):
        self.name = data.get("name")
        self.version = data.get("version")
        self.description = data.get("description")
        self.homepage = data.get("homepage")
        self.license = data.get("license")
        self.dependencies = data.get("dependencies", [])
        self.repo_url = data.get("repo_url")
        self.patch_url = data.get("patch_url", [])
        self.build_dir = data.get("build_dir")
        self.install_prefix = data.get("install_prefix")
        self.use_flags = data.get("use_flags", [])
        self.hooks = data.get("hooks", {})
        self.build_commands = data.get("build_commands", [])
        self.install_commands = data.get("install_commands", [])

class RecipeManager:
    """Gerencia todas as receitas do Merge"""
    def __init__(self, local_repo=LOCAL_REPO_DIR):
        self.local_repo = local_repo
        self.recipes = []

    def load_local_recipes(self):
        """Carrega todas as receitas YAML do repositório local recursivamente"""
        if not os.path.exists(self.local_repo):
            warn(f"Pasta de receitas local não encontrada: {self.local_repo}")
            return

        for root, dirs, files in os.walk(self.local_repo):
            for file in files:
                if file.endswith(".yaml") or file.endswith(".yml"):
                    path = os.path.join(root, file)
                    try:
                        with open(path, "r") as f:
                            data = yaml.safe_load(f)
                            if data:
                                recipe = Recipe(data)
                                self.recipes.append(recipe)
                                info(f"Receita carregada: {recipe.name} ({recipe.version})")
                            else:
                                warn(f"Arquivo vazio ou inválido: {file}")
                    except Exception as e:
                        warn(f"Erro ao carregar {file}: {e}")

    def list_recipes(self):
        """Retorna todas as receitas carregadas"""
        return self.recipes

    def find_recipe(self, name):
        """Busca receita pelo nome"""
        for recipe in self.recipes:
            if recipe.name == name:
                return recipe
        return None

    def add_recipe(self, data):
        """Adiciona uma nova receita em memória (não salva no disco)"""
        recipe = Recipe(data)
        self.recipes.append(recipe)
        info(f"Receita adicionada em memória: {recipe.name} ({recipe.version})")
        return recipe
