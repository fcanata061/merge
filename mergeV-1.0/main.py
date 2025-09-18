import sys
from logs import stage, info, warn, error
from upgrade import Upgrader
from install import Installer
from recipe import list_recipes, Recipe
import subprocess

MENU = '''
Merge System Main Menu:
1. Check for updates
2. Upgrade packages
3. Install a package
4. Recompile entire system
5. Recompile single package
6. Sync repository to Git
0. Exit
'''

def main():
    installer = Installer()
    upgrader = Upgrader()

    while True:
        print(MENU)
        choice = input('Select an option: ').strip()
        if choice == '0':
            info('Exiting...')
            sys.exit(0)

        elif choice == '1':
            from update import Updater
            updater = Updater()
            updates = updater.check_updates()
            if updates:
                for name, info_dict in updates.items():
                    print(f'{name}: current {info_dict["current"]}, latest {info_dict["latest"]}')
            else:
                info('All packages up to date')

        elif choice == '2':
            upgrader.interactive_upgrade()

        elif choice == '3':
            recipes = {r.name: r for r in list_recipes()}
            print('Available packages:')
            for name in recipes.keys():
                print(f'- {name}')
            pkg_name = input('Enter package name to install: ').strip()
            recipe = recipes.get(pkg_name)
            if recipe:
                installer.install_recipe(recipe)
            else:
                warn(f'Package {pkg_name} not found')

        elif choice == '4':
            info('Recompiling entire system...')
            recipes = list_recipes()
            for recipe in recipes:
                info(f'Installing {recipe.name}...')
                installer.install_recipe(recipe)

        elif choice == '5':
            recipes = {r.name: r for r in list_recipes()}
            print('Available packages:')
            for name in recipes.keys():
                print(f'- {name}')
            pkg_name = input('Enter package name to recompile: ').strip()
            recipe = recipes.get(pkg_name)
            if recipe:
                info(f'Recompiling {pkg_name}...')
                installer.install_recipe(recipe)
            else:
                warn(f'Package {pkg_name} not found')

        elif choice == '6':
            info('Syncing repository to Git...')
            try:
                subprocess.run(['git', 'add', '.'], check=True)
                subprocess.run(['git', 'commit', '-m', 'Sync from merge system'], check=True)
                subprocess.run(['git', 'push'], check=True)
                info('Repository synced successfully')
            except subprocess.CalledProcessError as e:
                error(f'Git sync failed: {e}')

        else:
            warn('Invalid choice, try again')

if __name__ == '__main__':
    main()
