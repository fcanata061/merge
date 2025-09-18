# main.py - CLI completo e funcional do Merge

import sys
import argparse
from logs import stage, info, warn, error
from upgrade import Upgrader
from install import Installer
from remove import Remover
from sync import SyncManager
from rootdir import RootDirManager
from recipe import list_recipes, Recipe
from merge_autocomplete import setup_autocomplete
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
    'sync': 'sync_repo',
    'pr': 'prepare_rootdir',
    'ls': 'list_recipes'
}

# Função de confirmação interativa
def confirm(prompt, silent=False):
    if silent:
        return True
    resp = input(f'{prompt} [y/N]: ').strip().lower()
    return resp in ['y', 'yes']

# Função para barra de progresso
def progress_iterable(iterable, desc='Processing'):
    return tqdm(iterable, desc=desc, unit='item')

def main():
    parser = argparse.ArgumentParser(description='Merge System CLI')
    parser.add_argument('command', nargs='?', help='Command to execute', choices=COMMAND_MAP.keys())
    parser.add_argument('package', nargs='?', help='Package name')
    parser.add_argument('--dry-run', action='store_true', help='Simulate operations without executing')
    parser.add_argument('--yes', '--silent', action='store_true', help='Run without confirmations')
    parser.add_argument('--repo', default='https://github.com/SEU_USUARIO/MergeRecipes.git', help='Git repository URL for recipes')
    parser.add_argument('--rootdir', default='/mnt/merge-root', help='Rootdir for chroot preparation')
    args = parser.parse_args()

    # Inicializando módulos
    installer = Installer(dry_run=args.dry_run, silent=args.yes)
    remover = Remover(dry_run=args.dry_run, silent=args.yes)
    upgrader = Upgrader(dry_run=args.dry_run, silent=args.yes)
    sync_manager = SyncManager(repo_url=args.repo)
    rootdir_manager = RootDirManager(rootdir=args.rootdir, dry_run=args.dry_run, silent=args.yes)
    recipes = {r.name: r for r in list_recipes()}

    # Configurar autocompletar
    setup_autocomplete(COMMAND_MAP, recipes)

    cmd = COMMAND_MAP.get(args.command, None)

    if cmd is None:
        print('Available commands:')
        for key, val in COMMAND_MAP.items():
            print(f'{key} -> {val}')
        sys.exit(0)

    # Listar receitas
    if cmd == 'list_recipes':
        info('Available recipes:')
        for pkg in recipes:
            print(f'- {pkg}')
        return

    # Comando: sync
    if cmd == 'sync_repo':
        if confirm('Synchronize repository?', args.yes):
            if args.dry_run:
                info('DRY-RUN: Would synchronize repository')
            else:
                if sync_manager.sync_repo():
                    recipes = {r.split('.')[0]: r for r in sync_manager.list_recipes()}
                    info(f'Recipes available: {list(recipes.keys())}')

    # Comando: prepare_rootdir
    elif cmd == 'prepare_rootdir':
        if confirm(f'Prepare rootdir at {rootdir_manager.rootdir}?', args.yes):
            rootdir_manager.prepare_rootdir()

    # Comando: install
    elif cmd == 'install':
        if args.package not in recipes:
            error(f'Package {args.package} not found')
            sys.exit(1)
        for _ in progress_iterable([recipes[args.package]], desc='Installing package'):
            installer.install_recipe(recipes[args.package].recipe)

    # Comando: remove
    elif cmd == 'recompile_one' or cmd == 'remove':
        if args.package not in recipes:
            error(f'Package {args.package} not found')
            sys.exit(1)
        for _ in progress_iterable([recipes[args.package]], desc='Removing package'):
            remover.remove_package(recipes[args.package].recipe)

    # Comando: upgrade
    elif cmd == 'upgrade':
        if args.package:
            if args.package not in recipes:
                error(f'Package {args.package} not found')
                sys.exit(1)
            upgrader.upgrade_package(recipes[args.package].recipe)
        else:
            upgrader.upgrade_all(recipes.values())

    # Comando: update (lista novas versões disponíveis)
    elif cmd == 'update':
        upgrader.list_updates(recipes.values())

    # Outros comandos
    elif cmd in ['build', 'download', 'extract', 'patch', 'sandbox_install', 'depclean', 'deepclean', 'use_flags', 'recompile_all']:
        info(f'Command {cmd} is recognized but must be implemented in respective module')

    else:
        warn(f'Command {cmd} not implemented in CLI')

if __name__ == '__main__':
    main()
