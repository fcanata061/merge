# main.py - CLI completo do Merge com barra de progresso, dry-run, modo silencioso e autocompletar

import sys
import argparse
from logs import stage, info, warn, error
from upgrade import Upgrader
from install import Installer
from remove import Remover
from sync import SyncManager
from rootdir import RootDirManager
from recipe import list_recipes, Recipe
from tqdm import tqdm
import readline

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
    'pr': 'prepare_rootdir'
}

# Função de confirmação interativa
def confirm(prompt, silent=False):
    if silent:
        return True
    resp = input(f'{prompt} [y/N]: ').strip().lower()
    return resp in ['y', 'yes']

# Função para barra de progresso em listas
def progress_iterable(iterable, desc='Processing'):
    return tqdm(iterable, desc=desc, unit='item')

# Autocomplete para nomes de pacotes
def completer(text, state):
    options = [pkg for pkg in COMMAND_MAP.keys()] + [pkg for pkg in list(recipes.keys())]
    matches = [s for s in options if s.startswith(text)]
    if state < len(matches):
        return matches[state]
    else:
        return None

readline.parse_and_bind('tab: complete')
readline.set_completer(completer)

def main():
    global recipes
    parser = argparse.ArgumentParser(description='Merge System CLI')
    parser.add_argument('command', nargs='?', help='Command to execute', choices=COMMAND_MAP.keys())
    parser.add_argument('package', nargs='?', help='Package name')
    parser.add_argument('--dry-run', action='store_true', help='Simulate operations without executing')
    parser.add_argument('--yes', '--silent', action='store_true', help='Run without confirmations')
    parser.add_argument('--repo', default='https://github.com/SEU_USUARIO/MergeRecipes.git', help='Git repository URL for recipes')
    parser.add_argument('--rootdir', default='/mnt/merge-root', help='Rootdir for chroot preparation')
    args = parser.parse_args()

    cmd = COMMAND_MAP.get(args.command, None)

    if cmd is None:
        print('Available commands:')
        for key, val in COMMAND_MAP.items():
            print(f'{key} -> {val}')
        sys.exit(0)

    # Inicializando módulos
    installer = Installer(dry_run=args.dry_run, silent=args.yes)
    remover = Remover(dry_run=args.dry_run, silent=args.yes)
    upgrader = Upgrader()
    sync_manager = SyncManager(repo_url=args.repo)
    rootdir_manager = RootDirManager(rootdir=args.rootdir, dry_run=args.dry_run, silent=args.yes)
    recipes = {r.name: r for r in list_recipes()}

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

    else:
        warn(f'Command {cmd} is recognized but not implemented in this CLI version')

if __name__ == '__main__':
    main()
