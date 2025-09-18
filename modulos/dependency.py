from collections import defaultdict, deque
from .recipe import get_dependencies
from .repository import package_exists
from .logs import log

class DependencyResolver:
    def __init__(self):
        self.graph = defaultdict(list)
        self.indegree = defaultdict(int)

    def add_package(self, package):
        """Adiciona um pacote e suas dependências ao grafo"""
        if not package_exists(package):
            raise ValueError(f"Pacote '{package}' não existe no repositório.")

        deps = get_dependencies(package)
        for dep in deps:
            if not package_exists(dep):
                raise ValueError(f"Dependência '{dep}' de '{package}' não existe no repositório.")
            self.graph[dep].append(package)
            self.indegree[package] += 1
        # Garantir que o pacote apareça no grafo mesmo sem deps
        if package not in self.indegree:
            self.indegree[package] = 0

    def build_graph(self, root_packages):
        """Constrói o grafo completo recursivamente"""
        visited = set()

        def dfs(pkg):
            if pkg in visited:
                return
            visited.add(pkg)
            self.add_package(pkg)
            for dep in get_dependencies(pkg):
                dfs(dep)

        for pkg in root_packages:
            dfs(pkg)

    def resolve(self, root_packages):
        """
        Retorna uma lista ordenada de pacotes para instalar (ordem topológica).
        Detecta ciclos.
        """
        self.build_graph(root_packages)

        queue = deque([pkg for pkg, deg in self.indegree.items() if deg == 0])
        order = []

        while queue:
            pkg = queue.popleft()
            order.append(pkg)

            for neigh in self.graph[pkg]:
                self.indegree[neigh] -= 1
                if self.indegree[neigh] == 0:
                    queue.append(neigh)

        if len(order) != len(self.indegree):
            cycle_nodes = set(self.indegree.keys()) - set(order)
            raise RuntimeError(f"Ciclo detectado nas dependências: {cycle_nodes}")

        log(f"Resolução topológica para {root_packages}: {order}")
        return order
