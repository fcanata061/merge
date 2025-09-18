import os
import tarfile
import zipfile
import shutil
from recipe import Recipe
from config import BUILD_DIR
from logs import info, warn, error, stage

class Extractor:
    def __init__(self, build_dir: str = BUILD_DIR):
        self.build_dir = build_dir

    def extract_file(self, file_path: str) -> str:
        dest_dir = os.path.join(self.build_dir, os.path.basename(file_path) + '_extracted')
        os.makedirs(dest_dir, exist_ok=True)
        try:
            if tarfile.is_tarfile(file_path):
                stage(f'Extracting tar file {file_path}...')
                with tarfile.open(file_path, 'r:*') as tar:
                    tar.extractall(path=dest_dir)
                info(f'Extracted {file_path}')
            elif zipfile.is_zipfile(file_path):
                stage(f'Extracting zip file {file_path}...')
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(dest_dir)
                info(f'Extracted {file_path}')
            else:
                warn(f'Unknown archive format for {file_path}, copying as is')
                shutil.copy(file_path, dest_dir)
        except Exception as e:
            error(f'Failed to extract {file_path}: {e}')
            return ''
        return dest_dir

    def extract_recipe(self, recipe: Recipe) -> list:
        extracted_dirs = []
        for uri in recipe.src_uri:
            filename = os.path.basename(uri)
            file_path = os.path.join(self.build_dir, filename)
            if os.path.exists(file_path):
                extracted_dirs.append(self.extract_file(file_path))
            else:
                warn(f'File {filename} not found for extraction')
        return extracted_dirs

# Teste rápido
if __name__ == '__main__':
    from recipe import Recipe
    test_recipe = Recipe(os.path.expanduser('~/.merge/repo/foo.yaml'))
    extractor = Extractor()
    dirs = extractor.extract_recipe(test_recipe)
    print('Extracted directories:', dirs)
