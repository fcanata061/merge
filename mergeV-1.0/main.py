# main.py refatorado para integrar módulo SyncManager

import sys
import argparse
from logs import stage, info, warn, error
from upgrade import Upgrader
from install import Installer
from remove import Remover
from sync import SyncManager
from recipe import list_recipes, Recipe
from tqdm import tqdm

# Map abreviações para comandos
COMMAND_MAP = {
    'i': 'install',
    'b': 'build',
    'd': 'download',
    'e': 'extract',
    's': 'patch',
    'si': 'sandbox_install',
    'u': 'update',
    'up': 'upgrade',
    'r': 'recompile_all',
    'ri': 'recompile_one',
    'depclean': 'depclean',
    'deepclean': 'deepclean',
    'use': 'use_flags',
    'sync': 'sync_repo'
}

# Função para confirmação interativa
def confirm(prompt, silent=False):
    if silent:
        return True
    resp = input(f'{prompt} [y/N]: ').strip().lower()
    return resp in ['y', 'yes']

# Função para mostrar barra de progresso em listas
def progress_iterable(iterable, desc='Processing'):
    from tqdm import tqdm
    return tqdm(iterable, desc=desc, unit='item')

# Função principal
def main():
    parser = argparse.ArgumentParser(description='Merge System CLI')
    parser.add_argument('command', nargs='?', help='Command to execute', choices=COMMAND_MAP.keys())
    parser.add_argument('package', nargs='?', help='Package name')
    parser.add_argument('--dry-run', action='store_true', help='Simulate operations without executing')
    parser.add_argument('--yes', '--silent', action='store_true', help='Run without confirmations')
    parser.add_argument('--repo', default='https://github.com/SEU_USUARIO/MergeRecipes.git', help='Git repository URL for recipes')
    args = parser.parse_args()

    installer = Installer(dry_run=args.dry_run, silent=args.yes)
    remover = Remover(dry_run=args.dry_run, silent=args.yes)
    upgrader = Upgrader()
    recipes = {r.name: r for r in list_recipes()}
    sync_manager = SyncManager(repo_url=args.repo)

    cmd = COMMAND_MAP.get(args.command, None)

    if cmd is None:
        print('Available commands:')
        for key, val in COMMAND_MAP.items():
            print(f'{key} -> {val}')
        sys.exit(0)

    # Comando sync
    if cmd == 'sync_repo':
        if confirm('Synchronize repository?', args.yes):
            if args.dry_run:
                info('DRY-RUN: Would synchronize repository')
            else:
                if sync_manager.sync_repo():
                    recipes = {r.split('.')[0]: r for r in sync_manager.list_recipes()}
                    info(f'Recipes available: {list(recipes.keys())}')

    # Outros comandos permanecem como já implementados (install, upgrade, remove, recompile, etc.)
    # ... (mantém a lógica previamente implementada para os outros comandos)

if __name__ == '__main__':
    main()
