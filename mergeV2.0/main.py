import asyncio
import readline
from config import Config
from recipe import RecipeManager
from install import Installer
from remove import Remover
from download import Downloader
from extract import Extractor
from upgrade import UpgraderV3
from update import Updater
from sync import SyncManager
from patch import PatchApplier
from hooks import HooksManager
from uses import UseManager
from sandbox import Sandbox
from merge_autocomplete import setup_autocomplete
from logs import info, success, warn, error, stage
from colorama import Fore, Style

# Inicializa módulos
installer = Installer()
remover = Remover()
downloader = Downloader(Config.BUILD_DIR, sandbox=Sandbox, hooks=HooksManager())
extractor = Extractor(sandbox=Sandbox, hooks=HooksManager())
upgrader = UpgraderV3()
updater = Updater()
sync_manager = SyncManager.from_config(Config.REPO_FILE)
patcher = PatchApplier(Config.BUILD_DIR)
hooks = HooksManager()
use_manager = UseManager()
recipe_manager = RecipeManager()

# Configura autocomplete
setup_autocomplete(recipe_manager, ["i", "r", "f", "g", "info", "build", "sync", "update", "upgrade"])

# --------------------
# Funções auxiliares
# --------------------
def pacote_status(recipe_name):
    try:
        installed = recipe_manager.get_installed(recipe_name)
        # Verifica se há update disponível
        if recipe_manager.has_update(recipe_name):
            return "UPDATE"
        return "INSTALADO"
    except Exception:
        return "NÃO INSTALADO"

def color_status(status):
    if status == "INSTALADO": return Fore.GREEN + status + Fore.RESET
    if status == "NÃO INSTALADO": return Fore.RED + status + Fore.RESET
    if status == "UPDATE": return Fore.YELLOW + status + Fore.RESET
    if status == "ERRO": return Fore.RED + Style.BRIGHT + status + Fore.RESET
    return status

def listar_receitas():
    stage("Receitas disponíveis:")
    for recipe in recipe_manager.list_recipes():
        status = pacote_status(recipe.name)
        flags = asyncio.run(use_manager.get_flags(recipe.name))
        info(f" - {recipe.name} ({recipe.version}) [{color_status(status)}] Flags: {', '.join(flags) if flags else 'Nenhuma'}")

# --------------------
# Comandos principais
# --------------------
def cmd_instalar(pkg):
    stage(f"Iniciando instalação de {pkg}...")
    try:
        installer.install(pkg)
        downloader.download(pkg)
        extractor.extract_all_parallel(pkg)
        asyncio.run(patcher.apply_recipe_patches(pkg, ["./build_dir"]))
        asyncio.run(hooks.run_all_hooks(pkg))
        flags = asyncio.run(use_manager.get_flags(pkg))
        info(f"Flags USE para {pkg}: {flags}")
        success(f"Pacote {pkg} instalado!")
    except Exception as e:
        error(f"Erro ao instalar {pkg}: {e}")

def cmd_remover(pkg):
    try:
        remover.remove(pkg)
        success(f"Pacote {pkg} removido!")
    except Exception as e:
        error(f"Erro ao remover {pkg}: {e}")

def cmd_flags(pkg):
    flags = asyncio.run(use_manager.get_flags(pkg))
    info(f"Flags USE para {pkg}: {flags}")

def cmd_gerenciar_flags(pkg):
    flags = asyncio.run(use_manager.get_flags(pkg))
    info(f"Flags atuais de {pkg}: {flags}")
    print("Digite a flag para ativar/desativar (ou 'sair' para voltar):")
    while True:
        f = input("Flag: ").strip()
        if f.lower() == "sair": break
        if f in flags:
            asyncio.run(use_manager.disable_flag(pkg, f))
            warn(f"Flag {f} desativada.")
        else:
            asyncio.run(use_manager.enable_flag(pkg, f))
            success(f"Flag {f} ativada.")
        flags = asyncio.run(use_manager.get_flags(pkg))
        info(f"Flags atuais: {flags}")

def cmd_sync(): asyncio.run(sync_manager.sync_all()); success("Repos sincronizados!")
def cmd_update(): updater.update(world=True); success("Sistema atualizado!")
def cmd_upgrade(): asyncio.run(upgrader.upgrade_packages()); success("Upgrade concluído!")

# --------------------
# Novos comandos
# --------------------
def cmd_info(pkg):
    try:
        recipe = recipe_manager.get_recipe(pkg)
        status = pacote_status(pkg)
        flags = asyncio.run(use_manager.get_flags(pkg))
        stage(f"Informações do pacote: {pkg}")
        info(f"Nome: {recipe.name}")
        info(f"Versão: {recipe.version}")
        info(f"Status: {color_status(status)}")
        info(f"Dependências: {', '.join(recipe.dependencies) if recipe.dependencies else 'Nenhuma'}")
        info(f"Flags USE: {', '.join(flags) if flags else 'Nenhuma'}")
        info(f"Receitas: {recipe.recipe_file}")
    except Exception as e:
        error(f"Erro ao obter info de {pkg}: {e}")

def cmd_build(pkg):
    stage(f"Iniciando build simulado para {pkg}...")
    try:
        downloader.download(pkg)
        extractor.extract_all_parallel(pkg)
        asyncio.run(patcher.apply_recipe_patches(pkg, ["./build_dir"]))
        asyncio.run(hooks.run_all_hooks(pkg))
        success(f"Build de {pkg} concluído (simulado, pacote não instalado).")
    except Exception as e:
        error(f"Erro no build simulado de {pkg}: {e}")

# --------------------
# Loop principal
# --------------------
def main_loop():
    stage("=== Merge Program Manager (Terminal Avançado) ===")
    info("Digite 'help' para ver os comandos disponíveis.\n")
    while True:
        listar_receitas()
        cmd = input("> ").strip()
        if not cmd: continue
        parts = cmd.split()
        action = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else None

        if action == "help":
            print("""
Comandos disponíveis:
 i <pacote>       - Instalar pacote
 r <pacote>       - Remover pacote
 f <pacote>       - Mostrar flags USE
 g <pacote>       - Gerenciar flags USE
 info <pacote>    - Mostrar informações detalhadas do pacote
 build <pacote>   - Simular build sem instalar
 sync             - Sincronizar repositórios
 update           - Atualizar sistema
 upgrade          - Upgrade do sistema
 exit / quit      - Sair
""")
        elif action == "i" and arg: cmd_instalar(arg)
        elif action == "r" and arg: cmd_remover(arg)
        elif action == "f" and arg: cmd_flags(arg)
        elif action == "g" and arg: cmd_gerenciar_flags(arg)
        elif action == "sync": cmd_sync()
        elif action == "update": cmd_update()
        elif action == "upgrade": cmd_upgrade()
        elif action == "info" and arg: cmd_info(arg)
        elif action == "build" and arg: cmd_build(arg)
        elif action in ["exit", "quit"]: stage("Saindo do gerenciador..."); break
        else: warn("Comando inválido! Digite 'help' para ajuda.")

if __name__ == "__main__":
    main_loop()
