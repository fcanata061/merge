import os
import json
import asyncio
from typing import List, Dict, Callable, Optional, Tuple
import aiofiles
import shutil
import datetime

BASE_DIR = os.path.expanduser("~/.merge")
USES_FILE = os.path.join(BASE_DIR, 'uses.json')
BACKUP_FILE = os.path.join(BASE_DIR, 'uses_backup.json')

# ----------------------------
# Logs simples e estruturados
# ----------------------------
def log(level: str, message: str):
    ts = datetime.datetime.now().isoformat()
    print(f"[{ts}] [{level.upper()}] {message}")

info = lambda msg: log("info", msg)
warn = lambda msg: log("warn", msg)
error = lambda msg: log("error", msg)

# ----------------------------
# UseManager avançado
# ----------------------------
class UseManager:
    def __init__(self, on_change: Optional[Callable[[str, str, bool], None]] = None):
        self.flags: Dict[str, List[str]] = {}
        self.history: List[Tuple[str, str, bool]] = []  # (package, flag, enabled)
        self.future: List[Tuple[str, str, bool]] = []
        self._lock = asyncio.Lock()
        self.on_change = on_change
        asyncio.run(self._load_uses())

    async def _load_uses(self):
        """Carrega as USE flags do arquivo JSON, criando backup se necessário."""
        async with self._lock:
            try:
                async with aiofiles.open(USES_FILE, 'r', encoding='utf-8') as f:
                    data = await f.read()
                    self.flags = json.loads(data)
            except (FileNotFoundError, json.JSONDecodeError):
                warn("Arquivo de USE flags não encontrado ou corrompido. Criando novo.")
                self.flags = {}
                await self._save_uses()

    async def _save_uses(self):
        """Salva flags com backup automático."""
        async with self._lock:
            try:
                os.makedirs(BASE_DIR, exist_ok=True)
                # Backup automático
                if os.path.exists(USES_FILE):
                    shutil.copy2(USES_FILE, BACKUP_FILE)
                async with aiofiles.open(USES_FILE, 'w', encoding='utf-8') as f:
                    await f.write(json.dumps(self.flags, indent=2))
            except Exception as e:
                error(f"Falha ao salvar USE flags: {e}")
                # Rollback automático
                if os.path.exists(BACKUP_FILE):
                    shutil.copy2(BACKUP_FILE, USES_FILE)

    def get_flags(self, package_name: str) -> List[str]:
        return self.flags.get(package_name, [])

    async def enable_flag(self, package_name: str, flag: str):
        async with self._lock:
            if package_name not in self.flags:
                self.flags[package_name] = []
            if flag not in self.flags[package_name]:
                self.flags[package_name].append(flag)
                self.history.append((package_name, flag, True))
                self.future.clear()
                info(f'Habilitada flag "{flag}" para "{package_name}".')
                if self.on_change:
                    self.on_change(package_name, flag, True)
            await self._save_uses()

    async def disable_flag(self, package_name: str, flag: str):
        async with self._lock:
            if package_name in self.flags and flag in self.flags[package_name]:
                self.flags[package_name].remove(flag)
                self.history.append((package_name, flag, False))
                self.future.clear()
                info(f'Desabilitada flag "{flag}" para "{package_name}".')
                if self.on_change:
                    self.on_change(package_name, flag, False)
            await self._save_uses()

    async def batch_update_flags(self, updates: Dict[str, Dict[str, bool]]):
        """Atualiza em lote de forma assíncrona, preservando histórico."""
        tasks = []
        for pkg, flags in updates.items():
            for flag, enable in flags.items():
                if enable:
                    tasks.append(self.enable_flag(pkg, flag))
                else:
                    tasks.append(self.disable_flag(pkg, flag))
        await asyncio.gather(*tasks)

    # ----------------------------
    # Undo/Redo avançado
    # ----------------------------
    async def undo(self):
        async with self._lock:
            if not self.history:
                warn("Nada para desfazer")
                return
            pkg, flag, enabled = self.history.pop()
            if enabled:
                self.flags[pkg].remove(flag)
            else:
                if pkg not in self.flags:
                    self.flags[pkg] = []
                self.flags[pkg].append(flag)
            self.future.append((pkg, flag, enabled))
            info(f"Undo: {'desabilitada' if enabled else 'habilitada'} flag {flag} para {pkg}")
            await self._save_uses()

    async def redo(self):
        async with self._lock:
            if not self.future:
                warn("Nada para refazer")
                return
            pkg, flag, enabled = self.future.pop()
            if enabled:
                if pkg not in self.flags:
                    self.flags[pkg] = []
                self.flags[pkg].append(flag)
            else:
                self.flags[pkg].remove(flag)
            self.history.append((pkg, flag, enabled))
            info(f"Redo: {'habilitada' if enabled else 'desabilitada'} flag {flag} para {pkg}")
            await self._save_uses()

    # ----------------------------
    # Exportação para auditoria
    # ----------------------------
    async def export_flags(self, path: str, fmt: str = "json"):
        async with self._lock:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            data = self.flags
            if fmt.lower() == "json":
                async with aiofiles.open(path, 'w', encoding='utf-8') as f:
                    await f.write(json.dumps(data, indent=2))
            elif fmt.lower() == "yaml":
                try:
                    import yaml
                    async with aiofiles.open(path, 'w', encoding='utf-8') as f:
                        await f.write(yaml.safe_dump(data))
                except ImportError:
                    error("PyYAML não instalado, não foi possível exportar para YAML")
            info(f"Flags exportadas para {path} em {fmt.upper()}")
