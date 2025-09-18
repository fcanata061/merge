import asyncio
import yaml
import json
from typing import Optional, Callable, List
from logs import stage, info, warn, error
from recipe import list_recipes
from install import Installer
from update import Updater
from sync_v2 import SyncManager

class UpgraderV3:
    def __init__(self, install_prefix: str = '/usr/local', dry_run: bool = False, retries: int = 3):
        self.updater = Updater()
        self.installer = Installer(install_prefix=install_prefix)
        self.dry_run = dry_run
        self.retries = retries

    async def upgrade_packages(self, packages: Optional[List[str]] = None, pre_hook: Optional[Callable] = None,
                               post_hook: Optional[Callable] = None):
        """Atualiza pacotes especificados ou todos desatualizados."""
        updates = await self.updater.check_updates()
        if not updates:
            info('Todos os pacotes estão atualizados.')
            return

        if not packages:
            packages = list(updates.keys())

        if pre_hook:
            await self._maybe_async_hook(pre_hook)

        tasks = [self._upgrade_package(pkg, updates[pkg]) for pkg in packages if pkg in updates]
        await asyncio.gather(*tasks)

        if post_hook:
            await self._maybe_async_hook(post_hook)

    async def _upgrade_package(self, pkg_name: str, info_dict: dict):
        recipes = {r.name: r for r in list_recipes()}
        recipe = recipes.get(pkg_name)
        if not recipe:
            warn(f'Receita não encontrada para {pkg_name}, ignorando.')
            return

        for attempt in range(1, self.retries + 1):
            try:
                stage(f'Atualizando {pkg_name} (tentativa {attempt})')
                if self.dry_run:
                    info(f'DRY-RUN: Instalaria {pkg_name}')
                    return
                success = await self.installer.install_recipe(recipe)
                if success:
                    info(f'{pkg_name} atualizado com sucesso.')
                else:
                    raise Exception('Falha desconhecida na instalação')
                break
            except Exception as e:
                warn(f'Tentativa {attempt} falhou para {pkg_name}: {e}')
                if attempt == self.retries:
                    error(f'Não foi possível atualizar {pkg_name} após {self.retries} tentativas')

    async def upgrade_from_config(self, path: str):
        """Carrega configuração YAML/JSON para atualizar pacotes e repositórios."""
        if not path or not os.path.exists(path):
            raise FileNotFoundError(f'Config {path} não encontrado')
        with open(path, 'r', encoding='utf-8') as f:
            if path.endswith(('.yaml', '.yml')):
                config = yaml.safe_load(f)
            else:
                config = json.load(f)

        # Sincroniza repositórios se definidos
        repos = config.get('repos')
        if repos:
            sync_manager = SyncManager(repos, dry_run=self.dry_run)
            await sync_manager.sync_all()

        # Atualiza pacotes
        packages = config.get('packages')
        pre_hook = config.get('pre_hook')
        post_hook = config.get('post_hook')
        await self.upgrade_packages(packages=packages, pre_hook=pre_hook, post_hook=post_hook)

    async def _maybe_async_hook(self, hook: Optional[Callable]):
        if hook:
            if asyncio.iscoroutinefunction(hook):
                await hook()
            else:
                hook()

# Execução rápida
if __name__ == '__main__':
    import os
    upgrader = UpgraderV3(dry_run=True)  # True para testar sem alterações
    config_file = os.path.expanduser('~/.merge/config_upgrade.yaml')
    asyncio.run(upgrader.upgrade_from_config(config_file))
