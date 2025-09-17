import os
import subprocess
from .config import cfg
from .logs import log

SANDBOX_PATH = cfg.get("global", "sandbox_path")

def run_in_sandbox(commands, package_name):
    """
    Executa comandos de instalação dentro de um sandbox temporário.
    """
    sandbox_dir = os.path.join(SANDBOX_PATH, package_name)
    os.makedirs(sandbox_dir, exist_ok=True)

    install_path = cfg.get("global", "install_path")
    env = os.environ.copy()
    env["MERGE_SANDBOX"] = sandbox_dir
    env["INSTALL_PATH"] = install_path

    for cmd in commands:
        cmd = cmd.replace("{install_path}", install_path)
        try:
            subprocess.run(cmd, shell=True, check=True, cwd=sandbox_dir, env=env)
        except subprocess.CalledProcessError:
            log(f"Erro ao executar comando '{cmd}' no sandbox de {package_name}")
            return False
    return True
