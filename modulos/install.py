import os
import subprocess
import shutil
from .config import cfg
from .repository import package_exists
from .recipe import get_commands, load_recipe
from .sandbox import run_in_sandbox
from .logs import log
from .dependency import DependencyResolver


def fetch_package(pkg):
    """
    Baixa os arquivos fonte do pacote
    """
    recipe = load_recipe(pkg)
    src_uri = recipe.get("src_uri")
    if not src_uri:
        print(f"Nenhuma URI de origem definida para {pkg}")
        return False

    workdir = cfg.get("global", "workdir")
    os.makedirs(workdir, exist_ok=True)

    try:
        print(f"Baixando {pkg} de {src_uri}...")
        subprocess.run(f"wget -c {src_uri} -P {workdir}", shell=True, check=True)
        log(f"Fetch concluído para {pkg}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Erro no fetch de {pkg}: {e}")
        return False


def extract_package(pkg):
    """
    Extrai os arquivos baixados
    """
    recipe = load_recipe(pkg)
    filename = os.path.basename(recipe.get("src_uri", ""))
    workdir = cfg.get("global", "workdir")
    src_path = os.path.join(workdir, filename)

    if not os.path.exists(src_path):
        print(f"Arquivo fonte não encontrado: {src_path}")
        return False

    try:
        print(f"Extraindo {pkg}...")
        subprocess.run(f"tar -xf {src_path} -C {workdir}", shell=True, check=True)
        log(f"Extração concluída para {pkg}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Erro ao extrair {pkg}: {e}")
        return False


def patch_package(pkg):
    """
    Aplica patches definidos no recipe
    """
    recipe = load_recipe(pkg)
    patches = recipe.get("patches", [])
    if not patches:
        print(f"Nenhum patch definido para {pkg}")
        return True

    workdir = cfg.get("global", "workdir")
    srcdir = recipe.get("srcdir", os.path.join(workdir, pkg))

    try:
        for patch in patches:
            patch_file = os.path.join("patches", patch)
            print(f"Aplicando patch {patch} em {pkg}...")
            subprocess.run(f"patch -d {srcdir} -p1 < {patch_file}",
                           shell=True, check=True)
        log(f"Patches aplicados em {pkg}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Erro ao aplicar patch em {pkg}: {e}")
        return False


def compile_package(pkg):
    """
    Compila o pacote em sandbox
    """
    commands = get_commands(pkg, section="compile")
    if not commands:
        print(f"Nenhum comando de compilação definido para {pkg}")
        return False

    print(f"Compilando {pkg} em sandbox...")
    if not run_in_sandbox(commands, pkg):
        print(f"Falha ao compilar {pkg}")
        return False

    log(f"Compilação concluída para {pkg}")
    return True


def build_package(pkg):
    """
    Executa fetch, extract, patch e compile (sem instalar)
    """
    print(f"Iniciando build de {pkg} (sem instalação)")
    if not fetch_package(pkg): return False
    if not extract_package(pkg): return False
    if not patch_package(pkg): return False
    if not compile_package(pkg): return False
    print(f"Build de {pkg} concluído com sucesso")
    log(f"Build de {pkg} concluído")
    return True


def install_package(package_name, installed=None, mode="recipe", source_path=None):
    """
    Instala um pacote em três modos:
    - recipe: executa comandos do recipe.yaml em sandbox
    - binary: instala binário pré-compilado (tar.gz)
    - dir   : copia diretório local para install_path usando fakeroot
    """
    if installed is None:
        installed = set()

    if package_name in installed:
        return True

    if not package_exists(package_name):
        print(f"Erro: Pacote '{package_name}' não encontrado no repositório.")
        log(f"Erro: Pacote '{package_name}' não encontrado.")
        return False

    install_path = cfg.get("global", "install_path")
    os.makedirs(install_path, exist_ok=True)
    dest_dir = os.path.join(install_path, package_name)

    try:
        if mode == "recipe":
            # executa pipeline completo + install
            if not build_package(package_name):
                return False
            commands = get_commands(package_name, section="install")
            if not run_in_sandbox(commands, package_name):
                print(f"Falha ao instalar {package_name}")
                return False

        elif mode == "binary":
            if not source_path or not os.path.exists(source_path):
                print("Erro: caminho do binário inválido")
                return False
            subprocess.run(f"tar -xzf {source_path} -C {install_path}",
                           shell=True, check=True)
            log(f"Pacote '{package_name}' instalado via binário")

        elif mode == "dir":
            if not source_path or not os.path.exists(source_path):
                print("Erro: diretório de origem inválido")
                return False
            subprocess.run(f"fakeroot cp -r {source_path} {dest_dir}",
                           shell=True, check=True)
            log(f"Pacote '{package_name}' instalado via diretório em {dest_dir}")

        else:
            print(f"Modo '{mode}' não suportado")
            return False

        installed.add(package_name)
        print(f"Pacote '{package_name}' instalado com sucesso.")
        log(f"Pacote '{package_name}' instalado com sucesso no modo '{mode}'")
        return True

    except subprocess.CalledProcessError as e:
        print(f"Erro ao instalar {package_name}: {e}")
        log(f"Erro ao instalar {package_name}: {e}")
        return False


def install_with_resolver(package_name, mode="recipe", source_path=None):
    """
    Resolve dependências com ordenação topológica e instala na ordem correta
    """
    resolver = DependencyResolver()
    try:
        order = resolver.resolve([package_name])
    except RuntimeError as e:
        print(f"Erro de dependência: {e}")
        log(f"Erro de dependência: {e}")
        return False

    print(f"Ordem de instalação: {order}")
    log(f"Plano de instalação: {order}")

    installed = set()
    for pkg in order:
        print(f"> Instalando {pkg} ...")
        success = install_package(pkg, installed=installed, mode=mode, source_path=source_path)
        if not success:
            print(f"Falha ao instalar {pkg}")
            log(f"Falha ao instalar {pkg}")
            return False

    return True
