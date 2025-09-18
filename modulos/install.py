import os
import subprocess
import shutil
from .config import cfg
from .repository import package_exists
from .recipe import get_commands, load_recipe
from .sandbox import run_in_sandbox
from .logs import log
from .dependency import DependencyResolver

# Cores
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"


def stage_msg(stage, msg, color=CYAN):
    """Imprime mensagem de estágio formatada"""
    print(f"{color}[{stage}]{RESET} {msg}")


def fetch_package(pkg):
    recipe = load_recipe(pkg)
    src_uri = recipe.get("src_uri")
    if not src_uri:
        stage_msg("FETCH", f"Nenhuma URI definida para {pkg}", RED)
        return False

    workdir = cfg.get("global", "workdir")
    os.makedirs(workdir, exist_ok=True)

    try:
        stage_msg("FETCH", f"Baixando {pkg} de {src_uri}")
        subprocess.run(f"wget -c {src_uri} -P {workdir}", shell=True, check=True)
        log(f"Fetch concluído para {pkg}")
        return True
    except subprocess.CalledProcessError as e:
        stage_msg("FETCH", f"Erro no fetch de {pkg}: {e}", RED)
        return False


def extract_package(pkg):
    recipe = load_recipe(pkg)
    filename = os.path.basename(recipe.get("src_uri", ""))
    workdir = cfg.get("global", "workdir")
    src_path = os.path.join(workdir, filename)

    if not os.path.exists(src_path):
        stage_msg("EXTRACT", f"Arquivo fonte não encontrado: {src_path}", RED)
        return False

    try:
        stage_msg("EXTRACT", f"Extraindo {pkg}")
        subprocess.run(f"tar -xf {src_path} -C {workdir}", shell=True, check=True)
        log(f"Extração concluída para {pkg}")
        return True
    except subprocess.CalledProcessError as e:
        stage_msg("EXTRACT", f"Erro ao extrair {pkg}: {e}", RED)
        return False


def patch_package(pkg):
    recipe = load_recipe(pkg)
    patches = recipe.get("patches", [])
    if not patches:
        stage_msg("PATCH", f"Nenhum patch para {pkg}", YELLOW)
        return True

    workdir = cfg.get("global", "workdir")
    srcdir = recipe.get("srcdir", os.path.join(workdir, pkg))

    try:
        for patch in patches:
            patch_file = os.path.join("patches", patch)
            stage_msg("PATCH", f"Aplicando {patch} em {pkg}")
            subprocess.run(f"patch -d {srcdir} -p1 < {patch_file}",
                           shell=True, check=True)
        log(f"Patches aplicados em {pkg}")
        return True
    except subprocess.CalledProcessError as e:
        stage_msg("PATCH", f"Erro ao aplicar patch em {pkg}: {e}", RED)
        return False


def compile_package(pkg):
    commands = get_commands(pkg, section="compile")
    if not commands:
        stage_msg("COMPILE", f"Nenhum comando de compilação definido para {pkg}", YELLOW)
        return False

    stage_msg("COMPILE", f"Compilando {pkg} em sandbox...")
    if not run_in_sandbox(commands, pkg):
        stage_msg("COMPILE", f"Falha ao compilar {pkg}", RED)
        return False

    log(f"Compilação concluída para {pkg}")
    stage_msg("COMPILE", f"{pkg} compilado com sucesso", GREEN)
    return True


def build_package(pkg):
    stage_msg("BUILD", f"Iniciando build de {pkg} (sem instalação)", YELLOW)
    if not fetch_package(pkg): return False
    if not extract_package(pkg): return False
    if not patch_package(pkg): return False
    if not compile_package(pkg): return False
    stage_msg("BUILD", f"Build de {pkg} concluído com sucesso", GREEN)
    log(f"Build de {pkg} concluído")
    return True


def install_package(package_name, installed=None, mode="recipe", source_path=None):
    if installed is None:
        installed = set()

    if package_name in installed:
        return True

    if not package_exists(package_name):
        stage_msg("INSTALL", f"Pacote '{package_name}' não encontrado", RED)
        log(f"Erro: Pacote '{package_name}' não encontrado.")
        return False

    install_path = cfg.get("global", "install_path")
    os.makedirs(install_path, exist_ok=True)
    dest_dir = os.path.join(install_path, package_name)

    try:
        if mode == "recipe":
            if not build_package(package_name):
                return False
            commands = get_commands(package_name, section="install")
            if not run_in_sandbox(commands, package_name):
                stage_msg("INSTALL", f"Falha ao instalar {package_name}", RED)
                return False

        elif mode == "binary":
            if not source_path or not os.path.exists(source_path):
                stage_msg("INSTALL", f"Binário inválido para {package_name}", RED)
                return False
            subprocess.run(f"tar -xzf {source_path} -C {install_path}",
                           shell=True, check=True)
            log(f"Pacote '{package_name}' instalado via binário")

        elif mode == "dir":
            if not source_path or not os.path.exists(source_path):
                stage_msg("INSTALL", f"Diretório inválido para {package_name}", RED)
                return False
            subprocess.run(f"fakeroot cp -r {source_path} {dest_dir}",
                           shell=True, check=True)
            log(f"Pacote '{package_name}' instalado via diretório em {dest_dir}")

        else:
            stage_msg("INSTALL", f"Modo '{mode}' não suportado", RED)
            return False

        installed.add(package_name)
        stage_msg("INSTALL", f"{package_name} instalado com sucesso", GREEN)
        log(f"Pacote '{package_name}' instalado no modo '{mode}'")
        return True

    except subprocess.CalledProcessError as e:
        stage_msg("INSTALL", f"Erro ao instalar {package_name}: {e}", RED)
        log(f"Erro ao instalar {package_name}: {e}")
        return False


def install_with_resolver(package_name, mode="recipe", source_path=None):
    resolver = DependencyResolver()
    try:
        order = resolver.resolve([package_name])
    except RuntimeError as e:
        stage_msg("DEP", f"Erro de dependência: {e}", RED)
        log(f"Erro de dependência: {e}")
        return False

    stage_msg("DEP", f"Ordem de instalação: {order}", CYAN)
    log(f"Plano de instalação: {order}")

    installed = set()
    for pkg in order:
        stage_msg("INSTALL", f"Iniciando instalação de {pkg}", YELLOW)
        success = install_package(pkg, installed=installed, mode=mode, source_path=source_path)
        if not success:
            stage_msg("INSTALL", f"Falha ao instalar {pkg}", RED)
            log(f"Falha ao instalar {pkg}")
            return False

    return True
