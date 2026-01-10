import base64
import os
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from django.conf import settings

def enviar_correo_gmail(destinatario, asunto, mensaje_texto):
    """
    Envía un correo usando la API de Gmail y el archivo token.json
    """
    SCOPES = ['https://www.googleapis.com/auth/gmail.send']
    
    # Ruta absoluta al token.json (asegúrate que esté en la raíz o ajusta la ruta)
    # BASE_DIR debe estar importado de settings o usar os.getcwd() si está en raíz
    token_path = 'token.json' 

    if not os.path.exists(token_path):
        print("No se encontró el archivo token.json")
        return False

    try:
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        service = build('gmail', 'v1', credentials=creds)

        # Crear el mensaje de correo
        message = MIMEText(mensaje_texto)
        message['to'] = destinatario
        message['subject'] = asunto
        
        # Codificación necesaria para Gmail API (Base64 URL Safe)
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        body = {'raw': raw_message}

        # Enviar
        message = service.users().messages().send(userId="me", body=body).execute()
        print(f"Correo enviado Id: {message['id']}")
        return True

    except Exception as error:
        print(f'Ocurrió un error al enviar correo: {error}')
        return False