import hashlib
import json
import logging
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from packaging.version import Version, InvalidVersion

logger = logging.getLogger("DependencyResolver")
logging.basicConfig(level=logging.INFO)

# ----------------------------
# Classe Recipe moderna
# ----------------------------
class Recipe:
    def __init__(self, name: str, version: str,
                 build_deps: List[str] = None,
                 runtime_deps: List[str] = None,
                 use_deps: Dict[str, List[str]] = None,
                 conflicts: List[str] = None):
        self.name = name
        self.version = version
        self.build_deps = build_deps or []
        self.runtime_deps = runtime_deps or []
        self.use_deps = use_deps or {}
        self.conflicts = conflicts or []

# ----------------------------
# Classe Graph moderna e paralelizável
# ----------------------------
class DependencyGraph:
    def __init__(self, use_flags: Optional[Set[str]] = None):
        self.graph: Dict[str, Set[str]] = defaultdict(set)
        self.reverse_graph: Dict[str, Set[str]] = defaultdict(set)
        self.recipes: Dict[str, Recipe] = {}
        self.use_flags: Set[str] = use_flags or set()
        self._lock = None  # opcional para threads

    def add_recipe(self, recipe: Recipe):
        self.recipes[recipe.name] = recipe
        logger.debug(f"Receita adicionada: {recipe.name}-{recipe.version}")

    def enable_use(self, flag: str):
        self.use_flags.add(flag)

    def _split_version(self, dep: str) -> Tuple[str, Optional[str], Optional[str]]:
        for op in [">=", "<=", "=", ">", "<"]:
            if op in dep:
                name, ver = dep.split(op, 1)
                return name.strip(), op, ver.strip()
        return dep.strip(), None, None

    def _parse_dependency(self, dep: str) -> List[Tuple[str, Optional[str], Optional[str]]]:
        # Suporte a OR-dependencies
        if "|" in dep:
            return [self._split_version(d.strip()) for d in dep.split("|")]
        return [self._split_version(dep)]

    def _check_version(self, recipe: Recipe, op: Optional[str], ver: Optional[str]) -> bool:
        if not op or not ver:
            return True
        try:
            return {
                ">=": Version(recipe.version) >= Version(ver),
                "<=": Version(recipe.version) <= Version(ver),
                "=": Version(recipe.version) == Version(ver),
                ">": Version(recipe.version) > Version(ver),
                "<": Version(recipe.version) < Version(ver),
            }.get(op, False)
        except InvalidVersion:
            return False

    def _check_conflicts(self, recipe: Recipe):
        for conflict in recipe.conflicts:
            for name, op, ver in self._parse_dependency(conflict):
                r = self.recipes.get(name)
                if r and self._check_version(r, op, ver):
                    raise RuntimeError(f"Conflito: {recipe.name}-{recipe.version} com {r.name}-{r.version}")

    def build_graph(self, root: str, parallel: bool = False) -> Set[str]:
        visited = set()
        executor = ThreadPoolExecutor() if parallel else None

        def dfs(pkg: str):
            if pkg in visited:
                return
            visited.add(pkg)
            recipe = self.recipes.get(pkg)
            if not recipe:
                raise ValueError(f"Receita não encontrada: {pkg}")
            self._check_conflicts(recipe)

            def process_deps(dep_list: List[str]):
                for dep in dep_list:
                    candidates = self._parse_dependency(dep)
                    chosen = None
                    for name, op, ver in candidates:
                        r = self.recipes.get(name)
                        if r and self._check_version(r, op, ver):
                            chosen = name
                            break
                    if not chosen:
                        raise RuntimeError(f"Nenhuma dependência válida encontrada para {dep} exigida por {pkg}")
                    self.graph[pkg].add(chosen)
                    self.reverse_graph[chosen].add(pkg)
                    if parallel:
                        executor.submit(dfs, chosen)
                    else:
                        dfs(chosen)

            process_deps(recipe.build_deps)
            process_deps(recipe.runtime_deps)
            for flag, deps in recipe.use_deps.items():
                if flag in self.use_flags:
                    process_deps(deps)

        dfs(root)
        if executor:
            executor.shutdown(wait=True)
        return visited

    def topological_sort(self) -> List[str]:
        indegree = defaultdict(int)
        for u in self.graph:
            for v in self.graph[u]:
                indegree[v] += 1
        queue = deque([u for u in self.graph if indegree[u] == 0])
        order = []
        while queue:
            u = queue.popleft()
            order.append(u)
            for v in self.graph[u]:
                indegree[v] -= 1
                if indegree[v] == 0:
                    queue.append(v)
        if len(order) != len(self.graph):
            raise RuntimeError("Ciclo detectado nas dependências!")
        return order

    def explain(self, root: Optional[str] = None):
        pkgs = [root] if root else self.graph.keys()
        for pkg in pkgs:
            for dep in self.graph[pkg]:
                print(f"{pkg} depende de {dep}")

    def why(self, pkg: str):
        if pkg not in self.reverse_graph:
            print(f"{pkg} não é dependido por ninguém")
            return
        print(f"{pkg} é requerido por:")
        for p in self.reverse_graph[pkg]:
            print(f" - {p}")

    def find_orphans(self) -> List[str]:
        depended = {dep for deps in self.graph.values() for dep in deps}
        return [pkg for pkg in self.recipes if pkg not in depended]

# ----------------------------
# Resolver de dependências moderno
# ----------------------------
class DependencyResolver:
    def __init__(self, use_flags: Optional[Set[str]] = None):
        self.graph = DependencyGraph(use_flags=use_flags)

    def add_recipe(self, recipe: Recipe):
        self.graph.add_recipe(recipe)

    def enable_use(self, flag: str):
        self.graph.enable_use(flag)

    def resolve(self, root: str, parallel: bool = False) -> List[str]:
        self.graph.build_graph(root, parallel=parallel)
        order = self.graph.topological_sort()
        logger.info(f"Ordem de instalação: {order}")
        return order

    def explain(self, root: Optional[str] = None):
        self.graph.explain(root)

    def why(self, pkg: str):
        self.graph.why(pkg)

    def find_orphans(self) -> List[str]:
        return self.graph.find_orphans()
