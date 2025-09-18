import os
import subprocess
from .config import cfg
from .logs import log
from pathlib import Path

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


def prepare_sandbox(pkg_name):
    """Cria diretório temporário para o sandbox do pacote"""
    workdir = cfg.get("global", "workdir")
    sandbox_dir = os.path.join(workdir, f"sandbox_{pkg_name}")
    os.makedirs(sandbox_dir, exist_ok=True)
    return sandbox_dir


def run_in_sandbox(commands, pkg_name):
    """
    Executa comandos em um sandbox isolado usando unshare + chroot mínimo.
    Retorna True se todos comandos rodarem com sucesso.
    """
    sandbox_dir = prepare_sandbox(pkg_name)
    workdir = cfg.get("global", "workdir")

    # Copia o código-fonte para o sandbox
    srcdir = os.path.join(workdir, pkg_name)
    if not os.path.exists(srcdir):
        stage_msg("SANDBOX", f"Diretório fonte {srcdir} não existe!", RED)
        return False

    # Limpando sandbox antigo
    if os.listdir(sandbox_dir):
        subprocess.run(f"rm -rf {sandbox_dir}/*", shell=True)

    subprocess.run(f"cp -r {srcdir}/* {sandbox_dir}/", shell=True, check=True)

    try:
        for cmd in commands:
            stage_msg("SANDBOX", f"Executando: {cmd} ... ", CYAN, end="")
            subprocess.run(
                f"unshare -pf --mount-proc chroot {sandbox_dir} /bin/bash -c '{cmd}'",
                shell=True,
                check=True
            )
            print(f"{GREEN}[OK]{RESET}")
        log(f"Sandbox concluída para {pkg_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"{RED}[FAIL]{RESET}")
        stage_msg("SANDBOX", f"Erro no sandbox para {pkg_name}: {e}", RED)
        log(f"Erro no sandbox para {pkg_name}: {e}")
        return False
