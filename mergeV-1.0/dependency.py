import os
from typing import List, Dict
from recipe import Recipe, list_recipes
from uses import UseManager
from logs import info, warn, error

class DependencyManager:
    def __init__(self):
        self.recipes = {r.name: r for r in list_recipes()}
        self.use_manager = UseManager()

    def resolve_dependencies(self, package_name: str, build: bool = True) -> List[str]:
        """Resolve all dependencies for a package including USE flags, avoiding duplicates."""
        if package_name not in self.recipes:
            error(f'Package {package_name} not found in recipes')
            return []

        resolved = []
        visited = set()

        def _resolve(pkg: str):
            if pkg in visited:
                return
            visited.add(pkg)

            r = self.recipes.get(pkg)
            if not r:
                warn(f'Dependency {pkg} not found in recipes')
                return

            # Resolve build or runtime deps
            deps = r.dependencies.get('build' if build else 'runtime', [])

            # Consider USE flags
            active_flags = self.use_manager.get_flags(pkg)
            for flag in active_flags:
                flag_deps = r.dependencies.get(flag, [])
                deps.extend(flag_deps)

            for d in deps:
                _resolve(d)

            resolved.append(pkg)

        _resolve(package_name)
        info(f'Resolved dependencies for {package_name}: {resolved}')
        return resolved

    def get_dependency_tree(self, package_name: str, build: bool = True, level: int = 0) -> str:
        """Returns a formatted string showing the dependency tree."""
        tree_str = ''
        if package_name not in self.recipes:
            return f'Package {package_name} not found in recipes\n'

        visited = set()

        def _tree(pkg: str, indent: int):
            nonlocal tree_str
            tree_str += '  ' * indent + f'- {pkg}\n'
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

# Teste rápido
if __name__ == '__main__':
    dm = DependencyManager()
    deps = dm.resolve_dependencies('foo')
    print('Dependencies list:', deps)
    print('\nDependency Tree:')
    print(dm.get_dependency_tree('foo'))
