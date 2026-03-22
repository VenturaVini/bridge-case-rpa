import re
from system.core.config.logger import setup_logger

log = setup_logger('pdf_service')

# padroes regex pra encontrar CPF e CEP no texto
CPF_REGEX = r'\d{3}\.\d{3}\.\d{3}\-\d{2}|\d{11}'
CEP_PATTERN = r'\d{5}\-\d{3}|\d{8}'

# CPF_REGEX = ele checa se tem nesse padrao ex: 123.456.789-01 
# ou se tiver 12345675555

# CEP_REGEX: checa se tem nesse padrao ex: 12345-678 ou se tiver 12345678



# CPF

def extrair_cpf(texto: str):
    '''
    Coleta todos os CPF apartir do regex e retorna em uma lista
    '''
    cpfs = re.findall(CPF_REGEX, texto)
    return cpfs



def validar_cpf_formato(cpf: str) -> bool:
    '''
    Checa se o CPF tem 11 digitos e nao e tudo igual (111.111.111-11).

    Args:
        cpf: string com o CPF

    Returns:
        True se o formato e valido
    '''
    cpf_limpo = re.sub(r'\D', '', cpf)

    if len(cpf_limpo) != 11:
        return False

    # cpf com todos digitos iguais e invalido
    if cpf_limpo == cpf_limpo[0] * 11:
        return False

    return True


def normalizar_cpf(cpf: str):
    '''
    Apos valida verifica se da pra colcoar no formato apdrao
    '''
    cpf_limpo = re.sub(r'\D', '', cpf)

    if len(cpf_limpo) != 11:
        return ""

    formatado = cpf_limpo[:3] + '.' + cpf_limpo[3:6] + '.' + cpf_limpo[6:9] + '-' + cpf_limpo[9:]
    return formatado



# CEP

def extrair_cep(texto: str):
    '''
    Coleta todos os CEP apartir do regex e retorna em uma lista

    '''
    ceps = re.findall(CEP_PATTERN, texto)
    return ceps



def validar_cep_formato(cep: str):
    '''
    Limpa o traco e valida o cep tem 8 digitos

    Args:
        cep: string com o CEP

    Returns:
        True se o formato e valido
    '''
    cep_limpo = re.sub(r'\D', '', cep)
    if len(cep_limpo) == 8:
        return True
    return False



def normalizar_cep(cep: str) -> str:
    '''
    Apos valida verifica se da pra colcoar no formato apdrao

    Args:
        cep: CEP em qualquer formato

    Returns:
        CEP formatado
    '''
    cep_limpo = re.sub(r'\D', '', cep)

    if len(cep_limpo) != 8:
        return ""

    formatado = cep_limpo[:5] + '-' + cep_limpo[5:]
    return formatado
