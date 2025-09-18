import os
import shutil
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from dependency import DependencyResolver
from recipe import Recipe
from download import download_source
from extract import extract_source
from patch import apply_patches
from hooks import run_hooks
from sandbox import run_in_sandbox
from rootdir import get_install_root
import logs


class Installer:
    def __init__(self, max_workers: int = 4):
        self.resolver = DependencyResolver()
        self.installed = {}  # registro de pacotes instalados
        self.max_workers = max_workers
        self.transaction_stack = []

    # ===============================
    # Registro de pacotes e USE
    # ===============================
    def register_recipe(self, recipe: Recipe):
        self.resolver.add_recipe(recipe)

    def enable_use(self, flag: str):
        self.resolver.enable_use(flag)

    def define_profile(self, name: str, flags: list[str]):
        self.resolver.define_profile(name, flags)

    def activate_profile(self, name: str):
        self.resolver.activate_profile(name)

    # ===============================
    # Transações (rollback avançado)
    # ===============================
    def start_transaction(self):
        self.transaction_stack.append(self.installed.copy())
        logs.debug("Transação iniciada.")

    def commit(self):
        if self.transaction_stack:
            self.transaction_stack.pop()
        logs.debug("Transação confirmada.")

    def rollback(self):
        if self.transaction_stack:
            previous_state = self.transaction_stack.pop()
            current_installed = set(self.installed) - set(previous_state)
            install_root = get_install_root()
            for pkg in current_installed:
                pkg_path = os.path.join(install_root, pkg)
                if os.path.exists(pkg_path):
                    shutil.rmtree(pkg_path)
                    logs.info(f"Rollback: {pkg} removido")
            self.installed = previous_state
            logs.debug("Rollback concluído.")

    # ===============================
    # Instalação principal
    # ===============================
    def install(self, package: str, force: bool = False):
        """Resolve e instala pacotes e dependências com sandbox, paralelismo e rollback"""
        try:
            order = self.resolver.resolve(package)
        except Exception as e:
            logs.error(f"Falha ao resolver dependências de {package}: {e}")
            return False

        self.start_transaction()
        install_root = get_install_root()
        futures = {}
        results = {}

        # ===============================
        # Executor para paralelismo seguro
        # ===============================
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            for pkg in order:
                recipe: Recipe = self.resolver.graph.recipes[pkg]

                if pkg in self.installed and not force:
                    logs.info(f"{pkg}-{recipe.version} já instalado, pulando...")
                    continue

                futures[executor.submit(self._install_package, recipe, install_root)] = pkg

            for future in as_completed(futures):
                pkg = futures[future]
                try:
                    success = future.result()
                    results[pkg] = success
                    if not success:
                        raise RuntimeError(f"Falha na instalação de {pkg}")
                except Exception as e:
                    logs.error(f"Erro crítico durante instalação: {e}")
                    self.rollback()
                    return False

        self.commit()
        return True

    # ===============================
    # Instalação de um único pacote
    # ===============================
    def _install_package(self, recipe: Recipe, install_root: str) -> bool:
        logs.info(f"==> Instalando {recipe.name}-{recipe.version} dentro do sandbox")

        with tempfile.TemporaryDirectory(prefix=f"sandbox_{recipe.name}_") as sandbox_dir:
            try:
                # 1. Hooks pré-instalação
                run_hooks("pre_install", recipe, cwd=sandbox_dir)

                # 2. Download
                src_path = download_source(recipe, cwd=sandbox_dir)

                # 3. Extração
                build_dir = extract_source(src_path, recipe, cwd=sandbox_dir)

                # 4. Patches
                apply_patches(build_dir, recipe, cwd=sandbox_dir)

                # 5. Build
                if recipe.build:
                    run_in_sandbox(recipe.build, cwd=build_dir, env={"DESTDIR": sandbox_dir})

                # 6. Instalação
                if recipe.install:
                    run_in_sandbox(recipe.install, cwd=build_dir, env={"DESTDIR": sandbox_dir})
                else:
                    shutil.copytree(build_dir, os.path.join(sandbox_dir, recipe.name), dirs_exist_ok=True)

                # 7. Hooks pós-instalação
                run_hooks("post_install", recipe, cwd=sandbox_dir)

                # 8. Copia do sandbox para root final
                target_path = os.path.join(install_root, recipe.name)
                if os.path.exists(target_path):
                    shutil.rmtree(target_path)
                shutil.copytree(sandbox_dir, target_path, dirs_exist_ok=True)

                self.installed[recipe.name] = recipe.version
                logs.success(f"{recipe.name}-{recipe.version} instalado com sucesso!")
                return True

            except Exception as e:
                logs.error(f"Erro durante instalação de {recipe.name}: {e}")
                return False

    # ===============================
    # Métodos auxiliares
    # ===============================
    def list_installed(self):
        """Lista pacotes já instalados"""
        return self.installed

    def explain(self, package: str):
        """Mostra árvore de dependências do pacote"""
        self.resolver.explain(package)

    def why(self, package: str):
        """Mostra quem depende do pacote"""
        self.resolver.why(package)

    def find_orphans(self):
        """Lista pacotes que ninguém mais usa"""
        return self.resolver.find_orphans()
