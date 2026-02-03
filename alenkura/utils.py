import base64
import os
from email.mime.text import MIMEText

# from django.conf import settings
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


def enviar_correo_gmail(destinatario, asunto, mensaje_texto):
    """
    Envía un correo usando la API de Gmail y el archivo token.json
    """
    SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

    # Ruta absoluta al token.json (asegúrate que esté en la raíz o ajusta la ruta)
    # BASE_DIR debe estar importado de settings o usar os.getcwd() si está en raíz
    token_path = "alenkura/token.json"

    if not os.path.exists(token_path):
        print("No se encontró el archivo token.json")
        return False

    try:
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        service = build("gmail", "v1", credentials=creds)

        # Crear el mensaje de correo
        message = MIMEText(mensaje_texto)
        message["to"] = destinatario
        message["subject"] = asunto

        # Codificación necesaria para Gmail API (Base64 URL Safe)
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        body = {"raw": raw_message}

        # Enviar
        message = service.users().messages().send(userId="me", body=body).execute()
        print(f"Correo enviado Id: {message['id']}")
        return True

    except Exception as error:
        print(f"Ocurrió un error al enviar correo: {error}")
        return False


# import base64
# import os
# import mimetypes
# from email.mime.multipart import MIMEMultipart
# from email.mime.text import MIMEText
# from email.mime.base import MIMEBase
# from email import encoders
# from google.oauth2.credentials import Credentials
# from googleapiclient.discovery import build

# def enviar_correo_gmail(destinatario, asunto, mensaje_texto, ruta_archivo=None):
#     SCOPES = ['https://www.googleapis.com/auth/gmail.send']
#     token_path = 'alenkura/token.json'

#     if not os.path.exists(token_path):
#         print("No se encontró el archivo token.json")
#         return False

#     try:
#         creds = Credentials.from_authorized_user_file(token_path, SCOPES)
#         service = build('gmail', 'v1', credentials=creds)

#         # 1. Crear el contenedor del mensaje (Multipart)
#         message = MIMEMultipart()
#         message['to'] = destinatario
#         message['subject'] = asunto

#         # 2. Añadir el cuerpo del mensaje
#         message.attach(MIMEText(mensaje_texto, 'plain'))

#         # 3. Procesar el archivo adjunto (si existe)
#         if ruta_archivo and os.path.exists(ruta_archivo):
#             nombre_archivo = os.path.basename(ruta_archivo)

#             # Detectar el tipo de archivo automáticamente (pdf, jpg, etc.)
#             content_type, encoding = mimetypes.guess_type(ruta_archivo)
#             if content_type is None or encoding is not None:
#                 content_type = 'application/octet-stream'

#             main_type, sub_type = content_type.split('/', 1)

#             with open(ruta_archivo, 'rb') as f:
#                 part = MIMEBase(main_type, sub_type)
#                 part.set_payload(f.read())

#             # Codificar en base64 para el transporte
#             encoders.encode_base64(part)

#             # Añadir cabeceras al adjunto
#             part.add_header(
#                 'Content-Disposition',
#                 f'attachment; filename="{nombre_archivo}"'
#             )
#             message.attach(part)

#         # 4. Codificación final para Gmail API
#         raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
#         body = {'raw': raw_message}

#         # Enviar
#         enviado = service.users().messages().send(userId="me", body=body).execute()
#         print(f"Correo enviado Id: {enviado['id']}")
#         return True

#     except Exception as error:
#         print(f'Ocurrió un error: {error}')
#         return False
