import requests
from system.core.config.logger import setup_logger

log = setup_logger('orchestrator_client')


class OrchestratorClient:
    '''
    Faz a ponte com o UiPath Orchestrator Cloud.
    Autentica via OAuth2 e publica/consome itens das filas.
    '''

    def __init__(self, config: dict):
        self.config = config
        self.log = log
        self.token = None

        self.url_base = config.get('orchestrator_url')
        self.conta = config.get('orchestrator_account')
        self.tenant = config.get('orchestrator_tenant')
        self.client_id = config.get('orchestrator_client_id')
        self.client_secret = config.get('orchestrator_client_secret')

        if not all([self.url_base, self.conta, self.tenant, self.client_id, self.client_secret]):
            self.log.error("credenciais do Orchestrator incompletas")
            return

        # auth fica na raiz, api precisa de conta/tenant no path
        self.url_api = f"{self.url_base}/{self.conta}/{self.tenant}/orchestrator_"

        self._autenticar()

    def _autenticar(self) -> bool:
        '''Pega o token OAuth2 do Orchestrator.'''
        try:
            url = f"{self.url_base}/identity_/connect/token"

            payload = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'scope': 'OR.Queues OR.Queues.Read OR.Queues.Write'
            }

            resp = requests.post(url, data=payload, timeout=30)

            if resp.status_code != 200:
                if resp.text:
                    erro = resp.text[:200]
                else:
                    erro = "sem corpo"
                self.log.error(f"erro na autenticacao: {resp.status_code} - {erro}")
                return False

            self.token = resp.json().get('access_token')
            self.log.info("autenticado no Orchestrator")
            return True

        except Exception as e:
            self.log.error(f"erro ao autenticar: {str(e)}")
            return False

    def _cabecalhos(self) -> dict:
        '''Monta os headers com o token.'''
        return {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }

    def publicar_item(self, nome_fila: str, dados: dict, referencia: str = None) -> bool:
        '''
        Joga um item na fila do Orchestrator.

        Args:
            nome_fila: nome da fila (ex: Bridge_Modulo_A)
            dados: dicionario com os campos do item
            referencia: id pra identificar o item (opcional)

        Returns:
            True se publicou
        '''
        if not self.token:
            self.log.error("nao autenticado")
            return False

        try:
            url = f"{self.url_api}/odata/Queues/UiPathODataSvc.AddQueueItem"

            # UiPath so aceita string no SpecificContent
            conteudo = {}
            for chave, valor in dados.items():
                if valor is not None:
                    conteudo[chave] = str(valor)
                else:
                    conteudo[chave] = ""

            payload = {
                "itemData": {
                    "Name": nome_fila,
                    "Priority": "Normal",
                    "SpecificContent": conteudo,
                    "Reference": referencia or ""
                }
            }

            resp = requests.post(url, json=payload, headers=self._cabecalhos(), timeout=30)

            if resp.status_code not in [200, 201]:
                if resp.text:
                    erro = resp.text[:200]
                else:
                    erro = "sem corpo"
                self.log.error(f"erro ao publicar: {resp.status_code} - {erro}")
                return False

            self.log.info(f"publicado em {nome_fila}")
            return True

        except Exception as e:
            self.log.error(f"erro ao publicar: {str(e)}")
            return False

    def consumir_item(self, nome_fila: str) -> dict:
        '''
        Puxa o proximo item da fila e trava a transacao.

        Args:
            nome_fila: nome da fila

        Returns:
            dict com o item ou None se fila vazia
        '''
        if not self.token:
            self.log.error("nao autenticado")
            return None

        try:
            url = f"{self.url_api}/odata/Queues/UiPathODataSvc.StartTransaction"

            payload = {
                "transactionData": {
                    "Name": nome_fila
                }
            }

            resp = requests.post(url, json=payload, headers=self._cabecalhos(), timeout=30)

            # 204 ou corpo vazio = nao tem item na fila
            if resp.status_code == 204 or not resp.text.strip():
                self.log.debug(f"fila vazia: {nome_fila}")
                return None

            if resp.status_code not in [200, 201]:
                self.log.warning(f"erro ao consumir: {resp.status_code}")
                return None

            self.log.info(f"consumido de {nome_fila}")
            return resp.json()

        except Exception as e:
            self.log.error(f"erro ao consumir: {str(e)}")
            return None

    def marcar_sucesso(self, id_transacao: int, saida: dict = None) -> bool:
        '''
        Marca a transacao como sucesso.

        Args:
            id_transacao: ID da transacao
            saida: dados de saida (opcional)

        Returns:
            True se marcou
        '''
        if not self.token:
            return False

        try:
            url = f"{self.url_api}/odata/Queues({id_transacao})/UiPathODataSvc.SetTransactionResult"

            conteudo_saida = {}
            if saida:
                for chave, valor in saida.items():
                    if valor is not None:
                        conteudo_saida[chave] = str(valor)
                    else:
                        conteudo_saida[chave] = ""

            payload = {
                "transactionResult": {
                    "IsSuccessful": True,
                    "Output": conteudo_saida
                }
            }

            resp = requests.post(url, json=payload, headers=self._cabecalhos(), timeout=30)

            if resp.status_code not in [200, 201, 204]:
                self.log.error(f"erro ao marcar sucesso: {resp.status_code}")
                return False

            self.log.info("marcado como sucesso")
            return True

        except Exception as e:
            self.log.error(f"erro ao marcar sucesso: {str(e)}")
            return False

    def marcar_erro(self, id_transacao: int, motivo: str = None) -> bool:
        '''
        Marca a transacao como erro.

        Args:
            id_transacao: ID da transacao
            motivo: descricao do erro

        Returns:
            True se marcou
        '''
        if not self.token:
            return False

        try:
            url = f"{self.url_api}/odata/Queues({id_transacao})/UiPathODataSvc.SetTransactionResult"

            payload = {
                "transactionResult": {
                    "IsSuccessful": False,
                    "ProcessingException": {
                        "Reason": motivo or "erro no processamento",
                        "Type": "ApplicationException"
                    }
                }
            }

            resp = requests.post(url, json=payload, headers=self._cabecalhos(), timeout=30)

            if resp.status_code not in [200, 201, 204]:
                self.log.error(f"erro ao marcar falha: {resp.status_code}")
                return False

            self.log.info("marcado como erro")
            return True

        except Exception as e:
            self.log.error(f"erro ao marcar falha: {str(e)}")
            return False
