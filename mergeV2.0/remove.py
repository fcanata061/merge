import os
import shutil
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from dependency import DependencyResolver
from rootdir import get_install_root
from hooks import run_hooks
import logs


class Remover:
    def __init__(self, resolver: DependencyResolver, max_workers: int = 4):
        self.resolver = resolver
        self.max_workers = max_workers
        self.removed = {}
        self.transaction_stack = []

    # ===============================
    # Transações e rollback
    # ===============================
    def start_transaction(self):
        self.transaction_stack.append(self.removed.copy())
        logs.debug("Transação de remoção iniciada.")

    def commit(self):
        if self.transaction_stack:
            self.transaction_stack.pop()
        logs.debug("Transação de remoção confirmada.")

    def rollback(self):
        if self.transaction_stack:
            previous_state = self.transaction_stack.pop()
            install_root = get_install_root()
            current_removed = set(self.removed) - set(previous_state)
            for pkg in current_removed:
                pkg_path = os.path.join(install_root, pkg)
                logs.info(f"Rollback: {pkg} não pode ser restaurado automaticamente.")
            self.removed = previous_state
            logs.debug("Rollback de remoção concluído.")

    # ===============================
    # Remoção principal
    # ===============================
    def remove(self, package: str, remove_orphans: bool = True):
        """Remove pacote e dependências órfãs com sandbox e rollback"""
        install_root = get_install_root()
        to_remove = self._compute_removal_list(package, remove_orphans)

        if not to_remove:
            logs.warning(f"Nenhum pacote encontrado para remover: {package}")
            return True

        self.start_transaction()
        futures = {}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            for pkg in to_remove:
                futures[executor.submit(self._remove_package, pkg, install_root)] = pkg

            for future in as_completed(futures):
                pkg = futures[future]
                try:
                    success = future.result()
                    if not success:
                        raise RuntimeError(f"Falha na remoção de {pkg}")
                except Exception as e:
                    logs.error(f"Erro crítico durante remoção: {e}")
                    self.rollback()
                    return False

        self.commit()
        return True

    # ===============================
    # Cálculo da lista de remoção
    # ===============================
    def _compute_removal_list(self, package: str, remove_orphans: bool):
        """Cria lista de pacotes a remover respeitando dependências"""
        to_remove = []
        visited = set()

        def dfs(pkg):
            if pkg in visited:
                return
            visited.add(pkg)
            dependents = self.resolver.graph.reverse_graph.get(pkg, [])
            if dependents:
                logs.warning(f"{pkg} não pode ser removido, ainda é dependência de {dependents}")
                return
            to_remove.append(pkg)
            # Verifica órfãos em cascata
            if remove_orphans:
                orphans = [p for p in self.resolver.find_orphans() if p not in to_remove]
                for orphan in orphans:
                    dfs(orphan)

        dfs(package)
        return to_remove

    # ===============================
    # Remoção de um único pacote
    # ===============================
    def _remove_package(self, pkg: str, install_root: str) -> bool:
        pkg_path = os.path.join(install_root, pkg)
        logs.info(f"==> Removendo {pkg} dentro do sandbox")

        if not os.path.exists(pkg_path):
            logs.warning(f"{pkg} não encontrado, pulando.")
            return True

        try:
            with tempfile.TemporaryDirectory(prefix=f"sandbox_remove_{pkg}_") as sandbox_dir:
                temp_path = os.path.join(sandbox_dir, pkg)
                shutil.copytree(pkg_path, temp_path)

                # Hooks pré-removal
                run_hooks("pre_remove", pkg, cwd=sandbox_dir)

                # Remoção real
                shutil.rmtree(pkg_path)
                self.removed[pkg] = True

                # Hooks pós-removal
                run_hooks("post_remove", pkg, cwd=sandbox_dir)

                logs.success(f"{pkg} removido com sucesso!")
            return True
        except Exception as e:
            logs.error(f"Erro durante remoção de {pkg}: {e}")
            return False

    # ===============================
    # Métodos auxiliares
    # ===============================
    def list_removed(self):
        """Lista pacotes removidos na sessão"""
        return self.removed

    def explain_removal(self, package: str):
        """Explica quem depende do pacote"""
        self.resolver.why(package)
