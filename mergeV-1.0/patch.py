import os
import subprocess
from recipe import Recipe
from logs import info, warn, error, stage

class PatchApplier:
    def __init__(self, build_dir: str):
        self.build_dir = build_dir

    def apply_patch(self, patch_file: str, target_dir: str) -> bool:
        if not os.path.exists(patch_file):
            warn(f'Patch file not found: {patch_file}')
            return False
        if not os.path.exists(target_dir):
            warn(f'Target directory not found for patch: {target_dir}')
            return False
        stage(f'Applying patch {os.path.basename(patch_file)} to {target_dir}')
        try:
            subprocess.run(['patch', '-p1', '-i', patch_file], cwd=target_dir, check=True)
            info(f'Patch {patch_file} applied successfully')
            return True
        except subprocess.CalledProcessError as e:
            error(f'Failed to apply patch {patch_file}: {e}')
            return False

    def apply_recipe_patches(self, recipe: Recipe, extracted_dirs: list) -> list:
        applied = []
        for patch_file in recipe.patches:
            for dir_path in extracted_dirs:
                patch_path = os.path.join(dir_path, patch_file)
                if self.apply_patch(patch_path, dir_path):
                    applied.append(patch_path)
        return applied

# Teste rápido
if __name__ == '__main__':
    from recipe import Recipe
    test_recipe = Recipe(os.path.expanduser('~/.merge/repo/foo.yaml'))
    from config import BUILD_DIR
    pa = PatchApplier(BUILD_DIR)
    extracted_dirs = [os.path.join(BUILD_DIR, 'foo_extracted')]
    applied = pa.apply_recipe_patches(test_recipe, extracted_dirs)
    print('Applied patches:', applied)
