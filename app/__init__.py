# app/__init__.py

from flask import Flask, Blueprint
from flask_restx import Api
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

# --- CRIAÇÃO DO APP ---
app = Flask(__name__)
CORS(app)
app.wsgi_app = ProxyFix(app.wsgi_app)


# --- [INÍCIO DA CORREÇÃO] ---

# 1. Crie o blueprint primeiro, DEFININDO O PREFIXO DA URL NELE
blueprint = Blueprint('api', __name__, url_prefix='/api')

# 2. Anexe o 'Api' (flask-restx) AO BLUEPRINT, não ao 'app'
#    Remova o 'prefix' daqui, pois ele já está no url_prefix do blueprint.
api = Api(blueprint,
          title='Análise de documentos jurídicos',
          version='1.0',
          description='Api para análise de documentos para verificar se é confidencial e gerar logs, utilizando IA')

# 3. Importe o Controller DEPOIS de criar o 'api'
#    (O controller vai adicionar seus 'namespaces' ao objeto 'api')
from .controller import ProcessaDocumentoController

# 4. Registre o blueprint (que agora contém as rotas do Swagger) no app principal
app.register_blueprint(blueprint)

# --- [FIM DA CORREÇÃO] ---