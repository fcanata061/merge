# merge_autocomplete.py
# Script para habilitar autocomplete do Merge CLI (Bash/Zsh/Fish)

import sys
import argcomplete
import argparse
from main import COMMAND_MAP
from recipe import list_recipes

parser = argparse.ArgumentParser(description='Merge CLI Autocomplete')
parser.add_argument('command', nargs='?')
parser.add_argument('package', nargs='?')

# Lista de pacotes para autocomplete
recipes = [r.name for r in list_recipes()]

def completer(prefix, **kwargs):
    if not kwargs['parsed_args'].command:
        # Sugere comandos
        return [c for c in COMMAND_MAP.keys() if c.startswith(prefix)]
    else:
        # Sugere pacotes
        return [p for p in recipes if p.startswith(prefix)]

argcomplete.autocomplete(parser, completer=completer)
args = parser.parse_args()
