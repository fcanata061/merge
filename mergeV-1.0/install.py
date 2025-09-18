import os
from recipe import Recipe
from download import Downloader
from extract import Extractor
from patch import PatchApplier
from sandbox import Sandbox
from logs import stage, info, error

class Installer:
    def __init__(self, install_prefix: str = '/usr/local'):
        self.downloader = Downloader()
        self.extractor = Extractor()
        self.install_prefix = install_prefix

    def install_recipe(self, recipe: Recipe, build_commands: list = None) -> bool:
        stage(f'Starting installation for recipe {recipe.name}')
        # 1. Download
        downloaded_files = self.downloader.download(recipe)
        if not downloaded_files:
            error(f'Failed to download any files for {recipe.name}')
            return False

        # 2. Extract
        extracted_dirs = self.extractor.extract_recipe(recipe)
        if not extracted_dirs:
            error(f'Failed to extract any files for {recipe.name}')
            return False

        # 3. Apply patches
        patcher = PatchApplier(build_dir=os.path.commonpath(extracted_dirs))
        patcher.apply_recipe_patches(recipe, extracted_dirs)

        # 4. Sandbox build and install
        sb = Sandbox(install_prefix=self.install_prefix)
        success = True
        for dir_path in extracted_dirs:
            if not sb.build_and_install(dir_path, build_commands=build_commands):
                success = False
                break

        sb.cleanup()

        if success:
            info(f'Recipe {recipe.name} installed successfully')
        else:
            error(f'Recipe {recipe.name} failed to install')

        return success

# Teste rápido
if __name__ == '__main__':
    from recipe import Recipe
    test_recipe = Recipe(os.path.expanduser('~/.merge/repo/foo.yaml'))
    installer = Installer()
    installer.install_recipe(test_recipe)
