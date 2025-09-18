import os
import subprocess
import asyncio
import yaml
from typing import List, Optional, Callable
from logs import stage, info, warn, error

class RepoSyncError(Exception):
    pass

class SyncManager:
    def __init__(self, repos: List[dict], dry_run: bool = False, retries: int = 3):
        """
        :param repos: Lista de repositórios com dicts {url, local_dir, pre_hook, post_hook}
        :param dry_run: Se True, não realiza operações de escrita
        :param retries: Número de tentativas em caso de falha
        """
        self.repos = repos
        self.dry_run = dry_run
        self.retries = retries

    async def sync_all(self):
        """Sincroniza todos os repositórios em paralelo."""
        tasks = [self.sync_repo(repo) for repo in self.repos]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for repo, res in zip(self.repos, results):
            if isinstance(res, Exception):
                error(f"Erro ao sincronizar {repo['url']}: {res}")
        return results

    async def sync_repo(self, repo: dict):
        url = repo.get("url")
        local_dir = repo.get("local_dir", os.path.expanduser('~/.merge/repo'))
        pre_hook = repo.get("pre_hook")
        post_hook = repo.get("post_hook")

        await self._maybe_async_hook(pre_hook)

        stage(f"Sincronizando repositório: {url}")
        for attempt in range(1, self.retries + 1):
            try:
                if not os.path.exists(local_dir):
                    await self._git_clone(url, local_dir)
                else:
                    await self._git_pull(local_dir)
                break
            except RepoSyncError as e:
                warn(f"Tentativa {attempt} falhou para {url}: {e}")
                if attempt == self.retries:
                    raise e
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

        await self._maybe_async_hook(post_hook)

    async def _git_clone(self, url: str, local_dir: str):
        if self.dry_run:
            info(f"DRY-RUN: Clonaria {url} para {local_dir}")
            return
        try:
            result = subprocess.run(['git', 'clone', url, local_dir],
                                    capture_output=True, text=True, check=True)
            info(f"Clonagem bem-sucedida: {result.stdout}")
        except subprocess.CalledProcessError as e:
            raise RepoSyncError(e.stderr)

    async def _git_pull(self, local_dir: str):
        if self.dry_run:
            info(f"DRY-RUN: Atualizaria repositório em {local_dir}")
            return
        try:
            result = subprocess.run(['git', 'pull'], cwd=local_dir,
                                    capture_output=True, text=True, check=True)
            info(f"Pull bem-sucedido: {result.stdout}")
        except subprocess.CalledProcessError as e:
            raise RepoSyncError(e.stderr)

    def list_recipes(self, local_dir: str) -> List[str]:
        """Lista arquivos YAML no repositório local."""
        stage(f"Listando receitas em {local_dir}")
        if not os.path.exists(local_dir):
            warn(f"Diretório {local_dir} não existe")
            return []
        return [f for f in os.listdir(local_dir) if f.endswith(('.yml', '.yaml'))]

    async def _maybe_async_hook(self, hook: Optional[Callable]):
        if hook:
            if asyncio.iscoroutinefunction(hook):
                await hook()
            else:
                hook()

    @classmethod
    def from_config(cls, path: str, dry_run: bool = False, retries: int = 3):
        """Cria SyncManager a partir de arquivo YAML ou JSON."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"Config {path} não encontrado")
        with open(path, 'r', encoding='utf-8') as f:
            if path.endswith('.yaml') or path.endswith('.yml'):
                repos = yaml.safe_load(f)
            else:
                import json
                repos = json.load(f)
        return cls(repos, dry_run=dry_run, retries=retries)
