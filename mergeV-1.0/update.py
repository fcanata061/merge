import os
import requests
from recipe import list_recipes, Recipe
from logs import stage, info, warn
from bs4 import BeautifulSoup

class Updater:
    def __init__(self):
        self.recipes = list_recipes()

    def check_updates(self) -> dict:
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
                        r = requests.get(url, timeout=5)
                        r.raise_for_status()
                        # Se for página HTML, tenta extrair versão com BeautifulSoup
                        if 'html' in r.headers.get('Content-Type', ''):
                            soup = BeautifulSoup(r.text, 'html.parser')
                            # Busca por elementos que contenham a versão, heurística simples
                            latest_version = None
                            for tag in soup.find_all():
                                text = tag.get_text().strip()
                                if text.startswith(recipe.name) and any(c.isdigit() for c in text):
                                    latest_version = text.split()[-1]
                                    break
                            if not latest_version:
                                warn(f'Could not detect version for {recipe.name} at {url}')
                                continue
                        else:
                            latest_version = r.text.strip()

                        if latest_version != recipe.version:
                            updates[recipe.name] = {
                                'current': recipe.version,
                                'latest': latest_version,
                                'source': url
                            }
                    elif source_type == 'git':
                        # Para repositórios git, pega a última tag
                        from subprocess import check_output
                        out = check_output(['git', 'ls-remote', '--tags', url]).decode()
                        tags = [line.split('/')[-1] for line in out.splitlines() if 'refs/tags/' in line]
                        if tags:
                            latest_version = sorted(tags, reverse=True)[0]
                            if latest_version != recipe.version:
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

# Teste rápido
if __name__ == '__main__':
    updater = Updater()
    updates = updater.check_updates()
    if updates:
        for name, info_dict in updates.items():
            print(f'{name}: current {info_dict["current"]}, latest {info_dict["latest"]}, source {info_dict["source"]}')
    else:
        print('All packages up to date')
