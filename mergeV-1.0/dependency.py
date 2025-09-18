import os
from typing import List, Dict, Optional
from recipe import Recipe, list_recipes
from uses import UseManager
from logs import info, warn, error
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
import re

class Version:
    """Classe simples para comparação de versões."""
    def __init__(self, version: str):
        self.parts = [int(p) for p in re.findall(r'\d+', version)]

    def __lt__(self, other: 'Version'):
        return self.parts < other.parts

    def __le__(self, other: 'Version'):
        return self.parts <= other.parts

    def __eq__(self, other: 'Version'):
        return self.parts == other.parts

    def __str__(self):
        return '.'.join(map(str, self.parts))

class DependencyManager:
    def __init__(self):
        self.recipes: Dict[str, Recipe] = {r.name: r for r in list_recipes()}
        self.use_manager = UseManager()

    @lru_cache(maxsize=None)
    def resolve_dependencies(
        self, package_name: str, build: bool = True, required_version: Optional[str] = None
    ) -> List[str]:
        """
        Resolve todas as dependências de um pacote, considerando versões e flags USE.
        """
        if package_name not in self.recipes:
            error(f'Pacote {package_name} não encontrado nas receitas')
            return []

        resolved: List[str] = []
        visited: set = set()

        def _resolve(pkg: str, version: Optional[str]):
            if pkg in visited:
                return
            visited.add(pkg)

            r = self.recipes.get(pkg)
            if not r:
                warn(f'Dependência {pkg} não encontrada nas receitas')
                return

            # Verifica versão
            if version and hasattr(r, 'version'):
                rv = Version(r.version)
                req_v = Version(version)
                if rv < req_v:
                    warn(f'{pkg} versão {rv} não atende requisito {req_v}')
                    return

            # Dependências básicas
            deps = r.dependencies.get('build' if build else 'runtime', [])

            # Dependências de flags USE
            active_flags = self.use_manager.get_flags(pkg)
            for flag in active_flags:
                deps.extend(r.dependencies.get(flag, []))

            for d in deps:
                if isinstance(d, tuple):
                    dep_name, dep_version = d
                else:
                    dep_name, dep_version = d, None
                _resolve(dep_name, dep_version)

            resolved.append(f"{pkg}-{getattr(r, 'version', 'N/A')}")

        _resolve(package_name, required_version)
        info(f'Dependências resolvidas para {package_name}: {resolved}')
        return resolved

    def get_dependency_tree(
        self, package_name: str, build: bool = True, level: int = 0
    ) -> str:
        """
        Retorna árvore de dependências formatada, mostrando versões e flags USE.
        """
        tree_str: str = ''
        if package_name not in self.recipes:
            return f'Pacote {package_name} não encontrado\n'

        visited: set = set()

        def _tree(pkg: str, indent: int):
            nonlocal tree_str
            r = self.recipes.get(pkg)
            version = getattr(r, 'version', 'N/A')
            active_flags = ','.join(self.use_manager.get_flags(pkg))
            tree_str += ' ' * indent + f'- {pkg}-{version} [USE: {active_flags}]\n'
            visited.add(pkg)

            deps = r.dependencies.get('build', []) + r.dependencies.get('runtime', [])
            for flag in self.use_manager.get_flags(pkg):
                deps.extend(r.dependencies.get(flag, []))
            for d in deps:
                dep_name = d[0] if isinstance(d, tuple) else d
                if dep_name not in visited:
                    _tree(dep_name, indent + 2)

        _tree(package_name, level)
        return tree_str

    def resolve_dependencies_parallel(
        self, package_names: List[str], build: bool = True
    ) -> Dict[str, List[str]]:
        """
        Resolve dependências de múltiplos pacotes em paralelo.
        """
        with ThreadPoolExecutor() as executor:
            results = executor.map(lambda pkg: (pkg, self.resolve_dependencies(pkg, build)), package_names)
        return dict(results)

# Exemplo de uso
if __name__ == '__main__':
    dm = DependencyManager()
    pkg = 'foo'  # pacote de teste
    print('Lista de dependências:')
    print(dm.resolve_dependencies(pkg))
    print('\nÁrvore de dependências:')
    print(dm.get_dependency_tree(pkg))

    # Paralelo
    packages = ['foo', 'bar', 'baz']
    parallel_deps = dm.resolve_dependencies_parallel(packages)
    print('\nDependências paralelas:')
    for k, v in parallel_deps.items():
        print(f'{k}: {v}')
