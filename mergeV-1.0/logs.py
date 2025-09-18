import sys
import datetime

# ANSI colors
RESET = '\033[0m'
BOLD = '\033[1m'
CYAN = '\033[36m'
GREEN = '\033[32m'
YELLOW = '\033[33m'
RED = '\033[31m'
MAGENTA = '\033[35m'

# Log levels
LEVELS = {
    'INFO': CYAN,
    'SUCCESS': GREEN,
    'WARN': YELLOW,
    'ERROR': RED,
    'STAGE': MAGENTA
}

# Optional: log to file
LOG_FILE = None

def set_log_file(path):
    global LOG_FILE
    LOG_FILE = path

def _write(message: str):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    full_message = f'[{timestamp}] {message}'
    print(full_message)
    if LOG_FILE:
        with open(LOG_FILE, 'a') as f:
            f.write(full_message + '\n')


def log(message: str, level: str = 'INFO'):
    color = LEVELS.get(level.upper(), '')
    _write(f'{color}{level.upper():<7}{RESET} {message}')


def info(message: str):
    log(message, 'INFO')

def success(message: str):
    log(message, 'SUCCESS')

def warn(message: str):
    log(message, 'WARN')

def error(message: str):
    log(message, 'ERROR')

def stage(message: str):
    log(message, 'STAGE')

# Example usage
if __name__ == '__main__':
    stage('Starting Merge')
    info('Loading recipes')
    success('Recipe installed successfully')
    warn('Optional dependency missing')
    error('Failed to apply patch')
