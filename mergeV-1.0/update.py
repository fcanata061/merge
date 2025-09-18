import os
import subprocess
import requests
import asyncio
from typing import Dict
from recipe import list_recipes
from logs import stage, info, warn, error
from bs4 import BeautifulSoup

class Updater:
    def __init__(self):
        self.recipes = list_recipes()

    async def check_updates(self) -> Dict[str, Dict[str, str]]:
        """Verifica novas versões disponíveis para todas as receitas."""
        updates = {}
        stage('Checking for updates...')
        for recipe in self.recipes:
            update_info = recipe.update_source
            if not update_info:
                continue
            for source_type, url in update_info.items():
                try:
                    if source_type in ['http', 'https']:
                        r = await self._fetch_url(url)
                        latest_version = await self._parse_version(r, url, recipe)
                        if latest_version and latest_version != recipe.version:
                            updates[recipe.name] = {
                                'current': recipe.version,
                                'latest': latest_version,
                                'source': url
                            }
                    elif source_type == 'git':
                        latest_version = await self._fetch_git_version(url)
                        if latest_version and latest_version != recipe.version:
                            updates[recipe.name] = {
                                'current': recipe.version,
                                'latest': latest_version,
                                'source': url
                            }
                    else:
                        warn(f'Unknown update source type: {source_type}')
                except Exception as e:
                    warn(f'Failed to check update for {recipe.name}: {e}')
        return updates

    async def _fetch_url(self, url: str):
        """Busca o conteúdo de uma URL de forma assíncrona."""
        async with requests.get(url, timeout=5) as r:
            r.raise_for_status()
            return r

    async def _parse_version(self, r, url: str, recipe) -> str:
        """Tenta extrair a versão de uma página HTML."""
        if 'html' in r.headers.get('Content-Type', ''):
            soup = BeautifulSoup(r.text, 'html.parser')
            latest_version = None
            for tag in soup.find_all():
                text = tag.get_text().strip()
                if text.startswith(recipe.name) and any(c.isdigit() for c in text):
                    latest_version = text.split()[-1]
                    break
            if latest_version:
                return latest_version
            else:
                warn(f'Could not detect version for {recipe.name} at {url}')
        else:
            return r.text.strip()

    async def _fetch_git_version(self, url: str) -> str:
        """Obtém a última tag de um repositório Git remoto."""
        out = await self._run_git_command(['git', 'ls-remote', '--tags', url])
        tags = [line.split('/')[-1] for line in out.splitlines() if 'refs/tags/' in line]
        if tags:
            return sorted(tags, reverse=True)[0]
        return None

    async def _run_git_command(self, command: list) -> str:
        """Executa um comando Git e retorna a saída."""
        process = await asyncio.create_subprocess_exec(*command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            raise Exception(f'Git command failed: {stderr.decode()}')
        return stdout.decode()

# Teste rápido
if __name__ == '__main__':
    updater = Updater()
    updates = asyncio.run(updater.check_updates())
    if updates:
        for name, info_dict in updates.items():
            print(f'{name}: current {info_dict["current"]}, latest {info_dict["latest"]}, source {info_dict["source"]}')
    else:
        print('All packages up to date')
