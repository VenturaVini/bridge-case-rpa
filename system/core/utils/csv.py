import csv
import os
from datetime import datetime
from system.core.config.logger import setup_logger

log = setup_logger('csv_utils')


def salvar_csv(dados: list, nome_arquivo: str, saida: str, fieldnames: list) -> str:
    '''
    Salva dados em CSV com idempotência (não duplica registros do mesmo dia).

    Args:
        dados: lista de dicts com os dados
        nome_arquivo: prefixo do arquivo (ex: news_raw)
        saida: pasta onde salva
        fieldnames: lista com nomes das colunas

    Returns:
        caminho completo do arquivo salvo
    '''
    os.makedirs(saida, exist_ok=True)
    data = datetime.now().strftime('%Y%m%d')
    arquivo_csv = os.path.join(saida, f'{nome_arquivo}_{data}.csv')
    ids_existentes = set()

    log.info(f"preparando {len(dados)} registros para CSV")

    # lê o arquivo existente pra pegar ids que já foram salvos
    if os.path.exists(arquivo_csv):
        with open(arquivo_csv, 'r', encoding='utf-8', newline='') as f:
            leitor = csv.DictReader(f)
            for linha in leitor:
                # assume que a primeira coluna é o id
                primeiro_campo = fieldnames[0]
                ids_existentes.add(linha.get(primeiro_campo))
        log.debug(f"encontrados {len(ids_existentes)} registros existentes")

    novos_registros = []
    ignorados = 0
    primeiro_campo = fieldnames[0]

    for item in dados:
        # se o id já existe, ignora (evita duplicação)
        if item.get(primeiro_campo) in ids_existentes:
            ignorados += 1
            continue
        ids_existentes.add(item.get(primeiro_campo))
        novos_registros.append(item)

    log.info(f"processou {len(novos_registros)} novos, {ignorados} duplicados")

    if not novos_registros:
        log.warning("nenhum registro novo pra salvar")
        return arquivo_csv

    # abre em append se o arquivo ja existe, senao cria novo
    if os.path.exists(arquivo_csv):
        escrever_modo = 'a'
    else:
        escrever_modo = 'w'

    with open(arquivo_csv, escrever_modo, encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if escrever_modo == 'w':
            writer.writeheader()
        writer.writerows(novos_registros)

    log.info(f"salvou {len(novos_registros)} registros em {arquivo_csv}")
    return arquivo_csv
