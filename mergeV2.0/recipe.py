import os
import yaml
import json
import asyncio
from typing import List, Dict
from logs import info, warn, error
from config import REPO_DIR

class Recipe:
    def __init__(self, path: str):
        self.path = path
        self.data = self._load_data()

    def _load_data(self) -> Dict:
        """Carrega os dados da receita e mantém compatibilidade com o sistema antigo."""
        if not os.path.exists(self.path):
            warn(f'Recipe file not found: {self.path}')
            return {}

        try:
            with open(self.path, 'r') as f:
                if self.path.endswith(('.yaml', '.yml')):
                    return yaml.safe_load(f) or {}
                elif self.path.endswith('.json'):
                    return json.load(f)
                else:
                    warn(f'Unsupported file format: {self.path}')
                    return {}
        except (yaml.YAMLError, json.JSONDecodeError) as e:
            error(f'Error parsing {self.path}: {e}')
            return {}

    def _validate_data(self) -> bool:
        """Valida as chaves obrigatórias da receita."""
        required_keys = ['name', 'version', 'src_uri']
        for key in required_keys:
            if key not in self.data:
                warn(f'Missing required key "{key}" in recipe: {self.path}')
                return False
        return True

    # ============================
    # Propriedades compatíveis
    # ============================
    @property
    def name(self) -> str:
        return self.data.get('name', 'unknown')

    @property
    def version(self) -> str:
        return self.data.get('version', '0.0.0')

    @property
    def src_uri(self) -> List[str]:
        return self.data.get('src_uri', [])

    @property
    def dependencies(self) -> Dict:
        return self.data.get('dependencies', {})

    @property
    def use_flags(self) -> List[str]:
        return self.data.get('use_flags', [])

    @property
    def patches(self) -> List[str]:
        return self.data.get('patches', [])

    @property
    def hooks(self) -> Dict[str, str]:
        return self.data.get('hooks', {})

    @property
    def update_source(self) -> Dict[str, str]:
        return self.data.get('update_source', {})

    def is_valid(self) -> bool:
        """Verifica se a receita está válida."""
        return self._validate_data()

# ============================
# Função assíncrona para listar receitas
# ============================
async def list_recipes() -> List[Recipe]:
    """Lista todas as receitas válidas no repositório."""
    recipes = []
    if not os.path.exists(REPO_DIR):
        warn(f'Repository directory does not exist: {REPO_DIR}')
        return recipes

    for file in os.listdir(REPO_DIR):
        if file.endswith(('.yaml', '.yml', '.json')):
            path = os.path.join(REPO_DIR, file)
            recipe = Recipe(path)
            if recipe.is_valid():
                recipes.append(recipe)
    info(f'Found {len(recipes)} valid recipes in repo')
    return recipes

# ============================
# Teste rápido (compatível)
# ============================
if __name__ == '__main__':
    asyncio.run(list_recipes())
