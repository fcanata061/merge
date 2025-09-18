import os
import hashlib
import time
import subprocess
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from logs import info, warn, error, stage, debug
from sandbox import Sandbox
from hooks import HooksManager
from recipe import Recipe

class Downloader:
    def __init__(self, build_dir: str, sandbox: Sandbox, hooks: HooksManager, max_workers: int = 4):
        self.build_dir = build_dir
        self.sandbox = sandbox
        self.hooks = hooks
        self.max_workers = max_workers
        os.makedirs(self.build_dir, exist_ok=True)

    # ===============================
    # Utilitário para checksum
    # ===============================
    def checksum(self, file_path: str, algo: str = 'sha256') -> str:
        hash_func = hashlib.new(algo)
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hash_func.update(chunk)
        return hash_func.hexdigest()

    # ===============================
    # Download HTTP/S com retries
    # ===============================
    def _download_http(self, uri: str, dest_path: str, checksum: str = None):
        if os.path.exists(dest_path):
            if checksum and self.checksum(dest_path) == checksum:
                info(f'{os.path.basename(dest_path)} já existe e checksum confere, pulando')
                return dest_path
            else:
                warn(f'{os.path.basename(dest_path)} existe mas checksum não confere, baixando novamente')
                os.remove(dest_path)

        retries = 3
        backoff = 2
        while retries > 0:
            try:
                stage(f'Downloading {os.path.basename(dest_path)}...')
                r = requests.get(uri, stream=True, timeout=15)
                r.raise_for_status()
                with open(dest_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                if checksum and self.checksum(dest_path) != checksum:
                    raise RuntimeError("Checksum não confere após download")
                info(f'Download concluído: {os.path.basename(dest_path)}')
                return dest_path
            except Exception as e:
                error(f'Falha ao baixar {uri}: {e}, tentativas restantes: {retries-1}')
                retries -= 1
                time.sleep(backoff)
                backoff *= 2
        raise RuntimeError(f"Falha no download de {uri} após múltiplas tentativas")

    # ===============================
    # Clone/atualiza repositório Git
    # ===============================
    def _clone_git(self, uri: str, dest_path: str):
        if os.path.exists(dest_path):
            stage(f'Atualizando repositório {uri}...')
            try:
                subprocess.run(['git', '-C', dest_path, 'pull'], check=True)
                info(f'Repositório atualizado: {uri}')
            except subprocess.CalledProcessError as e:
                error(f'Erro ao atualizar {uri}: {e}')
                raise
        else:
            stage(f'Clonando {uri}...')
            try:
                subprocess.run(['git', 'clone', uri, dest_path], check=True)
                info(f'Repositório clonado: {uri}')
            except subprocess.CalledProcessError as e:
                error(f'Erro ao clonar {uri}: {e}')
                raise

    # ===============================
    # Download principal
    # ===============================
    def download(self, recipe: Recipe):
        downloaded_files = []
        futures = {}
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            for uri in recipe.src_uri:
                filename = os.path.basename(urlparse(uri).path)
                dest_path = os.path.join(self.build_dir, filename)
                sandbox_dir = self.sandbox.create(prefix=f"sandbox_dl_{filename}_")

                # hooks pre-download
                import asyncio
                asyncio.run(self.hooks.run_hooks(recipe.name, "pre_download", cwd=sandbox_dir))

                # Escolhe método de download
                if uri.startswith(('http://', 'https://')):
                    futures[executor.submit(self._download_http, uri, dest_path, getattr(recipe, 'checksum', None))] = filename
                elif uri.endswith('.git') or uri.startswith(('git://', 'ssh://')):
                    futures[executor.submit(self._clone_git, uri, dest_path)] = filename
                else:
                    warn(f'URI desconhecida: {uri}, ignorando')

                # hooks post-download
                asyncio.run(self.hooks.run_hooks(recipe.name, "post_download", cwd=sandbox_dir))

            for future in as_completed(futures):
                try:
                    result = future.result()
                    downloaded_files.append(result)
                except Exception as e:
                    error(f"Falha no download de {futures[future]}: {e}")

        return downloaded_files
