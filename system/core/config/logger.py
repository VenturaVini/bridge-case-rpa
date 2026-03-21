import os
import logging
import json
from datetime import datetime
from pathlib import Path

# raiz do projeto pra montar caminho absoluto dos logs
RAIZ = str(Path(__file__).parent.parent.parent.parent)

# pasta e arquivo unico de log
PASTA_LOG = os.path.join(RAIZ, 'system', 'data', 'logs')
ARQUIVO_LOG = os.path.join(PASTA_LOG, 'app.log')

# cria a pasta se nao existir
os.makedirs(PASTA_LOG, exist_ok=True)


class JsonFormatter(logging.Formatter):
    '''Formata os logs em JSON pra ficar facil de ler e rastrear.'''

    def format(self, record):
        log = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "nivel": record.levelname,
            "modulo": record.name,
            "arquivo": record.filename,
            "funcao": record.funcName,
            "linha": record.lineno,
            "mensagem": record.getMessage()
        }

        if record.exc_info:
            log['erro'] = self.formatException(record.exc_info)

        return json.dumps(log, ensure_ascii=False)


# handler unico pro arquivo — todos os modulos escrevem no mesmo app.log
_formatador = JsonFormatter()

_handler_arquivo = logging.FileHandler(ARQUIVO_LOG, encoding='utf-8')
_handler_arquivo.setLevel(logging.DEBUG)
_handler_arquivo.setFormatter(_formatador)

_handler_console = logging.StreamHandler()
_handler_console.setLevel(logging.DEBUG)
_handler_console.setFormatter(_formatador)


def setup_logger(nome_modulo: str) -> logging.Logger:
    '''
    Cria um logger que escreve no console e num arquivo unico (app.log).

    Args:
        nome_modulo: nome que aparece no campo "modulo" do log

    Returns:
        logger configurado
    '''
    logger = logging.getLogger(nome_modulo)

    # se ja tem handler, nao duplica
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)
    logger.addHandler(_handler_console)
    logger.addHandler(_handler_arquivo)

    return logger
