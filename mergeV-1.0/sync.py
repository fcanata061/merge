import os
import subprocess
import asyncio
from typing import List
from logs import stage, info, warn, error

class SyncManager:
    def __init__(self, repo_url: str, local_dir: str = os.path.expanduser('~/.merge/repo'), dry_run: bool = False):
        self.repo_url = repo_url
        self.local_dir = local_dir
        self.dry_run = dry_run

    async def sync_repo(self, pre_hook: Optional[Callable] = None, post_hook: Optional[Callable] = None) -> bool:
        """Sincroniza o repositório remoto com o diretório local."""
        if pre_hook:
            await self._maybe_async_hook(pre_hook)

        stage(f'Synchronizing repository: {self.repo_url}')

        if not os.path.exists(self.local_dir):
            info(f'Repository directory does not exist, cloning to {self.local_dir}')
            if self.dry_run:
                info(f'DRY-RUN: Would clone {self.repo_url} to {self.local_dir}')
            else:
                try:
                    subprocess.run(['git', 'clone', self.repo_url, self.local_dir], check=True)
                    info('Repository cloned successfully')
                except subprocess.CalledProcessError as e:
                    error(f'Failed to clone repository: {e}')
                    return False
        else:
            info(f'Repository exists at {self.local_dir}, pulling latest changes')
            if self.dry_run:
                info(f'DRY-RUN: Would pull latest changes in {self.local_dir}')
            else:
                try:
                    subprocess.run(['git', 'pull'], cwd=self.local_dir, check=True)
                    info('Repository updated successfully')
                except subprocess.CalledProcessError as e:
                    error(f'Failed to update repository: {e}')
                    return False

        if post_hook:
            await self._maybe_async_hook(post_hook)

        return True

    def list_recipes(self) -> List[str]:
        """Lista os arquivos de receitas YAML no repositório local."""
        stage(f'Listing recipes in {self.local_dir}')
        recipes = []
        if os.path.exists(self.local_dir):
            for f in os.listdir(self.local_dir):
                if f.endswith('.yaml') or f.endswith('.yml'):
                    recipes.append(f)
        else:
            warn(f'Repository directory {self.local_dir} does not exist')
        return recipes

    async def _maybe_async_hook(self, hook: Optional[Callable]):
        """Executa hook que pode ser sync ou async."""
        if hook:
            if asyncio.iscoroutinefunction(hook):
                await hook()
            else:
                hook()
