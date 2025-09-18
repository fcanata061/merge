import os
import zipfile
import tarfile
import concurrent.futures
import hashlib
from sandbox import Sandbox
from hooks import HooksManager
from logs import info, warn, error, debug

# Bibliotecas externas
try:
    import py7zr
except ImportError:
    py7zr = None

try:
    import rarfile
except ImportError:
    rarfile = None

class Recipe:
    def __init__(self, name, files):
        """
        name: Nome do programa
        files: Lista de arquivos a extrair [(arquivo, destino)]
        """
        self.name = name
        self.files = files

class Extractor:
    def __init__(self, recipe: Recipe, sandbox: Sandbox, hooks: HooksManager):
        self.recipe = recipe
        self.sandbox = sandbox
        self.hooks = hooks

    def _checksum_file(self, path, algo="sha256"):
        if not os.path.exists(path):
            return None
        h = hashlib.new(algo)
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    def extract_file(self, file_path, dest_dir):
        if not os.path.exists(file_path):
            error(f"Arquivo não encontrado: {file_path}")
            return False

        sandbox_dir = self.sandbox.create(prefix=f"sandbox_extract_")
        os.makedirs(dest_dir, exist_ok=True)

        # Hooks pré-extract
        import asyncio
        asyncio.run(self.hooks.run_hooks(self.recipe.name, "pre_extract", cwd=sandbox_dir))

        try:
            if file_path.endswith(".zip"):
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(dest_dir)
                info(f"Extraído ZIP: {file_path}")

            elif file_path.endswith(('.tar', '.tar.gz', '.tar.bz2')):
                with tarfile.open(file_path, 'r:*') as tar_ref:
                    tar_ref.extractall(dest_dir)
                info(f"Extraído TAR: {file_path}")

            elif file_path.endswith('.7z'):
                if py7zr is None:
                    error("py7zr não instalado, não é possível extrair 7z")
                    return False
                with py7zr.SevenZipFile(file_path, mode='r') as archive:
                    archive.extractall(path=dest_dir)
                info(f"Extraído 7z: {file_path}")

            elif file_path.endswith('.rar'):
                if rarfile is None:
                    error("rarfile não instalado, não é possível extrair RAR")
                    return False
                with rarfile.RarFile(file_path) as archive:
                    archive.extractall(path=dest_dir)
                info(f"Extraído RAR: {file_path}")

            else:
                warn(f"Formato não suportado: {file_path}")
                return False

            # Hooks pós-extract
            asyncio.run(self.hooks.run_hooks(self.recipe.name, "post_extract", cwd=sandbox_dir))
            debug(f"Extração concluída para: {file_path}")
            return True

        except Exception as e:
            error(f"Erro ao extrair {file_path}: {e}")
            return False

    def extract_all_parallel(self):
        if not hasattr(self.recipe, 'files') or not self.recipe.files:
            warn("Nenhum arquivo definido na receita para extrair")
            return

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []
            for file_path, dest_dir in self.recipe.files:
                futures.append(executor.submit(self.extract_file, file_path, dest_dir))
            concurrent.futures.wait(futures)

        info(f"Extração concluída para {self.recipe.name}")

# Exemplo de uso integrado
if __name__ == "__main__":
    from hooks import HooksManager
    from sandbox import Sandbox

    sandbox = Sandbox()
    hooks = HooksManager()

    recipe = Recipe(
        name="ProgramaExemplo",
        files=[
            ("exemplo.zip", "./extraidos/zip"),
            ("exemplo.tar.gz", "./extraidos/tar"),
            ("exemplo.7z", "./extraidos/7z"),
            ("exemplo.rar", "./extraidos/rar"),
        ]
    )

    extractor = Extractor(recipe, sandbox, hooks)
    extractor.extract_all_parallel()
