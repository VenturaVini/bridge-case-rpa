from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from system.core.config.logger import setup_logger
import time

log = setup_logger('webdriver')


class ProcessadorWebDriver:
    # Iniciado do ChromeDriver

    def __init__(self, headless = True, timeout = 10):
        self.driver = None
        self.headless = headless # da pra escolher o headless
        self.timeout = timeout
        self.log = log

    def iniciar(self) -> bool:
        '''
        Abre o navegador Chrome.

        Returns:
            True se abriu, False se deu ruim
        '''
        try:
            opcoes = Options()

            if self.headless:
                opcoes.add_argument("--headless")

            opcoes.add_argument("--no-sandbox")
            opcoes.add_argument("--disable-dev-shm-usage")
            opcoes.add_argument("--disable-gpu")

            self.driver = webdriver.Chrome(options=opcoes)
            self.driver.set_page_load_timeout(self.timeout)

            self.log.info("navegador iniciado")
            return True

        except Exception as e:
            self.log.error(f"erro ao iniciar navegador: {str(e)}")
            return False

    def acessar_pagina(self, url: str) -> bool:
        '''
        Acessa URL

        Args:
            url: endereco pra acessar

        Returns:
            True se acessou
        '''
        if not self.driver:
            return False

        try:
            self.log.info(f"Acessando: {url}")
            self.driver.get(url)
            time.sleep(2)
            return True

        except Exception as e:
            self.log.error(f"Erro ao acessar: {url}: {str(e)}")
            return False

    def encontrar_elementos(self, seletor: str, tipo: str = "xpath"):
        '''
        Busca elementos na pagina pelo seletor.

        Args:
            seletor: escolhe o seletor id, xpath e css

        Returns:
            lista de elementos encontrados
        '''
        if not self.driver:
            return []

        try:
            if tipo == "css":
                metodo = By.CSS_SELECTOR
            elif tipo == "id":
                metodo = By.ID

            else:
                metodo = By.XPATH

            elementos = self.driver.find_elements(metodo, seletor) 
            return elementos

        except Exception as e:
            self.log.warning(f"nao achou elementos ({seletor}): {str(e)}")
            return []

    def fechar(self) -> None:
        '''Fecha o navegador.'''
        if self.driver:
            try:
                self.driver.quit()
                self.log.info("navegador fechado")
            except Exception as e:
                self.log.error(f"erro ao fechar: {str(e)}")
