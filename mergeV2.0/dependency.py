from collections import defaultdict, deque
from typing import Dict, List, Set, Tuple, Optional
from packaging.version import Version, InvalidVersion
import concurrent.futures
from recipe import Recipe
from config import Config
import logs


class DependencyGraph:
    def __init__(self):
        self.graph: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
        self.recipes: Dict[str, Recipe] = {}
        self.use_flags: Set[str] = set()
        self.profiles: Dict[str, Set[str]] = {}
        self.reverse_graph: Dict[str, List[str]] = defaultdict(list)  # para "why()"
        self.cache: Dict[str, List[str]] = {}  # cache de resoluções

    # ===============================
    # Gestão de receitas e USE
    # ===============================
    def add_recipe(self, recipe: Recipe):
        self.recipes[recipe.name] = recipe
        logs.debug(f"Receita registrada: {recipe.name}-{recipe.version}")

    def enable_use(self, flag: str):
        self.use_flags.add(flag)
        logs.debug(f"USE flag ativada: {flag}")

    def define_profile(self, name: str, flags: List[str]):
        self.profiles[name] = set(flags)

    def activate_profile(self, name: str):
        if name not in self.profiles:
            raise ValueError(f"Perfil não encontrado: {name}")
        self.use_flags |= self.profiles[name]
        logs.info(f"Perfil ativado: {name} -> {self.profiles[name]}")

    # ===============================
    # Resolução de dependências
    # ===============================
    def _split_version(self, dep: str):
        for op in [">=", "<=", "=", ">", "<"]:
            if op in dep:
                name, ver = dep.split(op, 1)
                return name.strip(), op, ver.strip()
        return dep.strip(), None, None

    def _parse_dependency(self, dep: str) -> List[Tuple[str, Optional[str], Optional[str]]]:
        if "|" in dep:  # OR-deps
            return [self._split_version(p.strip()) for p in dep.split("|")]
        return [self._split_version(dep)]

    def _check_version(self, recipe: Recipe, op: Optional[str], ver: Optional[str]) -> bool:
        if not op or not ver:
            return True
        try:
            pkg_version = Version(recipe.version)
            dep_version = Version(ver)
        except InvalidVersion:
            return False
        return {
            ">=": pkg_version >= dep_version,
            "<=": pkg_version <= dep_version,
            "=": pkg_version == dep_version,
            ">": pkg_version > dep_version,
            "<": pkg_version < dep_version,
        }.get(op, False)

    def _check_conflicts(self, recipe: Recipe):
        for conflict in getattr(recipe, "conflicts", []):
            for name, op, ver in self._parse_dependency(conflict):
                if name in self.recipes:
                    dep_recipe = self.recipes[name]
                    if self._check_version(dep_recipe, op, ver):
                        raise RuntimeError(
                            f"Conflito: {recipe.name}-{recipe.version} não pode coexistir com "
                            f"{dep_recipe.name}-{dep_recipe.version}"
                        )

    def build(self, root: str):
        if root in self.cache:  # cache para evitar recomputar
            logs.debug(f"Usando cache para {root}")
            return self.cache[root]

        visited = set()

        def dfs(pkg_name: str):
            if pkg_name in visited:
                return
            visited.add(pkg_name)

            recipe = self.recipes.get(pkg_name)
            if not recipe:
                raise ValueError(f"Receita não encontrada: {pkg_name}")

            self._check_conflicts(recipe)

            def process_deps(dep_list, dtype: str):
                for dep in dep_list:
                    candidates = self._parse_dependency(dep)
                    chosen = None
                    for name, op, ver in candidates:
                        dep_recipe = self.recipes.get(name)
                        if dep_recipe and self._check_version(dep_recipe, op, ver):
                            chosen = name
                            break
                    if not chosen:
                        raise RuntimeError(f"Nenhuma dependência válida encontrada para {dep} exigida por {pkg_name}")
                    self.graph[pkg_name].append((chosen, dtype))
                    self.reverse_graph[chosen].append(pkg_name)
                    dfs(chosen)

            process_deps(recipe.build_deps, "build")
            process_deps(recipe.runtime_deps, "runtime")
            for flag, use_deps in recipe.use_deps.items():
                if flag in self.use_flags:
                    process_deps(use_deps, f"use[{flag}]")

        dfs(root)
        self.cache[root] = list(visited)  # salva cache
        return list(visited)

    # ===============================
    # Ordenação + análise
    # ===============================
    def topological_sort(self) -> List[str]:
        indegree = defaultdict(int)
        for u in self.graph:
            for v, _ in self.graph[u]:
                indegree[v] += 1
        queue = deque([u for u in self.graph if indegree[u] == 0])
        order = []
        while queue:
            u = queue.popleft()
            order.append(u)
            for v, _ in self.graph[u]:
                indegree[v] -= 1
                if indegree[v] == 0:
                    queue.append(v)
        if len(order) != len(self.graph):
            raise RuntimeError("Ciclo detectado nas dependências!")
        return order

    def explain(self, root: Optional[str] = None):
        print("\n[DependencyGraph] Relatório de dependências:")
        pkgs = [root] if root else self.graph.keys()
        for pkg in pkgs:
            recipe = self.recipes[pkg]
            for dep, dtype in self.graph[pkg]:
                dep_recipe = self.recipes[dep]
                print(f" - {pkg}-{recipe.version} depende de {dep}-{dep_recipe.version} ({dtype})")

    def why(self, pkg: str):
        """Mostra quem pediu este pacote"""
        if pkg not in self.reverse_graph:
            print(f"{pkg} não é dependido por ninguém.")
            return
        print(f"\n[DependencyGraph] {pkg} foi requerido por:")
        for parent in self.reverse_graph[pkg]:
            print(f" - {parent}")

    def find_orphans(self) -> List[str]:
        depended = {dep for deps in self.graph.values() for dep, _ in deps}
        return [pkg for pkg in self.recipes if pkg not in depended]


class DependencyResolver:
    def __init__(self):
        self.graph = DependencyGraph()

    def add_recipe(self, recipe: Recipe):
        self.graph.add_recipe(recipe)

    def enable_use(self, flag: str):
        self.graph.enable_use(flag)

    def define_profile(self, name: str, flags: List[str]):
        self.graph.define_profile(name, flags)

    def activate_profile(self, name: str):
        self.graph.activate_profile(name)

    def resolve(self, root: str) -> List[str]:
        self.graph.build(root)
        order = self.graph.topological_sort()
        logs.info(f"Ordem de instalação: {order}")
        return order

    def explain(self, root: Optional[str] = None):
        self.graph.explain(root)

    def why(self, pkg: str):
        self.graph.why(pkg)

    def find_orphans(self) -> List[str]:
        return self.graph.find_orphans()
