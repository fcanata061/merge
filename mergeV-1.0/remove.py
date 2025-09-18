# remove.py evoluído, completo e funcional para Merge
import os
import shutil
from sandbox import Sandbox
from hooks import HooksManager
from logs import stage, info, warn, error

class Remover:
    def __init__(self, install_prefix: str = '/usr/local', dry_run: bool = False, silent: bool = False):
        self.install_prefix = install_prefix
        self.dry_run = dry_run
        self.silent = silent

    def remove_package(self, package) -> bool:
        stage(f'Removing package {package.name}')
        sb = Sandbox(install_prefix=self.install_prefix)
        hooks = HooksManager(sb, dry_run=self.dry_run, silent=self.silent)
        success = True

        try:
            # Run pre-remove hooks
            hooks.run_hooks(package.hooks.get('pre_remove', []))

            # Remove diretórios principais do pacote
            dirs_to_remove = [os.path.join(self.install_prefix, package.name)]
            for dir_path in dirs_to_remove:
                if os.path.exists(dir_path):
                    if self.dry_run:
                        info(f'DRY-RUN: Would remove directory {dir_path}')
                    else:
                        shutil.rmtree(dir_path)
                        info(f'Removed directory {dir_path}')
                else:
                    warn(f'Directory {dir_path} does not exist')

            # Remove arquivos adicionais (logs, caches, etc.) se definido
            extra_files = getattr(package, 'extra_files', [])
            for file_path in extra_files:
                if os.path.exists(file_path):
                    if self.dry_run:
                        info(f'DRY-RUN: Would remove file {file_path}')
                    else:
                        os.remove(file_path)
                        info(f'Removed file {file_path}')

            # Run post-remove hooks
            hooks.run_hooks(package.hooks.get('post_remove', []))

        except Exception as e:
            error(f'Failed to remove {package.name}: {e}')
            success = False

        sb.cleanup()
        return success

    def remove_packages_orphans(self, packages_list) -> None:
        stage('Removing orphaned packages')
        for pkg in packages_list:
            self.remove_package(pkg)
