import os
from datetime import datetime
import pandas as pd
from system.core.config.logger import setup_logger
from system.core.utils.pdf_validator import ler_pdf
from system.core.utils.validacao_cep_cpf import extrair_cpf, extrair_cep, validar_cpf_formato, validar_cep_formato, normalizar_cpf, normalizar_cep

log = setup_logger('pdf_service')


class ModuloD:
    '''
    Le os PDFs do modulo C, extrai CPF e CEP com regex,
    trata os dados (valida formato e deixa padrão)
    e depois salvar em .xlsx
    '''

    def __init__(self, config):
        self.log = log
        self.config = config
        self.dados_extraidos = []

        self.metricas = {
            "recebidos": 0,
            "processados": 0,
            "rejeitados": 0,
            "tempo_medio_seg": 0.0,
            "taxa_sucesso": 0.0
        }

    def executar(self, pasta_pdfs: str):
        '''
        Percorre a pasta, processa cada PDF e extrai CPF/CEP.

        '''
        try:
            if not os.path.exists(pasta_pdfs):
                self.log.error(f"pasta nao existe: {pasta_pdfs}")
                return False

            # pega todos os pdfs da pasta e subpastas dentro do inbox > valid > todos os dias
            arquivos_pdf = []
            for raiz, pastas, arquivos in os.walk(pasta_pdfs):
                for arquivo in arquivos:
                    if arquivo.endswith('.pdf'):
                        arquivos_pdf.append(os.path.join(raiz, arquivo))

            if not arquivos_pdf:
                self.log.warning("nenhum PDF encontrado")
                return True

            

            for caminho in arquivos_pdf:
                self._processar_pdf(caminho)

            #mtetricas
            self.metricas['recebidos'] = len(arquivos_pdf)

            if self.metricas['recebidos'] > 0: # porcetagem de processados
                self.metricas['taxa_sucesso'] = (self.metricas['processados'] / self.metricas['recebidos']) * 100

            self.log.info(f"extraiu dados de {self.metricas['processados']} PDFs")
            return True



        except Exception as e:
            self.log.error(f"erro na execucao: {str(e)}")
            return False
        



    def _processar_pdf(self, caminho_pdf: str):
        '''
        Le um PDF, extrai CPF e CEP, valida e guarda o resultado

        '''
        nome = os.path.basename(caminho_pdf)

        try:
            texto = ler_pdf(caminho_pdf)

            # if not texto or not texto.strip():
            if not texto:
                self._adicionar_resultado(nome, erro="PDF vazio")
                self.metricas['rejeitados'] += 1
                return

            # pega o primeiro CPF e CEP que achar no texto
            cpfs = extrair_cpf(texto)
            ceps = extrair_cep(texto)

            cpf = ""
            cep = ""
            cpf_valido = False
            cep_valido = False

            if cpfs:
                cpf = cpfs[0]
                cpf_valido = validar_cpf_formato(cpf)
                cpf = normalizar_cpf(cpf)

            if ceps:
                cep = ceps[0]
                cep_valido = validar_cep_formato(cep)
                cep = normalizar_cep(cep)

            # se nao tiver CPF ou CEP, ou nenhum dos dois
            erro = ""
            if not cpf and not cep:
                erro = "CPF e CEP nao encontrados"
            elif not cpf:
                erro = "CPF nao encontrado"
            elif not cep:
                erro = "CEP nao encontrado"

            self._adicionar_resultado(nome, cpf, cpf_valido, cep, cep_valido, erro)
            self.metricas['processados'] += 1

            self.log.debug(f"extraiu cpf={cpf} cep={cep} de {nome}")

        except Exception as e:
            self.log.error(f"erro ao processar {nome}: {str(e)}")
            self._adicionar_resultado(nome, erro=str(e))
            self.metricas['rejeitados'] += 1

    def _adicionar_resultado(self, 
                             arquivo: str, 
                             cpf: str = "", 
                             cpf_valido: bool = False,
                             cep: str = "", 
                             cep_valido: bool = False, 
                             erro: str = ""
                             ):
        

        '''Joga o resultado na lista de dados extraidos'''


        self.dados_extraidos.append({
            "arquivo": arquivo,
            "cpf": cpf,
            "cpf_valido": cpf_valido,
            "cep": cep,
            "cep_valido": cep_valido,
            "erro": erro
        })

    def salvar_xlsx(self, caminho_saida: str):
        '''
        Salva os dados extraidos em XLSX usando pandas.

        '''
        if not caminho_saida: # verfica se o caminho de saida existe e cria
            caminho_saida = os.path.join(os.getcwd(), 'system', 'data')
        os.makedirs(caminho_saida, exist_ok=True)


        data = datetime.now().strftime('%Y%m%d')  #
        arquivo_xlsx = os.path.join(caminho_saida, f'dados_extraidos_{data}.xlsx')

        df = pd.DataFrame(self.dados_extraidos) # transforma a lista de dcionario em df 
        df.to_excel(arquivo_xlsx, index=False, sheet_name='Dados Extraidos')

        self.log.info(f"salvou {len(self.dados_extraidos)} registros em {arquivo_xlsx}")
        return arquivo_xlsx
