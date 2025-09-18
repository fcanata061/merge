#!/usr/bin/env python3
import sys
import os
import readline
from merge import (
    sync, recipe, install, remove, download, extract, upgrade, update,
    logs, hooks, patch, dependency, uses, sandbox
)
from merge import merge_autocomplete

# Cores para terminal
class Colors:
    HEADER = '\033[95m'
    OK = '\033[92m'
    WARNING = '\033[93m'
    ERROR = '\033[91m'
    END = '\033[0m'

HISTORY_FILE = os.path.expanduser("~/.merge_history")

def confirm(prompt="Deseja continuar? (s/n): "):
    """Confirmação do usuário com segurança."""
    if not sys.stdin.isatty():
        return True
    resp = input(prompt).strip().lower()
    return resp in ("s", "sim", "y", "yes")

def save_history():
    try:
        readline.write_history_file(HISTORY_FILE)
    except Exception:
        pass

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            readline.read_history_file(HISTORY_FILE)
        except Exception:
            pass

def setup_autocomplete(recipe_manager):
    """Configura autocomplete para comandos e receitas."""
    commands = [
        "sync", "list", "install", "remove", "update", "upgrade",
        "download", "extract", "patch", "dependencies",
        "sandbox", "hooks", "uses", "exit", "quit"
    ]

    def completer(text, state):
        buffer = readline.get_line_buffer()
        tokens = buffer.split()
        if len(tokens) == 0 or (len(tokens) == 1 and not buffer.endswith(" ")):
            options = [c for c in commands if c.startswith(text)]
        elif len(tokens) == 2 and tokens[0] in ("install", "remove", "download", "extract"):
            options = [r.name for r in recipe_manager.list_recipes() if r.name.startswith(text)]
        else:
            options = []
        if state < len(options):
            return options[state]
        return None

    readline.set_completer(completer)
    readline.parse_and_bind("tab: complete")

def print_ok(msg):
    print(f"{Colors.OK}[OK]{Colors.END} {msg}")

def print_warn(msg):
    print(f"{Colors.WARNING}[AVISO]{Colors.END} {msg}")

def print_error(msg):
    print(f"{Colors.ERROR}[ERRO]{Colors.END} {msg}")

def main():
    logs.setup_logging()
    sync_manager = sync.SyncManager()
    recipe_manager = recipe.RecipeManager(sync_manager.list_recipes())

    setup_autocomplete(recipe_manager)
    load_history()

    if len(sys.argv) > 1:
        # Modo CLI direto
        main_command(sys.argv[1:], sync_manager, recipe_manager)
    else:
        # Modo interativo
        print(f"{Colors.HEADER}Merge CLI - Digite 'exit' para sair{Colors.END}")
        while True:
            try:
                cmd_input = input("> ").strip()
                if cmd_input.lower() in ("exit", "quit"):
                    break
                if not cmd_input:
                    continue
                sys.argv = ["main.py"] + cmd_input.split()
                main_command(sys.argv[1:], sync_manager, recipe_manager)
            except KeyboardInterrupt:
                print("\nSaindo...")
                break
            except Exception as e:
                print_error(f"Erro inesperado: {e}")
            finally:
                save_history()

def main_command(args, sync_manager, recipe_manager):
    if not args:
        print_warn("Nenhum comando informado.")
        return

    cmd = args[0]
    cmd_args = args[1:]

    try:
        if cmd == "sync":
            sync_manager.sync_repo()
            print_ok("Repositório sincronizado com sucesso!")

        elif cmd == "list":
            recipes = recipe_manager.list_recipes()
            print_ok("Receitas disponíveis:")
            for r in recipes:
                print(f" - {r.name}")

        elif cmd == "install":
            if not cmd_args:
                print_error("Informe a receita para instalar.")
                return
            rec_name = cmd_args[0]
            rec = recipe_manager.get_recipe(rec_name)
            if not rec:
                print_error(f"Receita '{rec_name}' não encontrada.")
                return
            if confirm(f"Deseja instalar {rec_name}? "):
                install.install_recipe(rec)
                print_ok(f"{rec_name} instalado com sucesso!")

        elif cmd == "remove":
            if not cmd_args:
                print_error("Informe a receita para remover.")
                return
            rec_name = cmd_args[0]
            rec = recipe_manager.get_recipe(rec_name)
            if not rec:
                print_error(f"Receita '{rec_name}' não encontrada.")
                return
            if confirm(f"Deseja remover {rec_name}? "):
                remove.remove_recipe(rec)
                print_ok(f"{rec_name} removido com sucesso!")

        elif cmd == "update":
            update.update_all()
            print_ok("Atualização concluída!")

        elif cmd == "upgrade":
            upgrade.upgrade_system()
            print_ok("Sistema atualizado!")

        elif cmd == "download":
            if not cmd_args:
                print_error("Informe a receita para download.")
                return
            rec_name = cmd_args[0]
            rec = recipe_manager.get_recipe(rec_name)
            if rec:
                download.download_recipe(rec)
                print_ok(f"{rec_name} baixado com sucesso!")
            else:
                print_error(f"Receita '{rec_name}' não encontrada.")

        elif cmd == "extract":
            if not cmd_args:
                print_error("Informe a receita para extrair.")
                return
            rec_name = cmd_args[0]
            rec = recipe_manager.get_recipe(rec_name)
            if rec:
                extract.extract_recipe(rec)
                print_ok(f"{rec_name} extraído com sucesso!")
            else:
                print_error(f"Receita '{rec_name}' não encontrada.")

        elif cmd == "patch":
            patch.apply_patches()
            print_ok("Patches aplicados com sucesso!")

        elif cmd == "dependencies":
            dependency.check_dependencies()
            print_ok("Verificação de dependências concluída!")

        elif cmd == "sandbox":
            sandbox.run_sandbox()
            print_ok("Sandbox executado com sucesso!")

        elif cmd == "hooks":
            hooks.run_hooks()
            print_ok("Hooks executados com sucesso!")

        elif cmd == "uses":
            uses.show_uses()
            print_ok("Exibição de usos concluída!")

        else:
            print_warn(f"Comando '{cmd}' não reconhecido.")

    except Exception as e:
        logs.log_error(f"Erro ao executar {cmd}: {e}")
        print_error(f"Erro: {e}")
