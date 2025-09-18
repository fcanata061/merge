import os
import json
import asyncio
from typing import List, Dict
from config import BASE_DIR
from logs import info, warn, error

USES_FILE = os.path.join(BASE_DIR, 'uses.json')

class UseManager:
    def __init__(self):
        self.flags = self._load_uses()

    def _load_uses(self) -> Dict[str, List[str]]:
        """Carrega as USE flags do arquivo JSON."""
        try:
            with open(USES_FILE, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            warn('Arquivo de USE flags não encontrado ou corrompido. Criando novo arquivo.')
            return {}

    def save(self):
        """Salva as USE flags no arquivo JSON."""
        try:
            with open(USES_FILE, 'w') as f:
                json.dump(self.flags, f, indent=2)
        except IOError as e:
            error(f'Erro ao salvar USE flags: {e}')

    def get_flags(self, package_name: str) -> List[str]:
        """Retorna as USE flags ativas para um pacote."""
        return self.flags.get(package_name, [])

    def enable_flag(self, package_name: str, flag: str):
        """Habilita uma USE flag para um pacote."""
        if package_name not in self.flags:
            self.flags[package_name] = []
        if flag not in self.flags[package_name]:
            self.flags[package_name].append(flag)
            info(f'Habilitada a USE flag "{flag}" para o pacote "{package_name}".')
            self.save()

    def disable_flag(self, package_name: str, flag: str):
        """Desabilita uma USE flag para um pacote."""
        if package_name in self.flags and flag in self.flags[package_name]:
            self.flags[package_name].remove(flag)
            info(f'Desabilitada a USE flag "{flag}" para o pacote "{package_name}".')
            self.save()

    async def batch_update_flags(self, updates: Dict[str, Dict[str, bool]]):
        """Atualiza as USE flags em lote de forma assíncrona."""
        for package_name, flags in updates.items():
            for flag, enable in flags.items():
                if enable:
                    self.enable_flag(package_name, flag)
                else:
                    self.disable_flag(package_name, flag)
            await asyncio.sleep(0.1)  # Simula uma operação assíncrona

# Teste rápido
if __name__ == '__main__':
    um = UseManager()
    um.enable_flag('foo', 'gui')
    um.enable_flag('foo', 'ssl')
    print(um.get_flags('foo'))
    um.disable_flag('foo', 'gui')
    print(um.get_flags('foo'))
