import configparser

CONFIG_PATH = "/etc/merge.conf"

class MergeConfig:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read(CONFIG_PATH)

    def get(self, section, option, fallback=None):
        return self.config.get(section, option, fallback=fallback)

cfg = MergeConfig()
