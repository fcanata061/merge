import asyncio
from recipe import list_recipes
from install import Installer
from update import Updater
from logs import stage, info, warn, error
from typing import Optional, Callable

class Upgrader:
    def __init__(self, install_prefix: str = '/usr/local', dry_run: bool = False):
        self.updater = Updater()
        self.installer = Installer(install_prefix=install_prefix)
        self.dry_run = dry_run

    async def interactive_upgrade(self, pre_hook: Optional[Callable] = None, post_hook: Optional[Callable] = None):
        """Interativa para atualizar pacotes com suporte a hooks."""
        updates = await self.updater.check_updates()
        if not updates:
            info('Todos os pacotes estão atualizados.')
            return

        stage('Pacotes com atualizações disponíveis:')
        for idx, (name, info_dict) in enumerate(updates.items(), start=1):
            print(f'{idx}. {name}: atual {info_dict["current"]}, última {info_dict["latest"]}')

        print('\nDigite os números dos pacotes para atualizar separados por espaço (ou "all" para atualizar todos):')
        choice = input('> ').strip()

        if choice.lower() == 'all':
            to_upgrade = list(updates.keys())
        else:
            try:
                indexes = [int(x) - 1 for x in choice.split()]
                to_upgrade = [list(updates.keys())[i] for i in indexes if 0 <= i < len(updates)]
            except Exception as e:
                error(f'Entrada inválida: {e}')
                return

        if pre_hook:
            await self._maybe_async_hook(pre_hook)

        for pkg_name in to_upgrade:
            info(f'Atualizando {pkg_name}...')
            recipes = {r.name: r for r in list_recipes()}
            recipe = recipes.get(pkg_name)
            if not recipe:
                warn(f'Receita não encontrada para {pkg_name}, ignorando.')
                continue

            if await self.installer.install_recipe(recipe):
                info(f'{pkg_name} atualizado com sucesso.')
            else:
                error(f'Falha ao atualizar {pkg_name}.')

        if post_hook:
            await self._maybe_async_hook(post_hook)

    async def _maybe_async_hook(self, hook: Optional[Callable]):
        """Executa hook que pode ser sync ou async."""
        if hook:
            if asyncio.iscoroutinefunction(hook):
                await hook()
            else:
                hook()

# Teste rápido
if __name__ == '__main__':
    upgrader = Upgrader()
    asyncio.run(upgrader.interactive_upgrade())
