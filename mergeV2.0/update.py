from recipe import RecipeManager
from logs import stage, info, success, warn
from auto_update_notify_desktop import AutoUpdateNotifier

class Updater:
    def __init__(self):
        self.recipe_manager = RecipeManager()

    def update(self, world=False, notify=True):
        stage("Iniciando processo de update...")
        self.fetch_repos()  # Atualiza listas de receitas locais

        if notify:
            notifier = AutoUpdateNotifier(self.recipe_manager)
            notifier.check_updates()

        stage("Update concluído.")

    def fetch_repos(self):
        info("Atualizando listas de pacotes dos repositórios...")
        # Lógica atual do Merge para baixar receitas ou atualizar repositórios
        success("Repositórios atualizados com sucesso.")
