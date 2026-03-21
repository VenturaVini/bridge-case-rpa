import imaplib
import email
from email.header import decode_header
import smtplib
from email.mime.text import MIMEText
import os
from datetime import datetime
from system.core.config.logger import setup_logger
from system.core.utils.pdf_validator import validar_pdf

log = setup_logger('gmail_service')


class EmailModuloC:
    '''
    Classe com funcoes de processar email (corpo, uid, anexos),
    Le emails do Gmail via IMAP
    salva os PDFs validos ou não, responde o remetente
    Usa UID pra nao processar o mesmo email duas vezes.
    '''

    def __init__(self, config: dict):
        self.config = config
        self.log = log
        self.imap = None

        # arquivo que guarda os uid dos emails ja processados
        self.arquivo_uids = os.path.join(config.get('pasta_dados'), 'emails_processados.txt') # nome do arquivo onde ele vai salvar os uids do email (BD em txt)

        # carrega uids ja processados
        self.uids_processados = self._carregar_uids()

        # metricas
        self.metricas = {
            "recebidos": 0,
            "processados": 0,
            "rejeitados": 0,
            "duplicados": 0,
            "tempo_medio_seg": 0.0,
            "taxa_sucesso": 0.0
        }

    def executar(self):
        '''
        Roda o fluxo: conecta no gmail, busca emails, salva PDFs.

        Returns:
            Bool 
        '''
        try:
            if not self._conectar():
                return False

            ids_emails = self._buscar_emails()

            if not ids_emails:
                self.log.info("Nenhum email encontrado")
                self._desconectar()
                return True

            

            for id_email in ids_emails:
                self._processar_email(id_email)

            #metricas
            self.metricas['recebidos'] = len(ids_emails)

            if self.metricas['recebidos'] > 0: # calculo de porcetagem do q ele fez com o total do que ele fez
                self.metricas['taxa_sucesso'] = (self.metricas['processados'] / self.metricas['recebidos']) * 100

            self.log.info(f"processou {self.metricas['processados']} emails")
            return True

        except Exception as e:
            self.log.error(f"erro na execucao: {str(e)}")
            return False

        finally:
            self._desconectar()

    def _conectar(self):
        '''
        Conecta no Gmail via IMAP.

        Returns:
            True 
        '''
        try:
            servidor = self.config.get('gmail_servidor')
            porta = self.config.get('gmail_porta')
            usuario = self.config.get('gmail_usuario')
            senha = self.config.get('gmail_senha_app')

            if not usuario or not senha:
                self.log.info("credenciais do Gmail nao configuradas")
                return False

            self.imap = imaplib.IMAP4_SSL(servidor, porta)
            self.imap.login(usuario, senha)

            self.log.info("conectado ao Gmail")
            return True

        except Exception as e:
            self.log.error(f"erro ao conectar: {str(e)}")
            return False

    def _buscar_emails(self):
        '''
        Busca emails com o assunto configurado.

        Returns:
            lista de IDs dos emails
        '''
        try:
            self.imap.select('INBOX') # tipo de caixa de email

            # busca todos — so pra ver como o assunto chega pelo imap
            status, mensagens = self.imap.search(None, 'ALL')

            if status != 'OK':
                return []

            ids = mensagens[0].split()
            self.log.info(f"encontrou {len(ids)} emails")
            return ids

        except Exception as e:
            self.log.error(f"erro ao buscar emails: {str(e)}")
            return []

    def _processar_email(self, id_email):
        '''
        Processa um email: valida PDF, salva ou rejeita. ( na pasta valid ou rejected)

        Args:
            id_email: ID do email no IMAP
        '''
        try:
            # busca o email completo
            status, dados_msg = self.imap.fetch(id_email, '(RFC822)') # pega o email inteiro
            msg = email.message_from_bytes(dados_msg[0][1])  # json do email

            remetente = msg['From']
            data_email = msg['Date']
            assunto = self._decodificar_assunto(msg['Subject']) # trata base 64
            # assunto = msg['Subject'] # normal


            filtro = self.config.get('filtro_assunto')
            if filtro.lower() not in assunto.lower():
                self.log.info(f"assunto '{assunto}' nao bate com filtro '{filtro}', pulando")
                return

            # pega o uid pra checar duplicata
            status_uid, dados_uid = self.imap.fetch(id_email, '(UID)')
            uid = None
            if dados_uid:
                uid = dados_uid[0].decode().split('UID')[1].strip().replace(')', '') # coleta o uid do email

            # informacoes do email
            self.log.info(f"email encontrado - UID: {uid} | de: {remetente} | assunto: {assunto} | data: {data_email}")

            if not uid:
                self.log.warning("nao conseguiu pegar UID do email, pulando")
                return

            # se ja processou esse email antes, pula
            if uid in self.uids_processados:
                self.metricas['duplicados'] += 1
                self.log.info(f"email ja processado (UID: {uid}), pulando")
                return

            # percorre as partes do email procurando PDFs
            achou_pdf = False

            for parte in msg.walk(): # pecorre as aprte do email
                nome_arquivo = parte.get_filename()

                # verifica se tem pdf anexado, se nao já rejeita esse uid
                if not nome_arquivo:
                    continue
                if not nome_arquivo.endswith('.pdf'): 
                    continue

                achou_pdf = True

                # salva temporariamente pra validar
                pasta_temp = os.path.join(self.config.get('pasta_dados'), 'temp')
                os.makedirs(pasta_temp, exist_ok=True)
                caminho_temp = os.path.join(pasta_temp, nome_arquivo)

                with open(caminho_temp, 'wb') as f:
                    f.write(parte.get_payload(decode=True))

                # valida o PDF
                resultado = validar_pdf(caminho_temp)

                if not resultado['valido']:
                    self._rejeitar(remetente, nome_arquivo, resultado['motivo'])
                    os.remove(caminho_temp)
                    self.metricas['rejeitados'] += 1
                    continue

                # pdf valido — move pra pasta do dia
                data_pasta = datetime.now().strftime('%Y-%m-%d')
                pasta_destino = os.path.join(self.config.get('pasta_validos'), data_pasta)
                os.makedirs(pasta_destino, exist_ok=True)

                caminho_final = os.path.join(pasta_destino, nome_arquivo)
                os.rename(caminho_temp, caminho_final)

                self.log.info(f"PDF salvo: {caminho_final}")
                

            # marca o UID como processado pra nao pegar de novo
            if uid:
                self._registrar_uid(uid)
                self.log.info(f"UID {uid} adicionado aos processados")
                self.metricas['processados'] += 1

            # se achou pdf valido, responde confirmando
            if achou_pdf:
                self._responder_email(remetente, assunto)

            if not achou_pdf:
                self._rejeitar(remetente, 'sem_anexo', 'nenhum PDF encontrado')
                self.log.info(f"email sem PDF anexado - de: {remetente}")
                self.metricas['rejeitados'] += 1

        except Exception as e:
            self.log.error(f"erro ao processar email: {str(e)}")
            self.metricas['rejeitados'] += 1




    def _responder_email(self, destinatario: str, assunto_do_email: str):
        '''Responde ao remetente, informando que recebeu o relatorio'''
        try:
            usuario = self.config.get('gmail_usuario')
            senha = self.config.get('gmail_senha_app')

            #Mensagem para envio para o remetentente
            msg_remen = "Recebemos o seu relatório diario. Anexo OK!"

            msg = MIMEText(msg_remen)
            msg['Subject'] = f"Re: {assunto_do_email}"
            msg['From'] = usuario
            msg['To'] = destinatario

            # enviando email de resposta
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(usuario, senha)
                smtp.send_message(msg)

            self.log.info(f"resposta enviada para {destinatario}")

        except Exception as e:
            self.log.warning(f"erro ao responder email: {str(e)}")

    def _rejeitar(self, remetente: str, nome_arquivo: str, motivo: str):
        '''Salva info sobre email rejeitado.'''
        try:
            pasta = self.config.get('pasta_rejeitados')
            os.makedirs(pasta, exist_ok=True)

            arquivo = os.path.join(
                pasta,
                f'{datetime.now().strftime("%Y%m%d_%H%M%S")}_{nome_arquivo.replace(".pdf", ".txt")}'
            )

            with open(arquivo, 'w') as f:
                f.write(f"Remetente: {remetente}\n")
                f.write(f"Arquivo: {nome_arquivo}\n")
                f.write(f"Data: {datetime.now().isoformat()}\n")
                f.write(f"Motivo: {motivo}\n")

        except Exception as e:
            self.log.error(f"erro ao registrar rejeicao: {str(e)}")


    def _decodificar_assunto(self, assunto: str):
        '''gmail manda o assunto em base64 quando tem acento, aqui ele codifica'''
        return str(email.header.make_header(decode_header(assunto)))

    # PARTE ONDE SALVA OS UIDs DOS EMAILS PROCESSADOS PRA NAO PROCESSAR DUPLICADO

    def _carregar_uids(self):
        '''Verficar se o txt do uids existe, se exitir puxa os uids em um set'''
        uids = set()

        if not os.path.exists(self.arquivo_uids):
            return uids

        try:
            with open(self.arquivo_uids, 'r') as f:
                for linha in f:
                    uid = linha.strip()
                    if uid:
                        uids.add(uid)
        except Exception as e:
            self.log.error(f"erro ao carregar UIDs: {str(e)}")

        return uids

    def _registrar_uid(self, uid: str) -> None:
        '''Salva o uid do email no arquvivo, pra quando n tiver no arquivo txt'''
        try:
            with open(self.arquivo_uids, 'a') as f: # adiciona no final do txt
                f.write(uid + '\n')
            self.uids_processados.add(uid)
        except Exception as e:
            self.log.error(f"erro ao salvar UID: {str(e)}")

    def _desconectar(self) -> None:
        '''Desconecta a conexao IMAP.'''
        if self.imap:

            self.imap.close()
            self.imap.logout()

