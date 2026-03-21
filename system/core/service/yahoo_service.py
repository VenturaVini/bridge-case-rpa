from system.core.config.logger import setup_logger
from system.core.services.webdriver import ProcessadorWebDriver
from system.core.services.locators import YahooNewsLocators
from system.core.services.orchestrator_client import OrchestratorClient
from system.core.utils.normalizacao_yahoo import normalizar_dados
import time

log = setup_logger('yahoo_service')


class YahooNewsExtracao:
    '''
    Scraping do Yahoo News.
    Puxa 5 noticias do bloco Stories for you
    '''

    def __init__(self, config: dict):
        self.log = log
        self.config = config
        self.lista_noticias = []
        self.navegador = None

        # metricas
        self.metricas = {
            "recebidos": 0,
            "processados": 0,
            "rejeitados": 0,
            "tempo_medio_seg": 0.0,
            "taxa_sucesso": 0.0
        }

    def executar(self):  # main-root
        '''
        main do fluxo completo: abre o yahoo, extrai, normaliza e publica
        Se falhar, tenta de novo ate 3 vezes

        Returns:
            Bool
        '''
        max_tentativas = self.config.get('max_tentativas')
        espera_base = self.config.get('espera_base')
        tentativa = 0

        while tentativa < max_tentativas:
            tentativa += 1

            try:
                # abre o navegador
                self.navegador = ProcessadorWebDriver(
                    headless=self.config.get('yahoo_headless'),
                    timeout=self.config.get('yahoo_timeout')
                )

                if not self.navegador.iniciar():
                    raise Exception("falhou ao iniciar navegador")

                # acessa o yahoo
                if not self.navegador.acessar_pagina(self.config.get('yahoo_url')):
                    raise Exception("falhou ao acessar Yahoo")

                # extrai as noticias
                self.lista_noticias = self._extrair_noticias()

                if not self.lista_noticias:
                    raise Exception("nenhuma noticia extraida")

                self.metricas['recebidos'] = len(self.lista_noticias)

                # normaliza os dados (limpa caracteres incomuns)
                for i in range(len(self.lista_noticias)):
                    self.lista_noticias[i] = normalizar_dados(self.lista_noticias[i])

                self.metricas['processados'] = len(self.lista_noticias)

                # publica na fila do orchestrator
                self._publicar_na_fila()



                # calcula metricas
                if self.metricas['recebidos'] > 0:
                    self.metricas['taxa_sucesso'] = (self.metricas['processados'] / self.metricas['recebidos']) * 100

                self.log.info(f"extraiu e publicou {len(self.lista_noticias)} noticias")
                return True

            except Exception as e:
                self.log.warning(f"tentativa {tentativa}/{max_tentativas} falhou: {str(e)}")

                if self.navegador:
                    self.navegador.fechar()

                # espera para tenta denovo exponenciamente
                if tentativa < max_tentativas:
                    espera = espera_base * tentativa
                    self.log.info(f"aguardando {espera}s")
                    time.sleep(espera)
                else:
                    self.log.error(f"falhou apos {max_tentativas} tentativas")

        return False

    def _extrair_noticias(self) -> list:
        '''
        Pega as 5 noticias do bloco Stories for you

        Returns:
            lista de dicts ccom os parametros da noticias coletadas
        '''
        noticias = []
        self.log.info("Extraindo noticias do yahoo")

        # busca todos os blocos de noticia na pagina (sem anuncios)
        blocos = self.navegador.encontrar_elementos(YahooNewsLocators.ITEM_NOTICIA, tipo="xpath")

        if not blocos:
            self.log.warning("nenhuma noticia encontrada na pagina")
            return noticias

        # filtra pelas elementos unicos cada parte
        for i, bloco in enumerate(blocos[:YahooNewsLocators.LIMITE]):
            try:
                noticia = {}

                # titulo
                elem_titulo = bloco.find_element("xpath", YahooNewsLocators.TITULO)

                noticia['titulo'] = elem_titulo.text

                # resumo
                noticia['resumo'] = self._pegar_texto(bloco, YahooNewsLocators.RESUMO)

                # tema, fonte e tempo de leitura
                noticia['tema'] = self._pegar_texto(bloco, YahooNewsLocators.TEMA)
                noticia['fonte'] = self._pegar_texto(bloco, YahooNewsLocators.FONTE)
                noticia['tempo_leitura'] = self._pegar_texto(bloco, YahooNewsLocators.TEMPO_LEITURA)

                # pode acontecer de ter algum parametro que falte (normalmente é tempo de leitura e fonte)
                if noticia['titulo'] and noticia['tema']: # tema mais importante para dps enviar o email
                    noticias.append(noticia)
                    self.log.debug(f"noticia {i+1}")
                else:
                    self.log.warning(f"noticia {i+1} sem titulo ou resumo, ignorada")

            except Exception as e:
                self.log.warning(f"erro na noticia {i+1}: {str(e)}")
                continue

        self.log.info(f"extraiu {len(noticias)} noticias")
        return noticias

    def _pegar_texto(self, elemento, xpath: str):
        '''Tenta pegar o texto de um sub-elemento. Retorna vazio se nao achar.'''
        try:
            elem = elemento.find_element("xpath", xpath)
            if elem:
                return elem.text
            return ""
        except Exception:
            return ""

    # OPICIONAL - Essa parte ele joga para o Uipath

    def _publicar_na_fila(self) -> None:
        '''Publica cada noticia na fila do Orchestrator.'''
        try:
            # inicia
            orchestrator = OrchestratorClient(self.config)

             # verifica se autenticou
            if not orchestrator.token:
                self.log.warning("nao autenticou no Orchestrator, pulando publicacao")
                return

            nome_fila = self.config.get('fila_modulo_a')

            for i, noticia in enumerate(self.lista_noticias, 1):

                referencia = f"noticia_{i}_{noticia.get('titulo', '').replace(' ', '_')[:30]}"

                sucesso = orchestrator.publicar_item(nome_fila=nome_fila,
                    dados=noticia,
                    referencia=referencia
                )

                if sucesso:
                    self.log.info(f"publicada noticia {i}")
                else:
                    self.log.warning(f"falhou ao publicar noticia {i}")

        except Exception as e:
            self.log.warning(f"erro ao publicar na fila: {str(e)}")
