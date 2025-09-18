# install.py refatorado com suporte completo a hooks

import os
from recipe import Recipe
from download import Downloader
from extract import Extractor
from patch import PatchApplier
from sandbox import Sandbox
from hooks import HooksManager
from logs import stage, info, error

class Installer:
    def __init__(self, install_prefix: str = '/usr/local', dry_run: bool = False, silent: bool = False):
        self.downloader = Downloader()
        self.extractor = Extractor()
        self.install_prefix = install_prefix
        self.dry_run = dry_run
        self.silent = silent

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
        hooks = HooksManager(sb, dry_run=self.dry_run, silent=self.silent)
        success = True
        for dir_path in extracted_dirs:
            try:
                # Run pre-configure hooks
                hooks.run_hooks(recipe.hooks.get('pre_configure', []))

                # Build/Compile inside sandbox
                if build_commands:
                    for cmd in build_commands:
                        if self.dry_run:
                            info(f'DRY-RUN: Would execute build command: {cmd}')
                        else:
                            sb.run_command(cmd.split(), cwd=dir_path)

                # Run post-configure hooks
                hooks.run_hooks(recipe.hooks.get('post_configure', []))
                hooks.run_hooks(recipe.hooks.get('pre_compile', []))
                # Assuming make install or similar
                sb.build_and_install(dir_path, build_commands=build_commands)
                hooks.run_hooks(recipe.hooks.get('post_compile', []))

                # Run pre/post install hooks
                hooks.run_hooks(recipe.hooks.get('pre_install', []))
                hooks.run_hooks(recipe.hooks.get('post_install', []))

            except Exception as e:
                error(f'Installation failed for {recipe.name} in {dir_path}: {e}')
                success = False
                break

        sb.cleanup()
        return success
