import os
from typing import List, Dict
from recipe import Recipe, list_recipes
from uses import UseManager
from logs import info, warn, error
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

class DependencyManager:
    def __init__(self):
        self.recipes = {r.name: r for r in list_recipes()}
        self.use_manager = UseManager()

    @lru_cache(maxsize=None)
    def resolve_dependencies(self, package_name: str, build: bool = True) -> List[str]:
        """Resolve todas as dependências de um pacote, incluindo flags USE e evitando duplicatas."""
        if package_name not in self.recipes:
            error(f'Pacote {package_name} não encontrado nas receitas')
            return []

        resolved = []
        visited = set()

        def _resolve(pkg: str):
            if pkg in visited:
                return
            visited.add(pkg)
            r = self.recipes.get(pkg)
            if not r:
                warn(f'Dependência {pkg} não encontrada nas receitas')
                return

            # Resolve dependências de build ou runtime
            deps = r.dependencies.get('build' if build else 'runtime', [])

            # Considera as flags USE ativas
            active_flags = self.use_manager.get_flags(pkg)
            for flag in active_flags:
                flag_deps = r.dependencies.get(flag, [])
                deps.extend(flag_deps)

            for d in deps:
                _resolve(d)
            resolved.append(pkg)

        _resolve(package_name)
        info(f'Dependências resolvidas para {package_name}: {resolved}')
        return resolved

    def get_dependency_tree(self, package_name: str, build: bool = True, level: int = 0) -> str:
        """Retorna uma string formatada mostrando a árvore de dependências."""
        tree_str = ''
        if package_name not in self.recipes:
            return f'Pacote {package_name} não encontrado nas receitas\n'

        visited = set()

        def _tree(pkg: str, indent: int):
            nonlocal tree_str
            tree_str += ' ' * indent + f'- {pkg}\n'
            visited.add(pkg)
            r = self.recipes.get(pkg)
            if not r:
                return
            deps = r.dependencies.get('build' if build else 'runtime', [])
            active_flags = self.use_manager.get_flags(pkg)
            for flag in active_flags:
                deps.extend(r.dependencies.get(flag, []))
            for d in deps:
                if d not in visited:
                    _tree(d, indent + 1)

        _tree(package_name, level)
        return tree_str

    def resolve_dependencies_parallel(self, package_names: List[str], build: bool = True) -> Dict[str, List[str]]:
        """Resolve dependências de múltiplos pacotes em paralelo."""
        with ThreadPoolExecutor() as executor:
            results = executor.map(lambda pkg: (pkg, self.resolve_dependencies(pkg, build)), package_names)
        return dict(results)

# Teste rápido
if __name__ == '__main__':
    dm = DependencyManager()
    deps = dm.resolve_dependencies('foo')
    print('Lista de dependências:', deps)
    print('\nÁrvore de dependências:')
    print(dm.get_dependency_tree('foo'))
