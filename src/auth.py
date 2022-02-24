import json
from flask import request, _request_ctx_stack
from constants.http_status_codes import HTTP_401_UNAUTHORIZED
from functools import wraps
from jose import jwt
from urllib.request import urlopen
import os

AUTH0_DOMAIN = str(os.environ.get("AUTH0_DOMAIN"))
ALGORITHMS = 'RS256'
API_AUDIENCE = os.environ.get("API_AUDIENCE")

class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code

# Format error response and append status code
def get_token_auth_header():
    """Obtains the Access Token from the Authorization Header
    """
    auth = request.headers.get("Authorization", None)
    
    if not auth:
        raise AuthError({"code": "authorization_header_missing",
                        "description":"Authorization header is expected"}, HTTP_401_UNAUTHORIZED)

    parts = auth.split()

    if parts[0].lower() != "bearer":
        raise AuthError({"code": "invalid_header",
                        "description":"Authorization header must start with Bearer"}, HTTP_401_UNAUTHORIZED)
    elif len(parts) == 1:
        raise AuthError({"code": "invalid_header",
                        "description": "Token not found"}, 401)
    elif len(parts) > 2:
        raise AuthError({"code": "invalid_header",
                        "description": "Authorization header must be Bearer token"}, HTTP_401_UNAUTHORIZED)
    
    token = parts[1]
    return token

def requires_auth(f):
    """Determines if the Access Token is valid
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_auth_header()
        jsonurl = urlopen("https://"+AUTH0_DOMAIN+"/.well-known/jwks.json")
        jwks = json.loads(jsonurl.read())
        unverified_header = jwt.get_unverified_header(token)
        rsa_key = {}
        try:
            for key in jwks["keys"]:
                if key["kid"] == unverified_header["kid"]:
                    rsa_key = {
                        "kty": key["kty"],
                        "kid": key["kid"],
                        "use": key["use"],
                        "n": key["n"],
                        "e": key["e"]
                    }
            if rsa_key:
                try:
                    payload = jwt.decode(
                        token,
                        rsa_key,
                        algorithms=ALGORITHMS,
                        audience=API_AUDIENCE,
                        issuer="https://"+AUTH0_DOMAIN+"/"
                    )
                except jwt.ExpiredSignatureError:
                    raise AuthError({"code": "token_expired",
                                    "description": "token is expired"}, HTTP_401_UNAUTHORIZED)
                except jwt.JWTClaimsError:
                    raise AuthError({"code": "invalid_claims",
                                    "description":
                                        "incorrect claims,"
                                        "please check the audience and issuer"}, HTTP_401_UNAUTHORIZED)
                except Exception:
                    raise AuthError({"code": "invalid_header",
                                    "description":
                                        "Unable to parse authentication"
                                        " token."}, HTTP_401_UNAUTHORIZED)

                _request_ctx_stack.top.current_user = payload
                return f(*args, **kwargs)
            raise AuthError({"code": "Invalid_header",
                            "description": "Unable to find appropriate key"}, HTTP_401_UNAUTHORIZED)
        except Exception:
            raise AuthError({"code": "invalid_access",
                            "description":
                            "Invalid access to AUTH0 domain, you need to refresh Auth0 token."}, HTTP_401_UNAUTHORIZED)
    return decorated
