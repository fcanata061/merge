import sys
from .install import install_package
from .remove import remove_package
from .repository import list_packages

def print_help():
    print("""
merge - Gerenciador de pacotes avançado
Comandos:
    install <pacote>   - Instala um pacote com dependências
    remove <pacote>    - Remove um pacote
    list               - Lista pacotes disponíveis
    help               - Mostra esta ajuda
""")

def main():
    if len(sys.argv) < 2:
        print_help()
        return

    cmd = sys.argv[1]

    if cmd == "install" and len(sys.argv) == 3:
        install_package(sys.argv[2])
    elif cmd == "remove" and len(sys.argv) == 3:
        remove_package(sys.argv[2])
    elif cmd == "list":
        for pkg in list_packages():
            print(pkg)
    else:
        print_help()

if __name__ == "__main__":
    main()
