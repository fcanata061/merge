import os
import subprocess
import requests
from urllib.parse import urlparse
from recipe import Recipe
from config import BUILD_DIR
from logs import info, warn, error, stage

class Downloader:
    def __init__(self, build_dir: str = BUILD_DIR):
        self.build_dir = build_dir
        os.makedirs(self.build_dir, exist_ok=True)

    def download(self, recipe: Recipe) -> list:
        downloaded_files = []
        for uri in recipe.src_uri:
            parsed = urlparse(uri)
            filename = os.path.basename(parsed.path)
            dest_path = os.path.join(self.build_dir, filename)

            if parsed.scheme in ['http', 'https']:
                if not os.path.exists(dest_path):
                    stage(f'Downloading {filename}...')
                    try:
                        r = requests.get(uri, stream=True)
                        r.raise_for_status()
                        with open(dest_path, 'wb') as f:
                            for chunk in r.iter_content(chunk_size=8192):
                                f.write(chunk)
                        info(f'Downloaded {filename}')
                    except requests.RequestException as e:
                        error(f'Failed to download {uri}: {e}')
                        continue
                else:
                    info(f'{filename} already exists, skipping')

            elif parsed.scheme in ['git', 'ssh'] or uri.endswith('.git'):
                if not os.path.exists(dest_path):
                    stage(f'Cloning {uri}...')
                    try:
                        subprocess.run(['git', 'clone', uri, dest_path], check=True)
                        info(f'Cloned {uri}')
                    except subprocess.CalledProcessError as e:
                        error(f'Failed to clone {uri}: {e}')
                        continue
                else:
                    info(f'{filename} already cloned, skipping')

            else:
                warn(f'Unknown URI scheme: {uri}, skipping')
                continue

            downloaded_files.append(dest_path)

        return downloaded_files

# Teste rápido
if __name__ == '__main__':
    from recipe import Recipe
    test_recipe = Recipe(os.path.expanduser('~/.merge/repo/foo.yaml'))
    dl = Downloader()
    files = dl.download(test_recipe)
    print('Downloaded files:', files)
