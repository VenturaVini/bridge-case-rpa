import PyPDF2
import os
from system.core.config.logger import setup_logger

log = setup_logger('gmail_service')


def ler_pdf(caminho_pdf: str):
    '''
    Le um PDF e extrai todo o texto.

    Args:
        caminho_pdf: caminho completo do arquivo PDF

    Returns:
        texto extraido do pdf ou string vazia se corrompido
    '''
    try:
        with open(caminho_pdf, 'rb') as f:
            reader = PyPDF2.PdfReader(f)

            if not reader.pages:
                log.warning(f"PDF sem paginas: {caminho_pdf}")
                return ""

            # extrai texto de todas as paginas
            texto_completo = ""
            for i in range(len(reader.pages)):
                try:
                    texto = reader.pages[i].extract_text()
                    texto_completo = texto_completo + texto + "\n"
                except Exception as e:
                    log.warning(f"erro ao ler pagina {i+1}: {str(e)}")
                    continue

            return texto_completo

    except PyPDF2.PdfReadError as e:
        log.error(f"PDF corrompido: {caminho_pdf} - {str(e)}")
        return "" # erro

    except Exception as e:
        log.error(f"erro ao ler PDF {caminho_pdf}: {str(e)}")
        return "" #erro


def validar_pdf(caminho_pdf: str):
    '''
    Valida um PDF: verifica se existe e se e legivel.

    Args:
        caminho_pdf: caminho do arquivo

    Returns:
        dict com valido (bool) e motivo (str)
    '''
    resultado = {
        'valido': False,
        'motivo': ''
    }

    # # verifica se o arquivo existe
    # if not os.path.exists(caminho_pdf):
    #     resultado['motivo'] = 'arquivo nao encontrado'
    #     return resultado

    # tenta ler o PDF
    texto = ler_pdf(caminho_pdf)

    if not texto or texto == "": #erro
        resultado['motivo'] = 'PDF corrompido'
        return resultado

    resultado['valido'] = True
    log.info(f"PDF validado: {caminho_pdf}")

    return resultado



