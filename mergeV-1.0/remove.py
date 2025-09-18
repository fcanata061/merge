#remove.py refatorado com suporte completo a hooks
class Remover:
    def __init__(self, install_prefix: str = '/usr/local', dry_run: bool = False, silent: bool = False):
        self.install_prefix = install_prefix
        self.dry_run = dry_run
        self.silent = silent

    def remove_package(self, package: Recipe) -> bool:
        sb = Sandbox(install_prefix=self.install_prefix)
        hooks = HooksManager(sb, dry_run=self.dry_run, silent=self.silent)
        success = True
        try:
            # Pre-remove hooks
            hooks.run_hooks(package.hooks.get('pre_remove', []))

            # Remove files (simulação simplificada)
            package_dir = os.path.join(self.install_prefix, package.name)
            if self.dry_run:
                info(f'DRY-RUN: Would remove directory {package_dir}')
            else:
                if os.path.exists(package_dir):
                    import shutil
                    shutil.rmtree(package_dir)
                info(f'Package {package.name} removed successfully')

            # Post-remove hooks
            hooks.run_hooks(package.hooks.get('post_remove', []))

        except Exception as e:
            error(f'Removal failed for {package.name}: {e}')
            success = False

        sb.cleanup()
        return success
