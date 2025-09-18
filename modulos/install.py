import os
import subprocess
import shutil
import time
from .config import cfg
from .logs import log
from .recipe import load_recipe, get_commands
from .sandbox import run_in_sandbox
from .dependency import DependencyResolver

# Cores
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"


def stage_msg(stage, msg, color=CYAN, end=None):
    if end is None:
        print(f"{color}[{stage}]{RESET} {msg}")
    else:
        print(f"{color}[{stage}]{RESET} {msg}", end=end)


def format_time(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m}m{s}s" if m else f"{s}s"


def timed_stage(func):
    """Decorador para medir tempo de uma etapa"""
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        stage_name = func.__name__.replace("_package", "").upper()
        if result:
            print(f"   ⏱️ {stage_name} levou {format_time(elapsed)}")
        return result
    return wrapper


@timed_stage
def fetch_package(pkg):
    """Baixa pacote usando cache"""
    recipe = load_recipe(pkg)
    src_uri = recipe.get("src_uri")
    if not src_uri:
        stage_msg("FETCH", f"Nenhuma URI definida para {pkg}", RED)
        return False

    workdir = cfg.get("global", "workdir")
    cache_dir = cfg.get("global", "cache_dir", fallback="/var/cache/merge/packages")
    os.makedirs(workdir, exist_ok=True)
    os.makedirs(cache_dir, exist_ok=True)

    filename = os.path.basename(src_uri)
    cached_file = os.path.join(cache_dir, filename)
    local_file = os.path.join(workdir, filename)

    try:
        if os.path.exists(cached_file):
            stage_msg("FETCH", f"Usando cache para {pkg} ... ", CYAN, end="")
            shutil.copy2(cached_file, local_file)
            print(f"{GREEN}[OK]{RESET}")
            log(f"Pacote {pkg} obtido do cache")
        else:
            stage_msg("FETCH", f"Baixando {pkg} de {src_uri} ... ", CYAN, end="")
            subprocess.run(f"wget -c {src_uri} -O {cached_file}", shell=True, check=True)
            shutil.copy2(cached_file, local_file)
            print(f"{GREEN}[OK]{RESET}")
            log(f"Pacote {pkg} baixado e salvo no cache")
        return True
    except subprocess.CalledProcessError as e:
        print(f"{RED}[FAIL]{RESET}")
        stage_msg("FETCH", f"Erro no fetch de {pkg}: {e}", RED)
        return False


