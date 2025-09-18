import os
import zipfile
import tarfile
import concurrent.futures

# Bibliotecas externas para 7z e RAR
try:
    import py7zr
except ImportError:
    py7zr = None

try:
    import rarfile
except ImportError:
    rarfile = None

# Logs do gerenciador
def info(msg):
    print(f"[INFO] {msg}")

def warn(msg):
    print(f"[WARN] {msg}")

def error(msg):
    print(f"[ERROR] {msg}")

class Recipe:
    def __init__(self, name, files):
        """
        name: Nome do programa
        files: Lista de arquivos a extrair
        """
        self.name = name
        self.files = files  # Lista de tuples (caminho_arquivo, destino)

class Extractor:
    def __init__(self, recipe):
        self.recipe = recipe

    def extract_file(self, file_path, dest_dir):
        if not os.path.exists(file_path):
            error(f"Arquivo não encontrado: {file_path}")
            return
        os.makedirs(dest_dir, exist_ok=True)

        try:
            if file_path.endswith('.zip'):
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
                    return
                with py7zr.SevenZipFile(file_path, mode='r') as archive:
                    archive.extractall(path=dest_dir)
                info(f"Extraído 7z: {file_path}")
            elif file_path.endswith('.rar'):
                if rarfile is None:
                    error("rarfile não instalado, não é possível extrair RAR")
                    return
                with rarfile.RarFile(file_path) as archive:
                    archive.extractall(path=dest_dir)
                info(f"Extraído RAR: {file_path}")
            else:
                warn(f"Formato não suportado: {file_path}")
        except Exception as e:
            error(f"Erro ao extrair {file_path}: {e}")

    def extract_all_parallel(self):
        """
        Extrai todos os arquivos da receita em paralelo
        """
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
    # Definindo uma receita de exemplo
    recipe = Recipe(
        name="ProgramaExemplo",
        files=[
            ("exemplo.zip", "./extraidos/zip"),
            ("exemplo.tar.gz", "./extraidos/tar"),
            ("exemplo.7z", "./extraidos/7z"),
            ("exemplo.rar", "./extraidos/rar"),
        ]
    )

    extractor = Extractor(recipe)
    extractor.extract_all_parallel()
