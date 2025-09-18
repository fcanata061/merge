import sys
from .install import install_with_resolver
from .remove import remove_package
from .repository import list_packages

def print_help():
    print("""
merge - Gerenciador de pacotes avançado

Comandos:
    install <pacote> [--mode <recipe|binary|dir>] [--source <caminho>]
        - Instala um pacote e todas as dependências em ordem topológica
        - --mode recipe   : usa recipe.yaml (sandbox)
        - --mode binary   : instala binário (tar.gz)
        - --mode dir      : instala diretório local usando fakeroot
        - --source PATH   : caminho do binário ou diretório (necessário para binary/dir)

    remove <pacote>           - Remove um pacote
    list                      - Lista pacotes disponíveis
    help                      - Mostra esta ajuda
""")

def main():
    if len(sys.argv) < 2:
        print_help()
        return

    cmd = sys.argv[1]

    if cmd == "install" and len(sys.argv) >= 3:
        package_name = sys.argv[2]
        mode = "recipe"
        source = None

        # Processa argumentos opcionais
        if "--mode" in sys.argv:
            mode_index = sys.argv.index("--mode") + 1
            if mode_index < len(sys.argv):
                mode = sys.argv[mode_index]

        if "--source" in sys.argv:
            source_index = sys.argv.index("--source") + 1
            if source_index < len(sys.argv):
                source = sys.argv[source_index]

        install_with_resolver(package_name, mode=mode, source_path=source)

    elif cmd == "remove" and len(sys.argv) == 3:
        remove_package(sys.argv[2])

    elif cmd == "list":
        for pkg in list_packages():
            print(pkg)

    else:
        print_help()

if __name__ == "__main__":
    main()
