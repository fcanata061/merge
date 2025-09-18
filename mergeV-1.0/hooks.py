import os
import subprocess
import asyncio
import json
from datetime import datetime
from sandbox import Sandbox
from logs import info, warn, error

class HooksManager:
    def __init__(self, sandbox: Sandbox, dry_run: bool = False, silent: bool = False, log_level: str = 'INFO'):
        self.sandbox = sandbox
        self.dry_run = dry_run
        self.silent = silent
        self.log_level = log_level

    def log(self, level: str, message: str):
        if self.silent:
            return
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] [{level}] {message}")

    def validate_command(self, cmd: str) -> bool:
        # Validação simples: verificar se o comando não está vazio e se o arquivo existe
        if not cmd:
            self.log('ERROR', 'Comando vazio detectado.')
            return False
        if not os.path.isfile(cmd.split()[0]):
            self.log('ERROR', f'Arquivo não encontrado: {cmd.split()[0]}')
            return False
        return True

    async def run_command(self, cmd: str):
        if self.dry_run:
            self.log('INFO', f'DRY-RUN: {cmd}')
            return
        if not self.validate_command(cmd):
            return
        try:
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            if process.returncode == 0:
                self.log('INFO', f'Comando executado com sucesso: {cmd}')
                if stdout:
                    self.log('INFO', f'Saída: {stdout.decode()}')
            else:
                self.log('ERROR', f'Erro ao executar comando: {cmd}')
                if stderr:
                    self.log('ERROR', f'Erro: {stderr.decode()}')
        except Exception as e:
            self.log('ERROR', f'Falha ao executar comando {cmd}: {e}')

    async def run_hooks(self, hooks_list: list):
        for hook in hooks_list:
            await self.run_command(hook)

    async def run_all_hooks(self, recipe):
        await self.run_hooks(recipe.hooks.get('pre_configure', []))
        await self.run_hooks(recipe.hooks.get('post_configure', []))
        await self.run_hooks(recipe.hooks.get('pre_compile', []))
        await self.run_hooks(recipe.hooks.get('post_compile', []))
        await self.run_hooks(recipe.hooks.get('pre_install', []))
        await self.run_hooks(recipe.hooks.get('post_install', []))

    async def run_remove_hooks(self, package):
        await self.run_hooks(package.hooks.get('pre_remove', []))
        await self.run_hooks(package.hooks.get('post_remove', []))

    def load_hooks_from_file(self, file_path: str):
        if not os.path.exists(file_path):
            self.log('ERROR', f'Arquivo de hooks não encontrado: {file_path}')
            return []
        try:
            with open(file_path, 'r') as file:
                hooks = json.load(file)
            self.log('INFO', f'Hooks carregados de {file_path}')
            return hooks
        except json.JSONDecodeError:
            self.log('ERROR', f'Erro ao decodificar JSON no arquivo: {file_path}')
            return []
