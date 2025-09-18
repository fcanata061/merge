import os
import sys
import asyncio
import hashlib
import yaml
import json
from typing import Optional, Callable, List, Dict

# ----------------------------
# Logs simples para demonstração
# ----------------------------
def stage(msg: str):
    print(f"[STAGE] {msg}")

def info(msg: str):
    print(f"[INFO] {msg}")

def warn(msg: str):
    print(f"[WARN] {msg}")

def error(msg: str):
    print(f"[ERROR] {msg}")

# ----------------------------
# Mock de recipes, installer e updater
# ----------------------------
class Recipe:
    def __init__(self, name, file_path):
        self.name = name
        self.file_path = file_path

def list_recipes() -> List[Recipe]:
    # Exemplo: lista receitas mockadas
    recipes_dir = os.path.expanduser("~/.merge/recipes")
    os.makedirs(recipes_dir, exist_ok=True)
    return [Recipe(f"pkg{i}", os.path.join(recipes_dir, f"pkg{i}.txt")) for i in range(1, 4)]

class Installer:
    async def install_recipe(self, recipe: Recipe) -> bool:
        # Mock: simula instalação com delay
        await asyncio.sleep(0.2)
        info(f"Instalando {recipe.name} (simulado)")
        return True

class Updater:
    async def check_updates(self) -> Dict[str, dict]:
        # Mock: simula pacotes desatualizados
        return {r.name: {"current": "1.0", "latest": "1.1"} for r in list_recipes()}

# ----------------------------
# SyncManager simplificado
# ----------------------------
class SyncManager:
    def __init__(self, repos: List[dict], dry_run: bool = False):
        self.repos = repos
        self.dry_run = dry_run

    async def sync_all(self):
        tasks = [self._sync_repo(repo) for repo in self.repos]
        await asyncio.gather(*tasks)

    async def _sync_repo(self, repo: dict):
        url = repo.get("url", "unknown")
        local_dir = repo.get("local_dir", os.path.expanduser("~/.merge/repo"))
        stage(f"Sincronizando {url} em {local_dir}")
        if self.dry_run:
            info(f"DRY-RUN: Clonaria/atualizaria {url}")
            return
        # Mock delay para simular git clone/pull
        await asyncio.sleep(0.2)
        info(f"{url} sincronizado com sucesso (simulado)")

# ----------------------------
# MergeManager Ultimate
# ----------------------------
class MergeManager:
    def __init__(self, config_path: str, dry_run: bool = False, retries: int = 3, cache_file: str = None):
        self.dry_run = dry_run
        self.retries = retries
        self.config_path = config_path
        self.installer = Installer()
        self.updater = Updater()
        self.cache_file = cache_file or os.path.expanduser("~/.merge/cache_hash.json")
        self.file_cache: Dict[str, str] = self._load_cache()

    # ----------------------------
    # Cache de hash
    # ----------------------------
    def _load_cache(self) -> Dict[str, str]:
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                warn("Falha ao carregar cache, iniciando vazio")
        return {}

    def _save_cache(self):
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(self.file_cache, f, indent=2)

    def _file_hash(self, path: str) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()

    # ----------------------------
    # Sincronização de repositórios
    # ----------------------------
    async def sync_repositories(self, repos: List[dict]):
        sync_manager = SyncManager(repos, dry_run=self.dry_run)
        await sync_manager.sync_all()

    # ----------------------------
    # Atualização de pacotes
    # ----------------------------
    async def upgrade_packages(self, packages: Optional[List[str]] = None,
                               pre_hook: Optional[Callable] = None,
                               post_hook: Optional[Callable] = None):
        updates = await self.updater.check_updates()
        if not updates:
            info("Todos os pacotes estão atualizados")
            return

        if packages is None:
            packages = list(updates.keys())

        if pre_hook:
            await self._maybe_async_hook(pre_hook)

        tasks = [self._upgrade_package(pkg, updates[pkg]) for pkg in packages if pkg in updates]
        await asyncio.gather(*tasks)

        if post_hook:
            await self._maybe_async_hook(post_hook)

        self._save_cache()

    async def _upgrade_package(self, pkg_name: str, info_dict: dict):
        recipes = {r.name: r for r in list_recipes()}
        recipe = recipes.get(pkg_name)
        if not recipe:
            warn(f"Receita não encontrada para {pkg_name}, ignorando.")
            return

        for attempt in range(1, self.retries + 1):
            try:
                stage(f"Atualizando {pkg_name} (tentativa {attempt})")
                recipe_path = recipe.file_path
                recipe_hash = self._file_hash(recipe_path)
                if self.file_cache.get(pkg_name) == recipe_hash:
                    info(f"{pkg_name} não mudou desde a última atualização, pulando")
                    return

                if self.dry_run:
                    info(f"DRY-RUN: Instalaria {pkg_name}")
                    self.file_cache[pkg_name] = recipe_hash
                    return

                success = await self.installer.install_recipe(recipe)
                if success:
                    info(f"{pkg_name} atualizado com sucesso")
                    self.file_cache[pkg_name] = recipe_hash
                else:
                    raise Exception("Falha desconhecida na instalação")
                break
            except Exception as e:
                warn(f"Tentativa {attempt} falhou para {pkg_name}: {e}")
                if attempt == self.retries:
                    error(f"Não foi possível atualizar {pkg_name} após {self.retries} tentativas")

    # ----------------------------
    # Configuração externa
    # ----------------------------
    async def upgrade_from_config(self):
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config {self.config_path} não encontrado")

        with open(self.config_path, "r", encoding="utf-8") as f:
            if self.config_path.endswith((".yaml", ".yml")):
                config = yaml.safe_load(f)
            else:
                config = json.load(f)

        repos = config.get("repos")
        packages = config.get("packages")
        pre_hook = config.get("pre_hook")
        post_hook = config.get("post_hook")

        if repos:
            await self.sync_repositories(repos)

        await self.upgrade_packages(packages, pre_hook, post_hook)

    # ----------------------------
    # Hooks sync/async
    # ----------------------------
    async def _maybe_async_hook(self, hook: Optional[Callable]):
        if hook:
            if asyncio.iscoroutinefunction(hook):
                await hook()
            else:
                hook()

# ----------------------------
# Execução direta
# ----------------------------
if __name__ == "__main__":
    config_path = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/.merge/config.yaml")
    manager = MergeManager(config_path=config_path, dry_run=False)
    asyncio.run(manager.upgrade_from_config())
