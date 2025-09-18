import os
import yaml
import json
import asyncio
from typing import List, Dict
from logs import info, error
from config import REPO_DIR

class Recipe:
    def __init__(self, path: str):
        self.path = path
        self.data = self._load_data()

    def _load_data(self) -> Dict:
        if not os.path.exists(self.path):
            error(f'Recipe file not found: {self.path}')
            return {}

        try:
            with open(self.path, 'r') as f:
                if self.path.endswith('.yaml') or self.path.endswith('.yml'):
                    return yaml.safe_load(f)
                elif self.path.endswith('.json'):
                    return json.load(f)
                else:
                    error(f'Unsupported file format: {self.path}')
                    return {}
        except (yaml.YAMLError, json.JSONDecodeError) as e:
            error(f'Error parsing {self.path}: {e}')
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

async def list_recipes() -> List[Recipe]:
    recipes = []
    for file in os.listdir(REPO_DIR):
        if file.endswith(('.yaml', '.yml', '.json')):
            path = os.path.join(REPO_DIR, file)
            recipes.append(Recipe(path))
    info(f'Found {len(recipes)} recipes in repo')
    return recipes

# Teste rápido
if __name__ == '__main__':
    asyncio.run(list_recipes())
