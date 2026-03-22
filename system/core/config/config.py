import os
from pathlib import Path
from dotenv import load_dotenv

RAIZ = str(Path(__file__).parent.parent.parent.parent)


def carregar_config() -> dict:
    '''
    Puxa as configuracoes do .env e monta o dicionario.

    Returns:
        dict com todas as configs do projeto
    '''
    load_dotenv(override=True)

    config = {
        # raiz do projeto
        "raiz": RAIZ,

        # geral
        "pasta_dados": os.path.join(RAIZ, "system", "data"),
        "nivel_log": os.getenv("NIVEL_LOG", "INFO"),

        # modulo A - yahoo
        "yahoo_url": os.getenv("YAHOO_URL", "https://news.yahoo.com"),
        "yahoo_timeout": int(os.getenv("YAHOO_TIMEOUT")),
        "yahoo_headless": os.getenv("yahoo_headless"),


         # modulo C - gmail
        "gmail_usuario": os.getenv("GMAIL_USUARIO"),
        "gmail_senha_app": os.getenv("GMAIL_SENHA_APP"),
        "gmail_servidor": os.getenv("GMAIL_SERVIDOR"),
        "gmail_porta": int(os.getenv("GMAIL_PORTA")),
        "filtro_assunto": os.getenv("FILTRO_ASSUNTO"),
        "pasta_validos": os.path.join(RAIZ, "system", "data", "inbox", "valid"),
        "pasta_rejeitados": os.path.join(RAIZ, "system", "data", "inbox", "rejected"),

        # modulo D - pdf
        "pasta_saida_xlsx": os.getenv("PASTA_SAIDA_XLSX"),
        
        # uipath 
        "orchestrator_url": os.getenv("ORCHESTRATOR_URL"),
        "orchestrator_account": os.getenv("ORCHESTRATOR_ACCOUNT_NAME"),
        "orchestrator_tenant": os.getenv("ORCHESTRATOR_TENANT"),
        "orchestrator_client_id": os.getenv("ORCHESTRATOR_CLIENT_ID"),
        "orchestrator_client_secret": os.getenv("ORCHESTRATOR_CLIENT_SECRET"),
        "orchestrator_folder_id": os.getenv("ORCHESTRATOR_FOLDER_ID"),

        # queues
        "fila_modulo_a": os.getenv("FILA_MODULO_A", "Bridge_Modulo_A"),
        "fila_modulo_b": os.getenv("FILA_MODULO_B", "Bridge_Modulo_B"),
        "fila_modulo_c": os.getenv("FILA_MODULO_C", "Bridge_Modulo_C"),
        "fila_modulo_d": os.getenv("FILA_MODULO_D", "Bridge_Modulo_D"),
    }

    return config
