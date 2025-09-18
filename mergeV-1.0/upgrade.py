import sys
from update import Updater
from install import Installer
from logs import stage, info, warn, error

class Upgrader:
    def __init__(self, install_prefix: str = '/usr/local'):
        self.updater = Updater()
        self.installer = Installer(install_prefix=install_prefix)

    def interactive_upgrade(self):
        updates = self.updater.check_updates()
        if not updates:
            info('All packages are up to date')
            return

        stage('Packages with updates available:')
        for idx, (name, info_dict) in enumerate(updates.items(), start=1):
            print(f'{idx}. {name}: current {info_dict["current"]}, latest {info_dict["latest"]}')

        print('\nEnter numbers of packages to upgrade separated by space (or "all" to upgrade everything):')
        choice = input('> ').strip()

        if choice.lower() == 'all':
            to_upgrade = list(updates.keys())
        else:
            try:
                indexes = [int(x) - 1 for x in choice.split()]
                to_upgrade = [list(updates.keys())[i] for i in indexes if 0 <= i < len(updates)]
            except Exception as e:
                error(f'Invalid input: {e}')
                return

        for pkg_name in to_upgrade:
            info(f'Upgrading {pkg_name}...')
            # Carrega a receita novamente para instalação
            from recipe import list_recipes
            recipes = {r.name: r for r in list_recipes()}
            recipe = recipes.get(pkg_name)
            if not recipe:
                warn(f'Recipe not found for {pkg_name}, skipping')
                continue
            if self.installer.install_recipe(recipe):
                info(f'{pkg_name} upgraded successfully')
            else:
                error(f'Failed to upgrade {pkg_name}')

# Teste rápido
if __name__ == '__main__':
    upgrader = Upgrader()
    upgrader.interactive_upgrade()
