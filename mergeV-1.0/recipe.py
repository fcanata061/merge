import os
import yaml
from typing import List, Dict
from logs import stage, error, info
from config import REPO_DIR

class Recipe:
    def __init__(self, path: str):
        self.path = path
        self.data = self._load_yaml()

    def _load_yaml(self) -> Dict:
        if not os.path.exists(self.path):
            error(f'Recipe file not found: {self.path}')
            return {}
        try:
            with open(self.path, 'r') as f:
                data = yaml.safe_load(f)
            info(f'Loaded recipe: {os.path.basename(self.path)}')
            return data
        except yaml.YAMLError as e:
            error(f'YAML parse error in {self.path}: {e}')
            return {}

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

# Função para listar todas as receitas disponíveis
def list_recipes() -> List[Recipe]:
    recipes = []
    for file in os.listdir(REPO_DIR):
        if file.endswith('.yaml') or file.endswith('.yml'):
            path = os.path.join(REPO_DIR, file)
            recipes.append(Recipe(path))
    stage(f'Found {len(recipes)} recipes in repo')
    return recipes

# Teste rápido
if __name__ == '__main__':
    for r in list_recipes():
        info(f'Recipe: {r.name}, version: {r.version}')
