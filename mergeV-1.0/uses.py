import os
import json
from typing import List
from config import BASE_DIR, STATE_FILE
from logs import info, warn

# Estrutura para armazenar USE flags ativas
USES_FILE = os.path.join(BASE_DIR, 'uses.json')

# Carrega ou cria arquivo de USE flags
if not os.path.exists(USES_FILE):
    with open(USES_FILE, 'w') as f:
        json.dump({}, f)

class UseManager:
    def __init__(self):
        self.flags = self._load_uses()

    def _load_uses(self) -> dict:
        try:
            with open(USES_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            warn('Uses file corrupted, resetting')
            return {}

    def save(self):
        with open(USES_FILE, 'w') as f:
            json.dump(self.flags, f, indent=2)

    def get_flags(self, package_name: str) -> List[str]:
        return self.flags.get(package_name, [])

    def enable_flag(self, package_name: str, flag: str):
        if package_name not in self.flags:
            self.flags[package_name] = []
        if flag not in self.flags[package_name]:
            self.flags[package_name].append(flag)
            info(f'Enabled USE flag {flag} for {package_name}')
        self.save()

    def disable_flag(self, package_name: str, flag: str):
        if package_name in self.flags and flag in self.flags[package_name]:
            self.flags[package_name].remove(flag)
            info(f'Disabled USE flag {flag} for {package_name}')
        self.save()

# Teste rápido
if __name__ == '__main__':
    um = UseManager()
    um.enable_flag('foo', 'gui')
    um.enable_flag('foo', 'ssl')
    print(um.get_flags('foo'))
    um.disable_flag('foo', 'gui')
    print(um.get_flags('foo'))
