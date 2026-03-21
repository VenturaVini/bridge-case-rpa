import os
from pathlib import Path
from dotenv import load_dotenv

# raiz do projeto (bridge-case-rpa-main), nao depende de onde roda o script
RAIZ = str(Path(__file__).parent.parent.parent.parent)


def carregar_config() -> dict:
    '''
    Puxa as configuracoes do .env e monta o dicionario.

    Returns:
        dict com todas as configs do projeto
    '''
    load_dotenv(override=True)

    config = {
        # raiz do projeto pra montar caminhos absolutos
        "raiz": RAIZ,

        # geral
        "pasta_dados": os.path.join(RAIZ, "system", "data"),
        "nivel_log": os.getenv("NIVEL_LOG", "INFO"),

        # modulo A - yahoo
        "yahoo_url": os.getenv("YAHOO_URL", "https://news.yahoo.com"),
        "yahoo_timeout": int(os.getenv("YAHOO_TIMEOUT")),
        "yahoo_headless": os.getenv("yahoo_headless"),

        # queues
        "fila_modulo_a": os.getenv("FILA_MODULO_A", "Bridge_Modulo_A"),
        "fila_modulo_b": os.getenv("FILA_MODULO_B", "Bridge_Modulo_B"),
        "fila_modulo_c": os.getenv("FILA_MODULO_C", "Bridge_Modulo_C"),
        "fila_modulo_d": os.getenv("FILA_MODULO_D", "Bridge_Modulo_D"),
    }

    return config
