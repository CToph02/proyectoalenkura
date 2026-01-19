import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# DEFINICIÓN DE PERMISOS (SCOPES)
# Si cambias estos permisos, debes eliminar el archivo token.json existente.
# Este scope es solo para LEER. Si necesitas enviar, usa: 'https://www.googleapis.com/auth/gmail.send'
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def main():
    creds = None
    
    # 1. Verificar si ya existe el archivo token.json
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
    # 2. Si no hay credenciales válidas, iniciar el flujo de "Login"
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Si el token expiró pero tenemos refresh token, lo renovamos
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Error al refrescar el token: {e}")
                # Forzar nueva autenticación si falla el refresh
                creds = None 
        
        if not creds:
            # Flujo completo: abre el navegador para que el usuario autorice
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            
        # 3. Guardar las credenciales para la próxima ejecución
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
            print("Nuevo token generado y guardado en 'token.json'.")

    return creds

if __name__ == '__main__':
    creds = main()
    if creds:
        print("¡Autenticación exitosa! Ya puedes usar la API.")