# hooks.py - Módulo central para gerenciar todos os hooks do Merge

from sandbox import Sandbox
from logs import info, warn, error

class HooksManager:
    def __init__(self, sandbox: Sandbox, dry_run: bool = False, silent: bool = False):
        self.sandbox = sandbox
        self.dry_run = dry_run
        self.silent = silent

    def run_hooks(self, hooks_list):
        for cmd in hooks_list:
            if self.dry_run:
                info(f'DRY-RUN: Would execute hook: {cmd}')
            else:
                try:
                    self.sandbox.run_command(cmd.split())
                except Exception as e:
                    error(f'Hook command failed: {cmd} | {e}')

    def run_all_hooks(self, recipe):
        # Hooks de build e instalação
        self.run_hooks(recipe.hooks.get('pre_configure', []))
        self.run_hooks(recipe.hooks.get('post_configure', []))
        self.run_hooks(recipe.hooks.get('pre_compile', []))
        self.run_hooks(recipe.hooks.get('post_compile', []))
        self.run_hooks(recipe.hooks.get('pre_install', []))
        self.run_hooks(recipe.hooks.get('post_install', []))

    def run_remove_hooks(self, package):
        # Hooks de remoção
        self.run_hooks(package.hooks.get('pre_remove', []))
        self.run_hooks(package.hooks.get('post_remove', []))
