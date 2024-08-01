from pypodio2 import api 

def authenticate_podio(client_id, client_secret, username, password):
    client = api.OAuthClient(client_id, client_secret, username, password)
    return client