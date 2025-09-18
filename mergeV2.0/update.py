import os
import shutil
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from dependency import DependencyResolver
from rootdir import get_install_root
from install import Installer
from remove import Remover
from hooks import run_hooks
import logs


class Updater:
    def __init__(self, resolver: DependencyResolver, max_workers: int = 4):
        self.resolver = resolver
        self.installer = Installer()
        self.remover = Remover(resolver, max_workers=max_workers)
        self.max_workers = max_workers
        self.updated = {}
        self.transaction_stack = []

    # ===============================
    # Transações e rollback
    # ===============================
    def start_transaction(self):
        self.transaction_stack.append(self.updated.copy())
        logs.debug("Transação de atualização iniciada.")

    def commit(self):
        if self.transaction_stack:
            self.transaction_stack.pop()
        logs.debug("Transação de atualização confirmada.")

    def rollback(self):
        if self.transaction_stack:
            previous_state = self.transaction_stack.pop()
            current_updated = set(self.updated) - set(previous_state)
            install_root = get_install_root()
            for pkg in current_updated:
                logs.info(f"Rollback: {pkg} pode precisar reinstalar manualmente")
            self.updated = previous_state
            logs.debug("Rollback de atualização concluído.")

    # ===============================
    # Atualização principal
    # ===============================
    def update(self, package: str = None, world: bool = False):
        """
        Atualiza um pacote específico ou todo o sistema (world)
        """
        self.start_transaction()
        install_root = get_install_root()
        packages_to_update = []

        if world:
            packages_to_update = list(self.resolver.graph.recipes.keys())
        elif package:
            packages_to_update = [package]
        else:
            logs.warning("Nenhum pacote especificado para atualização.")
            return False

        futures = {}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            for pkg in packages_to_update:
                futures[executor.submit(self._update_package, pkg, install_root)] = pkg

            for future in as_completed(futures):
                pkg = futures[future]
                try:
                    success = future.result()
                    if not success:
                        raise RuntimeError(f"Falha na atualização de {pkg}")
                except Exception as e:
                    logs.error(f"Erro crítico durante atualização: {e}")
                    self.rollback()
                    return False

        self.commit()
        return True

    # ===============================
    # Atualização de um único pacote
    # ===============================
    def _update_package(self, pkg: str, install_root: str) -> bool:
        logs.info(f"==> Atualizando {pkg} dentro do sandbox")

        try:
            # Hooks pré-atualização
            run_hooks("pre_update", pkg)

            # Remover versão antiga no sandbox
            if pkg in self.resolver.graph.recipes:
                old_pkg_path = os.path.join(install_root, pkg)
                if os.path.exists(old_pkg_path):
                    logs.info(f"Removendo versão antiga de {pkg}")
                    self.remover._remove_package(pkg, install_root)

            # Instalar nova versão no sandbox
            recipe = self.resolver.graph.recipes.get(pkg)
            if recipe:
                self.installer.register_recipe(recipe)
                success = self.installer._install_package(recipe, install_root)
                if not success:
                    raise RuntimeError(f"Falha na instalação de {pkg} durante update")
                self.updated[pkg] = recipe.version

            # Hooks pós-atualização
            run_hooks("post_update", pkg)
            logs.success(f"{pkg} atualizado com sucesso!")
            return True

        except Exception as e:
            logs.error(f"Erro durante atualização de {pkg}: {e}")
            return False

    # ===============================
    # Métodos auxiliares
    # ===============================
    def list_updated(self):
        """Lista pacotes atualizados na sessão"""
        return self.updated

    def explain_update(self, package: str):
        """Mostra dependências e por que o pacote será atualizado"""
        self.resolver.explain(package)
