import os
import shutil
import asyncio
from logs import info, warn, error, stage

class RootDirManager:
    def __init__(self, rootdir: str = '/mnt/merge-root', dry_run: bool = False, silent: bool = False):
        self.rootdir = rootdir
        self.dry_run = dry_run
        self.silent = silent

    async def prepare_rootdir(self):
        stage(f'Preparing rootdir at {self.rootdir}')

        # 1. Criar diretório root se não existir
        if not os.path.exists(self.rootdir):
            if self.dry_run:
                info(f'DRY-RUN: Would create {self.rootdir}')
            else:
                os.makedirs(self.rootdir, exist_ok=True)
            info(f'Created rootdir {self.rootdir}')

        # 2. Criar diretórios essenciais do sistema
        essential_dirs = ['bin', 'sbin', 'lib', 'lib64', 'usr/bin', 'usr/lib', 'usr/lib64', 'etc', 'proc', 'sys', 'dev', 'tmp', 'var', 'home']
        for d in essential_dirs:
            path = os.path.join(self.rootdir, d)
            if not os.path.exists(path):
                if self.dry_run:
                    info(f'DRY-RUN: Would create {path}')
                else:
                    os.makedirs(path, exist_ok=True)
                info(f'Created directory {path}')

        # 3. Copiar resolv.conf para permitir acesso a rede dentro do chroot
        resolv_src = '/etc/resolv.conf'
        resolv_dst = os.path.join(self.rootdir, 'etc', 'resolv.conf')
        if os.path.exists(resolv_src):
            if self.dry_run:
                info(f'DRY-RUN: Would copy {resolv_src} to {resolv_dst}')
            else:
                shutil.copy2(resolv_src, resolv_dst)
            info(f'Copied {resolv_src} to {resolv_dst}')
        else:
            warn(f'{resolv_src} does not exist, DNS may not work in chroot')

        # 4. Ajustar permissões corretas (ex.: tmp e var/tmp)
        tmp_dirs = [os.path.join(self.rootdir, 'tmp'), os.path.join(self.rootdir, 'var', 'tmp')]
        for tmp in tmp_dirs:
            if not os.path.exists(tmp):
                if self.dry_run:
                    info(f'DRY-RUN: Would create {tmp}')
                else:
                    os.makedirs(tmp, exist_ok=True)
            if self.dry_run:
                info(f'DRY-RUN: Would chmod 1777 {tmp}')
            else:
                os.chmod(tmp, 0o1777)
            info(f'Set permissions 1777 on {tmp}')

        # 5. Criar links simbólicos essenciais se necessário
        links = [("usr/bin", "bin"), ("usr/sbin", "sbin")]
        for target, link_name in links:
            link_path = os.path.join(self.rootdir, link_name)
            target_path = os.path.join(self.rootdir, target)
            if not os.path.exists(link_path):
                if self.dry_run:
                    info(f'DRY-RUN: Would create symlink {link_path} -> {target_path}')
                else:
                    os.symlink(target_path, link_path)
                info(f'Created symlink {link_path} -> {target_path}')

        info('Rootdir preparation completed successfully')
