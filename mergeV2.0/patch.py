import os
import subprocess
import asyncio
from recipe import Recipe
from logs import info, warn, error, stage

class PatchApplier:
    def __init__(self, build_dir: str):
        self.build_dir = build_dir

    async def apply_patch(self, patch_file: str, target_dir: str, dry_run: bool = False) -> bool:
        """
        Aplica um patch a um diretório alvo.
        :param patch_file: Caminho para o arquivo patch.
        :param target_dir: Diretório onde aplicar o patch.
        :param dry_run: Se True, simula a aplicação sem modificar arquivos.
        :return: True se aplicado com sucesso, False caso contrário.
        """
        if not os.path.exists(patch_file):
            warn(f'Patch file not found: {patch_file}')
            return False
        if not os.path.exists(target_dir):
            warn(f'Target directory not found for patch: {target_dir}')
            return False

        stage(f'Applying patch {os.path.basename(patch_file)} to {target_dir}')

        cmd = ['patch', '-p1', '-i', patch_file]
        if dry_run:
            cmd.append('--dry-run')

        try:
            # subprocess.run dentro de thread para não bloquear asyncio
            result = await asyncio.to_thread(subprocess.run, cmd, cwd=target_dir, capture_output=True, text=True)
            
            if result.returncode == 0:
                info(f'Patch {patch_file} applied successfully')
                return True
            else:
                error(f'Failed to apply patch {patch_file}: {result.stderr.strip()}')
                return False
        except Exception as e:
            error(f'Exception while applying patch {patch_file}: {e}')
            return False

    async def apply_recipe_patches(self, recipe: Recipe, extracted_dirs: list, dry_run: bool = False) -> list:
        """
        Aplica todos os patches de uma receita aos diretórios extraídos.
        :param recipe: Objeto Recipe contendo patches.
        :param extracted_dirs: Lista de diretórios extraídos.
        :param dry_run: Se True, simula a aplicação sem modificar arquivos.
        :return: Lista de patches aplicados com sucesso.
        """
        applied = []
        for patch_file in recipe.patches:
            for dir_path in extracted_dirs:
                patch_path = os.path.join(dir_path, patch_file)
                if await self.apply_patch(patch_path, dir_path, dry_run=dry_run):
                    applied.append(patch_path)
        return applied

# ==========================
# Teste rápido (compatível)
# ==========================
if __name__ == '__main__':
    from recipe import Recipe
    from config import BUILD_DIR

    test_recipe = Recipe(os.path.expanduser('~/.merge/repo/foo.yaml'))
    pa = PatchApplier(BUILD_DIR)
    extracted_dirs = [os.path.join(BUILD_DIR, 'foo_extracted')]

    # Aplica patches normalmente
    applied = asyncio.run(pa.apply_recipe_patches(test_recipe, extracted_dirs))
    print('Applied patches:', applied)

    # Exemplo de dry-run
    # applied_dry = asyncio.run(pa.apply_recipe_patches(test_recipe, extracted_dirs, dry_run=True))
    # print('Dry-run applied patches:', applied_dry)
