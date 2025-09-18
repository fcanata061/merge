import os
import shutil
import asyncio
import subprocess
from typing import List, Optional, Callable
from logs import stage, info, warn, error

class Sandbox:
    def __init__(self, base_dir: Optional[str] = None, use_fakeroot: bool = True, dry_run: bool = False):
        """
        :param base_dir: Diretório base do sandbox. Se None, cria um temporário.
        :param use_fakeroot: Usa fakeroot nos comandos.
        :param dry_run: Se True, apenas loga as ações sem executá-las.
        """
        self.base_dir = base_dir or f'/tmp/merge_sandbox_{os.getpid()}'
        self.use_fakeroot = use_fakeroot
        self.dry_run = dry_run
        os.makedirs(self.base_dir, exist_ok=True)
        stage(f'Sandbox created at {self.base_dir}')

    async def run_command(self, command: List[str], cwd: Optional[str] = None,
                          capture_output: bool = True,
                          pre_hook: Optional[Callable] = None,
                          post_hook: Optional[Callable] = None) -> int:
        """
        Executa um comando dentro do sandbox.
        :param command: Lista do comando.
        :param cwd: Diretório de execução. Se None, usa sandbox base.
        :param capture_output: Se True, captura stdout/stderr.
        :param pre_hook: Função opcional executada antes do comando.
        :param post_hook: Função opcional executada após o comando.
        :return: Código de saída do comando.
        """
        cwd = cwd or self.base_dir
        cmd = command.copy()
        if self.use_fakeroot:
            cmd = ['fakeroot'] + cmd

        if pre_hook:
            await self._maybe_async_hook(pre_hook, cmd)

        stage(f'Executing command: {" ".join(cmd)} in {cwd}')

        if self.dry_run:
            info(f'DRY-RUN: Would execute: {" ".join(cmd)}')
            return 0

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE if capture_output else None,
                stderr=asyncio.subprocess.PIPE if capture_output else None,
            )
            stdout, stderr = await process.communicate()
            if capture_output:
                if stdout:
                    info(f'[stdout] {stdout.decode()}')
                if stderr:
                    warn(f'[stderr] {stderr.decode()}')

            if post_hook:
                await self._maybe_async_hook(post_hook, cmd, process.returncode)

            return process.returncode
        except Exception as e:
            error(f'Failed to execute command {" ".join(cmd)}: {e}')
            return -1

    async def run_commands_parallel(self, commands: List[List[str]], cwd: Optional[str] = None):
        """Executa múltiplos comandos em paralelo."""
        tasks = [self.run_command(cmd, cwd=cwd) for cmd in commands]
        results = await asyncio.gather(*tasks)
        return results

    async def copy_to_sandbox(self, src: str, dest_name: Optional[str] = None) -> str:
        """Copia arquivo ou diretório para dentro do sandbox."""
        dest_name = dest_name or os.path.basename(src)
        dest_path = os.path.join(self.base_dir, dest_name)
        if self.dry_run:
            info(f'DRY-RUN: Would copy {src} to {dest_path}')
            return dest_path

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

    async def cleanup(self, force: bool = True):
        """Remove o sandbox."""
        if not os.path.exists(self.base_dir):
            warn(f'Sandbox {self.base_dir} does not exist')
            return
        if self.dry_run:
            info(f'DRY-RUN: Would remove sandbox {self.base_dir}')
            return
        try:
            if force:
                shutil.rmtree(self.base_dir)
                stage(f'Sandbox {self.base_dir} removed')
            else:
                stage(f'Sandbox {self.base_dir} retained (force=False)')
        except Exception as e:
            warn(f'Failed to remove sandbox {self.base_dir}: {e}')

    async def _maybe_async_hook(self, hook: Callable, *args, **kwargs):
        """Executa hook que pode ser sync ou async."""
        if asyncio.iscoroutinefunction(hook):
            await hook(*args, **kwargs)
        else:
            hook(*args, **kwargs)
