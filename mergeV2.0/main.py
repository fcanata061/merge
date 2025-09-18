#!/usr/bin/env python3
import sys
from merge import sync, recipe, install, remove, download, extract, upgrade, update, logs, hooks, patch, dependency, uses, sandbox, rootdir

def confirm(prompt="Deseja continuar? (s/n): "):
    """Confirmação do usuário com segurança."""
    if not sys.stdin.isatty():
        return True  # Assume sim em ambiente não interativo
    resp = input(prompt).strip().lower()
    return resp in ("s", "sim", "y", "yes")

def main():
    if len(sys.argv) < 2:
        print("Uso: main.py <comando> [args]")
        sys.exit(1)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    # Inicializa log
    logs.setup_logging()

    # Inicializa sync manager
    sync_manager = sync.SyncManager()

    # Carrega receitas
    recipe_manager = recipe.RecipeManager(sync_manager.list_recipes())

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
            if not args:
                print("Erro: informe o nome da receita para instalar.")
                sys.exit(1)
            rec_name = args[0]
            rec = recipe_manager.get_recipe(rec_name)
            if not rec:
                print(f"Receita '{rec_name}' não encontrada.")
                sys.exit(1)
            if confirm(f"Deseja instalar {rec_name}?"):
                install.install_recipe(rec)
                print(f"{rec_name} instalado com sucesso!")

        elif cmd == "remove":
            if not args:
                print("Erro: informe o nome da receita para remover.")
                sys.exit(1)
            rec_name = args[0]
            rec = recipe_manager.get_recipe(rec_name)
            if not rec:
                print(f"Receita '{rec_name}' não encontrada.")
                sys.exit(1)
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
            if not args:
                print("Erro: informe a receita para download.")
                sys.exit(1)
            rec_name = args[0]
            rec = recipe_manager.get_recipe(rec_name)
            if rec:
                download.download_recipe(rec)
                print(f"{rec_name} baixado com sucesso!")
            else:
                print(f"Receita '{rec_name}' não encontrada.")

        elif cmd == "extract":
            if not args:
                print("Erro: informe a receita para extrair.")
                sys.exit(1)
            rec_name = args[0]
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
            sys.exit(1)

    except Exception as e:
        logs.log_error(f"Erro ao executar {cmd}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
