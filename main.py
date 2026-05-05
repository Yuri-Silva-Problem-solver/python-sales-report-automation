# ========================
# IMPORTAÇÕES
# ========================
import pandas as pd
import base64
import os
from email.mime.text import MIMEText

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

from dotenv import load_dotenv

load_dotenv()

# ========================
# CONFIGURAÇÃO API
# ========================
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# ========================
# IMPORTAR BASE DE DADOS
# ========================
tabela_vendas = pd.read_excel('Vendas Shell.xlsx')

print(tabela_vendas)

# ========================
# FATURAMENTO POR LOJA
# ========================
faturamento = (
    tabela_vendas[['ID Loja', 'Valor Final']]
    .groupby('ID Loja')
    .sum()
    .sort_values(by='Valor Final', ascending=False)
)
print(faturamento)

# ========================
# QUANTIDADE POR LOJA
# ========================
quantidade_produtos = (
    tabela_vendas[['ID Loja', 'Quantidade']]
    .groupby('ID Loja')
    .sum()
    .sort_values(by='Quantidade', ascending=False)
)
print(quantidade_produtos)

print('-' * 50)

# ========================
# TICKET MÉDIO
# ========================
ticket_medio = (
    (faturamento['Valor Final'] / quantidade_produtos['Quantidade'])
    .to_frame(name='Ticket Médio')
    .sort_values(by='Ticket Médio', ascending=False)
)
ticket_medio = ticket_medio.rename(columns={0: 'Ticket Médio'})
print(ticket_medio)

# ========================
# FUNÇÃO DE ENVIO DE EMAIL
# ========================
def enviar_email():
    creds = None

    # Se já existe token
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # Se não existe ou expirou
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # Salva token
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    # Conectar com API
    service = build('gmail', 'v1', credentials=creds)

    # Corpo do email
    html_body = f"""
    <p>Prezados,</p>

    <p>Segue o Relatório de Vendas por cada Loja.</p>

    <p><b>Faturamento:</b></p>
    {faturamento.to_html(formatters={'Valor Final': 'R${:,.2f}'.format})}

    <p><b>Quantidade Vendida:</b></p>
    {quantidade_produtos.to_html()}

    <p><b>Ticket Médio:</b></p>
    {ticket_medio.to_html(formatters={'Ticket Médio': 'R${:,.2f}'.format})}

    <p>Qualquer dúvida estou à disposição.</p>

    <p>Att.,<br>Yuri Silva</p>
    """

    msg = MIMEText(html_body, 'html')
    msg['to'] = os.getenv('EMAIL_DESTINO')
    msg['subject'] = 'Relatório de Vendas por Loja'

    # Codificação
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

    # Enviar email
    service.users().messages().send(
        userId="me",
        body={'raw': raw}
    ).execute()

    print("Email enviado com sucesso!")

# ========================
# EXECUÇÃO
# ========================
enviar_email()