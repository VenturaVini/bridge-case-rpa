import re
from system.core.config.logger import setup_logger

log = setup_logger('yahoo_services')


def limpar_texto(texto: str):
    '''
    Remove caracteres invalidos e arruma espacos (se houver)

    Args:
        texto: string 

    Returns:
        texto limpo
    '''
    if not texto:
        return ""

    # retira espacos a mais
    texto = re.sub(r'\s+', ' ', texto)

    # remove caracteres incomuns
    texto = re.sub(r'[^\w\s\.,\-\–]', '', texto)

    texto = texto.strip()
    return texto


def normalizar_dados(dados: dict):
    '''
    Limpa os campos de texto de um dicionario de noticia.

    Args:
        dados: dict com titulo, resumo, tema, fonte

    Returns:
        dict com dados limpos
    '''
    normalizado = dados.copy()

    if 'titulo' in normalizado:
        titulo = limpar_texto(normalizado['titulo'])
        normalizado['titulo'] = titulo

    if 'resumo' in normalizado:
        resumo = limpar_texto(normalizado['resumo'])
        normalizado['resumo'] = resumo

    if 'tema' in normalizado:
        normalizado['tema'] = limpar_texto(normalizado['tema'])

    if 'fonte' in normalizado:
        normalizado['fonte'] = limpar_texto(normalizado['fonte'])

    return normalizado
