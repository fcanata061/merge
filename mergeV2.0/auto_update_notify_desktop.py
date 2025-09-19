import re
import requests
import json
import subprocess
from urllib.parse import urlparse
from recipe import RecipeManager
from logs import stage, info, warn, success

class AutoUpdateNotifier:
    """Notificador de novas versões do Merge (somente aviso)"""
    def __init__(self, recipe_manager: RecipeManager, report_file="update_report.json"):
        self.recipe_manager = recipe_manager
        self.report_file = report_file
        self.updates = []

    def get_latest_version_tarball(self, url: str):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            versions = re.findall(r'(\d+\.\d+(\.\d+)*)', response.text)
            versions = sorted(set(versions), key=lambda v: list(map(int, v.split('.'))))
            return versions[-1] if versions else None
        except Exception as e:
            warn(f"Não foi possível verificar versão em {url}: {e}")
            return None

    def get_latest_version_git(self, git_url: str):
        try:
            url = git_url.replace("git+", "")
            if "github.com" in url:
                repo_path = urlparse(url).path.strip("/")
                api_url = f"https://api.github.com/repos/{repo_path}/tags"
                r = requests.get(api_url, timeout=10)
                r.raise_for_status()
                tags = [t["name"] for t in r.json()]
                tags = sorted(tags, key=lambda v: [int(x) for x in re.findall(r'\d+', v)])
                return tags[-1] if tags else None
            return None
        except Exception as e:
            warn(f"Não foi possível verificar Git {git_url}: {e}")
            return None

    def notify_desktop(self, title: str, message: str):
        try:
            subprocess.run(["notify-send", title, message])
        except Exception as e:
            warn(f"Não foi possível enviar notificação: {e}")

    def check_updates(self):
        stage("Verificando novas versões dos pacotes (somente notificação)...")
        for recipe in self.recipe_manager.list_recipes():
            latest_version = None
            for src in recipe.src_uri:
                if src.startswith("git+"):
                    latest_version = self.get_latest_version_git(src)
                else:
                    url_base = "/".join(src.split("/")[:-1]) + "/"
                    latest_version = self.get_latest_version_tarball(url_base)
                if latest_version:
                    break

            if latest_version and latest_version != recipe.version:
                info(f"🚨 Novo disponível: {recipe.name} {latest_version} (instalada: {recipe.version})")
                self.updates.append({
                    "name": recipe.name,
                    "installed_version": recipe.version,
                    "latest_version": latest_version
                })
                self.notify_desktop(f"Merge Update: {recipe.name}", f"Nova versão disponível: {latest_version}")
            else:
                info(f"✅ {recipe.name} está atualizado ({recipe.version})")

        self.save_report()
        if self.updates:
            self.notify_desktop("Merge Update", f"{len(self.updates)} pacote(s) possuem atualizações disponíveis")
        else:
            self.notify_desktop("Merge Update", "Todos os pacotes estão atualizados")

    def save_report(self):
        try:
            with open(self.report_file, "w") as f:
                json.dump(self.updates, f, indent=4)
            success(f"Relatório salvo em {self.report_file}")
        except Exception as e:
            warn(f"Não foi possível salvar relatório: {e}")