@timed_stage
def extract_package(pkg):
    recipe = load_recipe(pkg)
    filename = os.path.basename(recipe.get("src_uri", ""))
    workdir = cfg.get("global", "workdir")
    src_path = os.path.join(workdir, filename)

    if not os.path.exists(src_path):
        stage_msg("EXTRACT", f"Arquivo fonte não encontrado: {src_path}", RED)
        return False

    try:
        stage_msg("EXTRACT", f"Extraindo {pkg} ... ", CYAN, end="")
        subprocess.run(f"tar -xf {src_path} -C {workdir}", shell=True, check=True)
        print(f"{GREEN}[OK]{RESET}")
        log(f"Extração concluída para {pkg}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"{RED}[FAIL]{RESET}")
        stage_msg("EXTRACT", f"Erro ao extrair {pkg}: {e}", RED)
        return False


@timed_stage
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
            stage_msg("PATCH", f"Aplicando {patch} em {pkg} ... ", CYAN, end="")
            subprocess.run(f"patch -d {srcdir} -p1 < {patch_file}", shell=True, check=True)
            print(f"{GREEN}[OK]{RESET}")
        log(f"Patches aplicados em {pkg}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"{RED}[FAIL]{RESET}")
        stage_msg("PATCH", f"Erro ao aplicar patch em {pkg}: {e}", RED)
        return False


@timed_stage
def compile_package(pkg):
    commands = get_commands(pkg, section="compile")
    if not commands:
        stage_msg("COMPILE", f"Nenhum comando de compilação definido para {pkg}", YELLOW)
        return False

    stage_msg("COMPILE", f"Compilando {pkg} em sandbox ... ", CYAN, end="")
    if not run_in_sandbox(commands, pkg):
        print(f"{RED}[FAIL]{RESET}")
        return False

    print(f"{GREEN}[OK]{RESET}")
    log(f"Compilação concluída para {pkg}")
    return True


@timed_stage
def build_package(pkg):
    stage_msg("BUILD", f"Iniciando build de {pkg} (sem instalação)", YELLOW)
    if not fetch_package(pkg): return False
    if not extract_package(pkg): return False
    if not patch_package(pkg): return False
    if not compile_package(pkg): return False
    stage_msg("BUILD", f"Build de {pkg} concluído com sucesso", GREEN)
    log(f"Build de {pkg} concluído")
    return True


def install_package(pkg_name, installed=None, mode="recipe", source_path=None):
    if installed is None:
        installed = set()

    if pkg_name in installed:
        return True

    from .repository import package_exists
    if not package_exists(pkg_name):
        stage_msg("INSTALL", f"Pacote '{pkg_name}' não encontrado", RED)
        log(f"Erro: Pacote '{pkg_name}' não encontrado.")
        return False

    install_path = cfg.get("global", "install_path")
    os.makedirs(install_path, exist_ok=True)
    dest_dir = os.path.join(install_path, pkg_name)

    try:
        if mode == "recipe":
            if not build_package(pkg_name):
                return False
            stage_msg("INSTALL", f"Instalando {pkg_name} ... ", CYAN, end="")
            commands = get_commands(pkg_name, section="install")
            if not run_in_sandbox(commands, pkg_name):
                print(f"{RED}[FAIL]{RESET}")
                return False
            print(f"{GREEN}[OK]{RESET}")

        elif mode == "binary":
            if not source_path or not os.path.exists(source_path):
                stage_msg("INSTALL", f"Binário inválido para {pkg_name}", RED)
                return False
            stage_msg("INSTALL", f"Extraindo binário {pkg_name} ... ", CYAN, end="")
            subprocess.run(f"tar -xzf {source_path} -C {install_path}", shell=True, check=True)
            print(f"{GREEN}[OK]{RESET}")
            log(f"Pacote '{pkg_name}' instalado via binário")

        elif mode == "dir":
            if not source_path or not os.path.exists(source_path):
                stage_msg("INSTALL", f"Diretório inválido para {pkg_name}", RED)
                return False
            stage_msg("INSTALL", f"Copiando diretório {pkg_name} ... ", CYAN, end="")
            subprocess.run(f"fakeroot cp -r {source_path} {dest_dir}", shell=True, check=True)
            print(f"{GREEN}[OK]{RESET}")
            log(f"Pacote '{pkg_name}' instalado via diretório em {dest_dir}")

        else:
            stage_msg("INSTALL", f"Modo '{mode}' não suportado", RED)
            return False

        installed.add(pkg_name)
        stage_msg("INSTALL", f"{pkg_name} instalado com sucesso", GREEN)
        log(f"Pacote '{pkg_name}' instalado no modo '{mode}'")
        return True

    except subprocess.CalledProcessError as e:
        stage_msg("INSTALL", f"Erro ao instalar {pkg_name}: {e}", RED)
        log(f"Erro ao instalar {pkg_name}: {e}")
        return False


def install_with_resolver(pkg_name, mode="recipe", source_path=None):
    resolver = DependencyResolver()
    try:
        order = resolver.resolve([pkg_name])
    except RuntimeError as e:
        stage_msg("DEP", f"Erro de dependência: {e}", RED)
        log(f"Erro de dependência: {e}")
        return False

    stage_msg("DEP", f"Ordem de instalação: {order}", CYAN)
    log(f"Plano de instalação: {order}")

    start_total = time.time()
    installed = set()
    for pkg in order:
        stage_msg("INSTALL", f"Iniciando instalação de {pkg}", YELLOW)
        success = install_package(pkg, installed=installed, mode=mode, source_path=source_path)
        if not success:
            stage_msg("INSTALL", f"Falha ao instalar {pkg}", RED)
            log(f"Falha ao instalar {pkg}")
            print(f"\n{RED}>>> Instalação abortada em {pkg}{RESET}")
            return False

    elapsed_total = format_time(time.time() - start_total)
    print(f"\n{GREEN}>>> Todos os pacotes instalados com sucesso em {elapsed_total}{RESET}")
    return True
