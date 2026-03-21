import requests
from system.core.config.logger import setup_logger

log = setup_logger('orchestrator_client')


class OrchestratorClient:
    '''
    Conecta no Uipath Orquestrador cloud via API com python
    
    '''

    def __init__(self, config: dict):
        self.config = config
        self.log = log
        self.token = None

        # env
        self.url_base = config.get('orchestrator_url')
        self.conta = config.get('orchestrator_account')
        self.tenant = config.get('orchestrator_tenant')
        self.client_id = config.get('orchestrator_client_id')
        self.client_secret = config.get('orchestrator_client_secret')

        # monta a url base da api
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
                self.log.error(f"erro na autenticacao: {resp.status_code}")
                return False

            self.token = resp.json().get('access_token')
            self.log.info("autenticado no Orchestrator")
            return True

        except Exception as e:
            self.log.error(f"erro ao autenticar: {str(e)}")
            return False

    def _cabecalhos(self) -> dict:
        '''Headers com token e folder id.'''
        return {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json',
            'X-UIPATH-OrganizationUnitId': self.config.get('orchestrator_folder_id')
        }

    def publicar_item(self, nome_fila: str, dados: dict, referencia = None):
        '''
        Joga um item na fila do Orchestrator.

        Args:
            nome_fila: nome da fila (ex: Bridge_Modulo_A)
            dados: dicionario com os campos do item
            referencia: id pra identificar o item

        Returns:
            TBool
        '''
        if not self.token:
            self.log.error("nao autenticado")
            return False

        try:
            url = f"{self.url_api}/odata/Queues/UiPathODataSvc.AddQueueItem"

            # converte tudo pra string pq o UiPath so aceita string
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
                self.log.error(f"erro ao publicar: {resp.status_code} - {resp.text[:200]}")
                return False

            self.log.info(f"publicado em {nome_fila}")
            return True

        except Exception as e:
            self.log.error(f"erro ao publicar: {str(e)}")
            return False

    def consumir_item(self, nome_fila: str):
        '''
        Puxa o proximo item da fila.
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

            # 204 = fila vazia
            if resp.status_code == 204 or not resp.text.strip():
                self.log.info(f"fila vazia: {nome_fila}")
                return None

            if resp.status_code not in [200, 201]: # sucesso
                self.log.error(f"erro ao consumir: {resp.status_code}")
                return None

            self.log.info(f"consumido de {nome_fila}")
            return resp.json()

        except Exception as e: # outros erros
            self.log.error(f"erro ao consumir: {str(e)}")
            return None
