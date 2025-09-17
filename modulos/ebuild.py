import os
import subprocess
from .config import cfg
from .logs import log

def run_ebuild(package_name):
    """
    Executa o script de instalação do pacote, chamado ebuild.sh
    localizado em /var/lib/merge/repo/<pacote>/ebuild.sh
    """
    repo_path = cfg.get("global", "repository_path")
    ebuild_file = os.path.join(repo_path, package_name, "ebuild.sh")
    if not os.path.exists(ebuild_file):
        log(f"Pacote {package_name} não possui ebuild.")
        return False

    try:
        subprocess.run(["/bin/bash", ebuild_file], check=True)
        log(f"Pacote {package_name} instalado com sucesso.")
        return True
    except subprocess.CalledProcessError:
        log(f"Falha ao instalar pacote {package_name}.")
        return False
