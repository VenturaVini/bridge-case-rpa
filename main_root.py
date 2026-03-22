import json
from datetime import datetime
from system.core.config.config import carregar_config
from system.core.config.logger import setup_logger
from system.core.services.yahoo_service import YahooNewsExtracao
from system.core.services.gmail_service import EmailModuloC
from system.core.services.pdf_service import ModuloD
from system.core.utils.csv import salvar_csv


def executar_modulo_a() -> bool:
    '''
    Modulo A: scraping do Yahoo News, normaliza e publica na fila.
    '''
    log = setup_logger('modulo_a')
    config = carregar_config()
    processador = YahooNewsExtracao(config)

    sucesso = processador.executar()

    # salva os dados em CSV
    if sucesso and processador.lista_noticias:
        fieldnames = ['titulo', 'resumo', 'tema', 'fonte', 'tempo_leitura']
        arquivo_csv = salvar_csv(
            processador.lista_noticias,
            'noticias_yahoo',
            config.get('pasta_dados'),
            fieldnames
        )
        log.info(f"dados salvos em {arquivo_csv}")

    _imprimir_resumo(sucesso, processador.metricas)
    return sucesso


def executar_modulo_c() -> bool:
    '''
    Modulo C: le emails do Gmail, valida PDFs e salva.
    '''
    config = carregar_config()
    processador = EmailModuloC(config)

    sucesso = processador.executar()

    _imprimir_resumo(sucesso, processador.metricas)
    return sucesso

def executar_modulo_d():
    '''
    Modulo D: Coleta CPF/CEP dos pdfs trata depois salva em xlsx.
    '''
    log = setup_logger('modulo_d')
    config = carregar_config()
    processador = ModuloD(config)

    pasta_pdfs = config.get('pasta_validos')
    sucesso = processador.executar(pasta_pdfs)

    if sucesso:
        arquivo_xlsx = processador.salvar_xlsx(config.get('pasta_saida_xlsx'))
        log.info(f"dados salvos em {arquivo_xlsx}")

    _imprimir_resumo(sucesso, processador.metricas)
    return sucesso


def _imprimir_resumo(sucesso: bool, metricas: dict) -> None:
    '''Printa o resumo em JSON pro UiPath ler.'''
    if sucesso:
        status = 'success'
    else:
        status = 'failed'

    resumo = {
        'timestamp': datetime.now().isoformat(),
        'status': status,
        'metricas': metricas
    }

    print(json.dumps(resumo, ensure_ascii=False, indent=2))
