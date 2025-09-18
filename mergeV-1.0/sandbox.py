import os
import subprocess
import tempfile
import shutil
from typing import List
from logs import stage, info, warn, error

class Sandbox:
    def __init__(self, base_dir: str = None, use_fakeroot: bool = True):
        self.base_dir = base_dir or tempfile.mkdtemp(prefix='merge_sandbox_')
        self.use_fakeroot = use_fakeroot
        os.makedirs(self.base_dir, exist_ok=True)
        stage(f'Sandbox created at {self.base_dir}')

    def run_command(self, command: List[str], cwd: str = None, capture_output: bool = False) -> int:
        """Executa um comando dentro do sandbox de forma segura."""
        cwd = cwd or self.base_dir
        if self.use_fakeroot:
            command = ['fakeroot'] + command
        stage(f'Executing command: {" ".join(command)}')
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                check=True,
                capture_output=capture_output,
                text=True
            )
            if capture_output:
                info(f'Command output:\n{result.stdout}')
            return result.returncode
        except subprocess.CalledProcessError as e:
            error(f'Command failed with code {e.returncode}\n{e.stderr if e.stderr else ""}')
            return e.returncode

    def copy_to_sandbox(self, src: str, dest_name: str = None) -> str:
        """Copia arquivo ou diretório para dentro do sandbox."""
        dest_name = dest_name or os.path.basename(src)
        dest_path = os.path.join(self.base_dir, dest_name)
        try:
            if os.path.isdir(src):
                shutil.copytree(src, dest_path)
            else:
                shutil.copy2(src, dest_path)
            info(f'Copied {src} to sandbox at {dest_path}')
            return dest_path
        except Exception as e:
            error(f'Failed to copy {src} to sandbox: {e}')
            return ''

    def cleanup(self):
        """Remove todo o sandbox do sistema."""
        try:
            shutil.rmtree(self.base_dir)
            stage(f'Sandbox {self.base_dir} removed')
        except Exception as e:
            warn(f'Failed to remove sandbox {self.base_dir}: {e}')

# Teste rápido
if __name__ == '__main__':
    sb = Sandbox()
    sb.run_command(['echo', 'Hello from sandbox'], capture_output=True)
    tmp_file = sb.copy_to_sandbox('/etc/hosts')
    print('Copied file path:', tmp_file)
    sb.cleanup()
