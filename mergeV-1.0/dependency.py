import re
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from recipe import Recipe, list_recipes
from uses import UseManager
from logs import info, warn, error

class Version:
    """Classe para manipulação e comparação de versões."""
    def __init__(self, version: str):
        self.parts = [int(p) for p in re.findall(r'\d+', version)]

    def __lt__(self, other: 'Version'): return self.parts < other.parts
    def __le__(self, other: 'Version'): return self.parts <= other.parts
    def __eq__(self, other: 'Version'): return self.parts == other.parts
    def __ge__(self, other: 'Version'): return self.parts >= other.parts
    def __gt__(self, other: 'Version'): return self.parts > other.parts
    def __str__(self): return '.'.join(map(str, self.parts))

class DependencyManager:
    def __init__(self):
        self.recipes: Dict[str, Recipe] = {r.name: r for r in list_recipes()}
        self.use_manager = UseManager()

    @lru_cache(maxsize=None)
    def resolve_dependencies(
        self,
        package_name: str,
        build: bool = True,
        required_version: Optional[str] = None,
        resolved_versions: Optional[Dict[str, str]] = None,
        version_constraints: Optional[Dict[str, List[str]]] = None
    ) -> List[str]:
        """Resolve dependências com suporte a versões, flags USE e resolução automática de conflitos."""
        if resolved_versions is None:
            resolved_versions = {}
        if version_constraints is None:
            version_constraints = {}

        if package_name not in self.recipes:
            error(f'Pacote {package_name} não encontrado')
            return []

        resolved: List[str] = []
        visited: set = set()

        def _check_version(current: str, constraints: List[str]) -> bool:
            for required in constraints:
                if not required:
                    continue
                m = re.match(r'(>=|<=|==)?\s*([\d\.]+)', required)
                if not m:
                    warn(f'Formato de versão inválido: {required}')
                    continue
                op, ver = m.groups()
                op = op or '=='
                pkg_version = Version(current)
                req_version = Version(ver)
                if op == '==': satisfied = pkg_version == req_version
                elif op == '>=': satisfied = pkg_version >= req_version
                elif op == '<=': satisfied = pkg_version <= req_version
                else: satisfied = True
                if not satisfied:
                    return False
            return True

        def _resolve(pkg: str, version_constraint: Optional[str]):
            if pkg in visited:
                if version_constraint:
                    version_constraints[pkg].append(version_constraint)
                    r = self.recipes[pkg]
                    current_version = Version(resolved_versions[pkg])
                    best_version = current_version
                    for constr in version_constraints[pkg]:
                        m = re.match(r'(>=|<=|==)?\s*([\d\.]+)', constr)
                        if m:
                            op, ver = m.groups()
                            ver_obj = Version(ver)
                            if op == '>=' and ver_obj > current_version:
                                best_version = ver
                            elif op == '<=' and ver_obj < current_version:
                                best_version = ver
                            elif op == '==' and ver_obj != current_version:
                                warn(f'Impossível satisfazer {pkg} {constr}, mantendo {current_version}')
                    resolved_versions[pkg] = best_version
                return

            visited.add(pkg)
            r = self.recipes.get(pkg)
            if not r:
                warn(f'Dependência {pkg} não encontrada')
                return

            version_constraints.setdefault(pkg, [])
            if version_constraint:
                version_constraints[pkg].append(version_constraint)

            if pkg in resolved_versions:
                current_version = resolved_versions[pkg]
                if not _check_version(current_version, version_constraints[pkg]):
                    warn(f'Conflito detectado em {pkg}, mantendo {current_version}')
            else:
                resolved_versions[pkg] = r.version

            deps = r.dependencies.get('build' if build else 'runtime', [])
            active_flags = self.use_manager.get_flags(pkg)
            for flag in active_flags:
                deps.extend(r.dependencies.get(flag, []))

            for d in deps:
                if isinstance(d, tuple):
                    dep_name, dep_version = d
                else:
                    dep_name, dep_version = d, None
                _resolve(dep_name, dep_version)

            resolved.append(f"{pkg}-{resolved_versions[pkg]}")

        _resolve(package_name, required_version)
        info(f'Dependências resolvidas para {package_name}: {resolved}')
        return resolved

    def suggest_final_versions(self, packages: List[str], build: bool = True) -> Dict[str, str]:
        """Sugere versão final de cada pacote para instalação, resolvendo conflitos."""
        final_versions: Dict[str, str] = {}
        for pkg in packages:
            self.resolve_dependencies(pkg, build, resolved_versions=final_versions)
        return final_versions

    def get_installation_plan(self, packages: List[str], build: bool = True) -> List[str]:
        """
        Gera plano de instalação sequencial:
        - Dependências instaladas antes dos pacotes que dependem delas.
        """
        final_versions = self.suggest_final_versions(packages, build)
        installed = set()
        plan = []

        def _add_pkg(pkg: str):
            if pkg in installed:
                return
            r = self.recipes.get(pkg)
            if not r:
                warn(f'Dependência {pkg} não encontrada')
                return
            deps = r.dependencies.get('build' if build else 'runtime', [])
            active_flags = self.use_manager.get_flags(pkg)
            for flag in active_flags:
                deps.extend(r.dependencies.get(flag, []))
            for d in deps:
                dep_name = d[0] if isinstance(d, tuple) else d
                _add_pkg(dep_name)
            installed.add(pkg)
            plan.append(f"{pkg}-{final_versions[pkg]}")

        for pkg in packages:
            _add_pkg(pkg)

        return plan

    def get_dependency_tree(self, package_name: str, build: bool = True, level: int = 0) -> str:
        tree_str = ''
        if package_name not in self.recipes:
            return f'Pacote {package_name} não encontrado\n'
        visited = set()
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

    def resolve_dependencies_parallel(self, package_names: List[str], build: bool = True) -> Dict[str, List[str]]:
        with ThreadPoolExecutor() as executor:
            results = executor.map(lambda pkg: (pkg, self.resolve_dependencies(pkg, build)), package_names)
        return dict(results)


# Exemplo de uso
if __name__ == '__main__':
    dm = DependencyManager()
    packages = ['foo', 'bar', 'baz']

    print('Versões finais sugeridas:')
    final_versions = dm.suggest_final_versions(packages)
    for pkg, ver in final_versions.items():
        print(f'{pkg}: {ver}')

    print('\nPlano de instalação sequencial:')
    plan = dm.get_installation_plan(packages)
    for p in plan:
        print(p)

    print('\nÁrvore de dependências:')
    print(dm.get_dependency_tree('foo'))

    print('\nDependências resolvidas em paralelo:')
    parallel_deps = dm.resolve_dependencies_parallel(packages)
    for k, v in parallel_deps.items():
        print(f'{k}: {v}')
