import os
import shutil
import asyncio
import subprocess
import json
import time
from typing import List, Optional, Callable
from logs import stage, info, warn, error

class Sandbox:
    _instances = {}

    def __init__(self, name: str = None, base_dir: Optional[str] = None, use_fakeroot: bool = True, dry_run: bool = False):
        """
        :param name: Nome do sandbox (para múltiplos sandboxes isolados)
        :param base_dir: Diretório base do sandbox
        :param use_fakeroot: Executa comandos via fakeroot
        :param dry_run: Se True, apenas simula ações
        """
        self.name = name or f"sandbox_{len(Sandbox._instances)+1}"
        self.base_dir = base_dir or f'/tmp/merge_sandbox_{self.name}_{os.getpid()}'
        self.use_fakeroot = use_fakeroot
        self.dry_run = dry_run
        self.global_pre_hooks: List[Callable] = []
        self.global_post_hooks: List[Callable] = []
        os.makedirs(self.base_dir, exist_ok=True)
        Sandbox._instances[self.name] = self
        stage(f'Sandbox "{self.name}" created at {self.base_dir}')

    # ==========================
    # Comandos
    # ==========================
    async def run_command(
        self,
        command: List[str],
        cwd: Optional[str] = None,
        capture_output: bool = True,
        pre_hook: Optional[Callable] = None,
        post_hook: Optional[Callable] = None,
        timeout: Optional[int] = 300
    ) -> int:
        """Executa um comando dentro do sandbox com suporte a timeout e hooks."""
        cwd = cwd or self.base_dir
        cmd = command.copy()
        if self.use_fakeroot:
            cmd = ['fakeroot'] + cmd

        # Hooks globais e específicos
        for hook in self.global_pre_hooks:
            await self._maybe_async_hook(hook, cmd)
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
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            except asyncio.TimeoutError:
                process.kill()
                warn(f'Command {" ".join(cmd)} timed out after {timeout}s')
                return -1

            if capture_output:
                if stdout: info(f'[stdout] {stdout.decode()}')
                if stderr: warn(f'[stderr] {stderr.decode()}')

            for hook in self.global_post_hooks:
                await self._maybe_async_hook(hook, cmd, process.returncode)
            if post_hook:
                await self._maybe_async_hook(post_hook, cmd, process.returncode)

            return process.returncode
        except Exception as e:
            error(f'Failed to execute command {" ".join(cmd)}: {e}')
            return -1

    async def run_commands_parallel(self, commands: List[List[str]], cwd: Optional[str] = None) -> List[int]:
        tasks = [self.run_command(cmd, cwd=cwd) for cmd in commands]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r if isinstance(r, int) else -1 for r in results]

    # ==========================
    # Gerenciamento de arquivos
    # ==========================
    async def copy_to_sandbox(self, src: str, dest_name: Optional[str] = None) -> str:
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

    # ==========================
    # Limpeza
    # ==========================
    async def cleanup(self, force: bool = True):
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

    # ==========================
    # Hooks globais
    # ==========================
    def add_global_pre_hook(self, hook: Callable):
        self.global_pre_hooks.append(hook)

    def add_global_post_hook(self, hook: Callable):
        self.global_post_hooks.append(hook)

    # ==========================
    # Helpers internos
    # ==========================
    async def _maybe_async_hook(self, hook: Callable, *args, **kwargs):
        if asyncio.iscoroutinefunction(hook):
            await hook(*args, **kwargs)
        else:
            hook(*args, **kwargs)
