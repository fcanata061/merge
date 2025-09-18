import os
import yaml
from .config import cfg
from .logs import log
from .repository import is_installed
from .install import install_with_resolver
from .remove import remove_with_dependencies

USES_DIR = os.path.join(cfg.get("global", "workdir"), "useflags")
os.makedirs(USES_DIR, exist_ok=True)

def get_uses_file(pkg_name):
    return os.path.join(USES_DIR, f"{pkg_name}.yaml")

def load_use_flags(pkg_name):
    """Carrega flags ativas do pacote"""
    path = get_uses_file(pkg_name)
    if not os.path.exists(path):
        return {"active_flags": {}, "dependencies_from_flags": {}}
    with open(path, "r") as f:
        return yaml.safe_load(f)

def save_use_flags(pkg_name, data):
    path = get_uses_file(pkg_name)
    with open(path, "w") as f:
        yaml.safe_dump(data, f)

def show_flags(pkg_name, recipe):
    """Exibe as flags ativas/inativas"""
    uses = load_use_flags(pkg_name)
    active_flags = uses.get("active_flags", {})
    recipe_flags = recipe.get("use_flags", {})
    print(f"\n{pkg_name} USE flags:")
    for flag in recipe_flags:
        status = "✅ ativa" if active_flags.get(flag, False) else "❌ inativa"
        print(f"  {flag}: {status}")

def activate_flag(pkg_name, flag, recipe):
    """Ativa uma flag e instala dependências correspondentes"""
    recipe_flags = recipe.get("use_flags", {})
    if flag not in recipe_flags:
        print(f"⚠ Flag {flag} não definida na receita de {pkg_name}")
        return
    uses = load_use_flags(pkg_name)
    uses.setdefault("active_flags", {})[flag] = True
    deps = recipe_flags[flag].get("dependencies", [])
    uses.setdefault("dependencies_from_flags", {})[flag] = deps
    save_use_flags(pkg_name, uses)
    log(f"Flag ativada: {flag} para {pkg_name}")
    # Instala dependências extras
    for dep in deps:
        if not is_installed(dep):
            print(f"Instalando dependência {dep} por flag {flag}")
            install_with_resolver(dep)

def deactivate_flag(pkg_name, flag, recipe):
    """Desativa uma flag e marca dependências órfãs"""
    uses = load_use_flags(pkg_name)
    active_flags = uses.get("active_flags", {})
    if flag not in active_flags or not active_flags[flag]:
        print(f"⚠ Flag {flag} já está desativada")
        return
    active_flags[flag] = False
    deps = uses.get("dependencies_from_flags", {}).get(flag, [])
    uses["dependencies_from_flags"][flag] = deps
    save_use_flags(pkg_name, uses)
    log(f"Flag desativada: {flag} para {pkg_name}")
    # Marcar dependências para depclean
    for dep in deps:
        print(f"Dependência {dep} da flag {flag} agora pode ser órfã (depclean)")

def process_uses_command(pkg_name, args, recipe):
    """
    args: lista de flags com + ou -
    ex: ["+http2", "-lua"]
    """
    for arg in args:
        if arg.startswith("+"):
            activate_flag(pkg_name, arg[1:], recipe)
        elif arg.startswith("-"):
            deactivate_flag(pkg_name, arg[1:], recipe)
        else:
            print(f"⚠ Flag inválida: {arg}")
