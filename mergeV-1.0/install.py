import os
import subprocess
import asyncio
from recipe import Recipe
from download import Downloader
from extract import Extractor
from patch import PatchApplier
from sandbox import Sandbox
from hooks import HooksManager
from logs import stage, info, error

class Installer:
    def __init__(self, install_prefix: str = '/usr/local', dry_run: bool = False, silent: bool = False, log_level: str = 'INFO'):
        self.downloader = Downloader()
        self.extractor = Extractor()
        self.install_prefix = install_prefix
        self.dry_run = dry_run
        self.silent = silent
        self.log_level = log_level

    async def install_recipe(self, recipe: Recipe, build_commands: list = None) -> bool:
        stage(f'Iniciando instalação da receita {recipe.name}')
        # 1. Download
        downloaded_files = self.downloader.download(recipe)
        if not downloaded_files:
            error(f'Falha ao baixar arquivos para {recipe.name}')
            return False

        # 2. Extract
        extracted_dirs = self.extractor.extract_recipe(recipe)
        if not extracted_dirs:
            error(f'Falha ao extrair arquivos para {recipe.name}')
            return False

        # 3. Apply patches
        patcher = PatchApplier(build_dir=os.path.commonpath(extracted_dirs))
        patcher.apply_recipe_patches(recipe, extracted_dirs)

        # 4. Sandbox build and install
        sb = Sandbox(install_prefix=self.install_prefix)
        hooks = HooksManager(sb, dry_run=self.dry_run, silent=self.silent, log_level=self.log_level)
        success = True

        for dir_path in extracted_dirs:
            try:
                # Run pre-configure hooks
                await hooks.run_hooks(recipe.hooks.get('pre_configure', []))

                # Build/Compile inside sandbox
                if build_commands:
                    for cmd in build_commands:
                        if self.dry_run:
                            info(f'DRY-RUN: Executaria o comando de build: {cmd}')
                        else:
                            await sb.run_command(cmd.split(), cwd=dir_path)

                # Run post-configure hooks
                await hooks.run_hooks(recipe.hooks.get('post_configure', []))
                await hooks.run_hooks(recipe.hooks.get('pre_compile', []))

                # Assuming make install or similar
                await sb.build_and_install(dir_path, build_commands=build_commands)

                # Run post-compile hooks
                await hooks.run_hooks(recipe.hooks.get('post_compile', []))

                # Run pre/post install hooks
                await hooks.run_hooks(recipe.hooks.get('pre_install', []))
                await hooks.run_hooks(recipe.hooks.get('post_install', []))

            except Exception as e:
                error(f'Instalação falhou para {recipe.name} em {dir_path}: {e}')
                success = False
                break

        await sb.cleanup()
        return success
