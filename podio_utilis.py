from pypodio2 import api 
from urllib.parse import urlencode
def authenticate_podio(client_id, client_secret, username, password):
    client = api.OAuthClient(client_id, client_secret, username, password)
    return client