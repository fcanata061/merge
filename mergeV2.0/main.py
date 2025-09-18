#!/usr/bin/env python3
import sys
import readline
from merge import (
    sync, recipe, install, remove, download, extract, upgrade, update,
    logs, hooks, patch, dependency, uses, sandbox
)
from merge import merge_autocomplete

def confirm(prompt="Deseja continuar? (s/n): "):
    """Confirmação do usuário com segurança."""
    if not sys.stdin.isatty():
        return True  # Assume sim em ambiente não interativo
    resp = input(prompt).strip().lower()
    return resp in ("s", "sim", "y", "yes")

def setup_autocomplete(recipe_manager):
    """Configura autocomplete para comandos e receitas."""
    commands = [
        "sync", "list", "install", "remove", "update", "upgrade",
        "download", "extract", "patch", "dependencies",
        "sandbox", "hooks", "uses"
    ]

    def completer(text, state):
        buffer = readline.get_line_buffer()
        tokens = buffer.split()
        if len(tokens) == 1:
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

def main():
    logs.setup_logging()
    sync_manager = sync.SyncManager()
    recipe_manager = recipe.RecipeManager(sync_manager.list_recipes())

    setup_autocomplete(recipe_manager)

    if len(sys.argv) < 2:
        # Modo interativo
        print("Modo interativo do gerenciador de programas. Digite 'exit' para sair.")
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
    else:
        # Modo CLI direto
        main_command(sys.argv[1:], sync_manager, recipe_manager)

def main_command(args, sync_manager, recipe_manager):
    if not args:
        print("Erro: nenhum comando informado.")
        return

    cmd = args[0]
    cmd_args = args[1:]

    try:
        if cmd == "sync":
            sync_manager.sync_repo()
            print("Repositório sincronizado com sucesso!")

        elif cmd == "list":
            recipes = recipe_manager.list_recipes()
            print("Receitas disponíveis:")
            for r in recipes:
                print(f" - {r.name}")

        elif cmd == "install":
            if not cmd_args:
                print("Erro: informe a receita para instalar.")
                return
            rec_name = cmd_args[0]
            rec = recipe_manager.get_recipe(rec_name)
            if not rec:
                print(f"Receita '{rec_name}' não encontrada.")
                return
            if confirm(f"Deseja instalar {rec_name}?"):
                install.install_recipe(rec)
                print(f"{rec_name} instalado com sucesso!")

        elif cmd == "remove":
            if not cmd_args:
                print("Erro: informe a receita para remover.")
                return
            rec_name = cmd_args[0]
            rec = recipe_manager.get_recipe(rec_name)
            if not rec:
                print(f"Receita '{rec_name}' não encontrada.")
                return
            if confirm(f"Deseja remover {rec_name}?"):
                remove.remove_recipe(rec)
                print(f"{rec_name} removido com sucesso!")

        elif cmd == "update":
            update.update_all()
            print("Atualização concluída!")

        elif cmd == "upgrade":
            upgrade.upgrade_system()
            print("Sistema atualizado!")

        elif cmd == "download":
            if not cmd_args:
                print("Erro: informe a receita para download.")
                return
            rec_name = cmd_args[0]
            rec = recipe_manager.get_recipe(rec_name)
            if rec:
                download.download_recipe(rec)
                print(f"{rec_name} baixado com sucesso!")
            else:
                print(f"Receita '{rec_name}' não encontrada.")

        elif cmd == "extract":
            if not cmd_args:
                print("Erro: informe a receita para extrair.")
                return
            rec_name = cmd_args[0]
            rec = recipe_manager.get_recipe(rec_name)
            if rec:
                extract.extract_recipe(rec)
                print(f"{rec_name} extraído com sucesso!")
            else:
                print(f"Receita '{rec_name}' não encontrada.")

        elif cmd == "patch":
            patch.apply_patches()
            print("Patches aplicados com sucesso!")

        elif cmd == "dependencies":
            dependency.check_dependencies()
            print("Verificação de dependências concluída!")

        elif cmd == "sandbox":
            sandbox.run_sandbox()
            print("Sandbox executado com sucesso!")

        elif cmd == "hooks":
            hooks.run_hooks()
            print("Hooks executados com sucesso!")

        elif cmd == "uses":
            uses.show_uses()
            print("Exibição de usos concluída!")

        else:
            print(f"Comando '{cmd}' não reconhecido.")

    except Exception as e:
        logs.log_error(f"Erro ao executar {cmd}: {e}")
        print(f"Erro: {e}")

if __name__ == "__main__":
    main()
