# sync.py - Módulo para sincronizar o Merge com repositório Git e baixar diretórios de receitas

import os
import subprocess
from logs import stage, info, warn, error

class SyncManager:
    def __init__(self, repo_url: str, local_dir: str = os.path.expanduser('~/.merge/repo')):
        self.repo_url = repo_url
        self.local_dir = local_dir

    def sync_repo(self) -> bool:
        stage(f'Synchronizing repository: {self.repo_url}')
        if not os.path.exists(self.local_dir):
            info(f'Repository directory does not exist, cloning to {self.local_dir}')
            try:
                subprocess.run(['git', 'clone', self.repo_url, self.local_dir], check=True)
                info('Repository cloned successfully')
            except subprocess.CalledProcessError as e:
                error(f'Failed to clone repository: {e}')
                return False
        else:
            info(f'Repository exists at {self.local_dir}, pulling latest changes')
            try:
                subprocess.run(['git', 'pull'], cwd=self.local_dir, check=True)
                info('Repository updated successfully')
            except subprocess.CalledProcessError as e:
                error(f'Failed to update repository: {e}')
                return False
        return True

    def list_recipes(self) -> list:
        stage(f'Listing recipes in {self.local_dir}')
        recipes = []
        if os.path.exists(self.local_dir):
            for f in os.listdir(self.local_dir):
                if f.endswith('.yaml') or f.endswith('.yml'):
                    recipes.append(f)
        else:
            warn(f'Repository directory {self.local_dir} does not exist')
        return recipes

# Teste rápido
if __name__ == '__main__':
    repo_url = 'https://github.com/SEU_USUARIO/MergeRecipes.git'
    sync = SyncManager(repo_url)
    if sync.sync_repo():
        recipes = sync.list_recipes()
        info(f'Recipes found: {recipes}')
