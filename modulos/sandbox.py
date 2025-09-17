import os
import shutil
import subprocess
from .config import cfg
from .logs import log

SANDBOX_BASE = cfg.get("global", "sandbox_path")
INSTALL_PATH = cfg.get("global", "install_path")

def run_in_sandbox(commands, package_name):
    """
    Executa os comandos de instalação dentro de um sandbox isolado.
    Se todos os comandos forem bem-sucedidos, copia o conteúdo
    do sandbox para o diretório final de instalação.
    """
    # Caminho do sandbox para este pacote
    sandbox_dir = os.path.join(SANDBOX_BASE, package_name)
    
    # Limpa sandbox antigo se existir
    if os.path.exists(sandbox_dir):
        shutil.rmtree(sandbox_dir)
    os.makedirs(sandbox_dir, exist_ok=True)

    # Variáveis de ambiente para o sandbox
    env = os.environ.copy()
    env["MERGE_SANDBOX"] = sandbox_dir
    env["INSTALL_PATH"] = INSTALL_PATH

    log(f"Iniciando sandbox para '{package_name}' em {sandbox_dir}")

    # Executa todos os comandos da recipe
    for cmd in commands:
        cmd_expanded = cmd.replace("{install_path}", INSTALL_PATH)
        try:
            result = subprocess.run(cmd_expanded, shell=True, check=True, cwd=sandbox_dir, env=env,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            log(f"[{package_name}] {cmd_expanded}\nSaída: {result.stdout.strip()}")
        except subprocess.CalledProcessError as e:
            log(f"ERRO no sandbox de '{package_name}': {cmd_expanded}\n{e.stderr.strip()}")
            print(f"Falha ao executar comando no sandbox: {cmd_expanded}")
            return False

    # Copia do sandbox para o install_path
    dest_dir = os.path.join(INSTALL_PATH, package_name)
    if os.path.exists(dest_dir):
        shutil.rmtree(dest_dir)
    try:
        shutil.copytree(sandbox_dir, dest_dir)
        log(f"Pacote '{package_name}' movido do sandbox para {dest_dir}")
    except Exception as e:
        log(f"Falha ao mover '{package_name}' do sandbox para {INSTALL_PATH}: {e}")
        print(f"Erro ao finalizar instalação de '{package_name}'")
        return False

    # Limpa sandbox após instalação
    shutil.rmtree(sandbox_dir, ignore_errors=True)
    log(f"Sandbox para '{package_name}' limpo com sucesso")

    return True
