# app/ProcessaDocumentoController.py

import os
import hashlib
from flask_restx import Resource, fields
from werkzeug.datastructures import FileStorage  # <-- MUDANÇA: Importar FileStorage

# --- Importa o 'api' do __init__.py ---
from app import api

# --- Importa a LÓGICA DO SEU AGENTE ---
try:
    from app.dlp_uba_with_nn import (
        setup_database,
        classify_with_neural_network,
        log_access_for_uba
    )
except ImportError:
    print("[ERRO FATAL] Não foi possível encontrar 'dlp_uba_with_nn.py'.")
    exit()
except Exception as e:
    print(f"[ERRO FATAL] Erro ao carregar o modelo de IA ou o script do agente: {e}")
    exit()

# --- (REMOVER A CONFIGURAÇÃO DO FLASK DAQUI) ---

# --- Inicialização do Agente ---
# (Como recomendado anteriormente, isso deveria estar no run.py)
# Mas, mantendo como está no seu arquivo:
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, 'data')
db_path = os.path.join(DATA_DIR, 'legal_dlp_uba.db')
if os.path.exists(db_path):
    os.remove(db_path)
setup_database()
print("Banco de dados 'legal_dlp_uba.db' inicializado.")
print("Servidor de API pronto para receber requisições.")

# --- [INÍCIO DAS MUDANÇAS] ---

# 1. Removido o 'input_model = api.model(...)'
#    Em vez disso, criamos um PARSER para upload de arquivos

file_upload_parser = api.parser()
file_upload_parser.add_argument(
    'username',
    type=str,
    required=True,
    location='form',  # <-- MUDANÇA: O dado vem de um formulário
    choices=['estagiario', 'advogado_senior'],  # <-- MUDANÇA: Validação
    help='O cargo do usuário (estagiario ou advogado_senior)'
)
file_upload_parser.add_argument(
    'file',
    type=FileStorage,  # <-- MUDANÇA: Tipo de dado é um arquivo
    required=True,
    location='files',  # <-- MUDANÇA: O dado vem da seção 'files'
    help='Arquivo .txt para análise'
)
# --- [FIM DAS MUDANÇAS] ---


# 2. Crie um "namespace" para organizar a API
ns = api.namespace('processing', description='Processamento de Documentos DLP/UBA')


# 3. Mude de @app.route para @ns.route e use uma Classe
@ns.route('/process_document')
class DocumentProcessor(Resource):
    """
    Este é o "endpoint" da API. O Front-end vai chamar esta URL.
    """

    @ns.doc('process_document_content')
    # <-- MUDANÇA: Usar o parser em vez do 'model'
    @ns.expect(file_upload_parser)
    def post(self):
        """
        Processa o conteúdo de um documento, classifica o sigilo e analisa o comportamento do usuário.
        """
        try:
            # --- [INÍCIO DAS MUDANÇAS NO POST] ---

            # 1. Pega os dados usando o parser
            args = file_upload_parser.parse_args()
            username = args['username']
            uploaded_file = args['file']  # Este é um objeto FileStorage

            # 2. Valida o arquivo
            if not uploaded_file or uploaded_file.filename == '':
                return {"error": "Nenhum arquivo enviado."}, 400

            if not uploaded_file.filename.endswith('.txt'):
                return {"error": "Arquivo inválido. Apenas .txt é permitido."}, 400

            print(f"\n--- API: Nova Requisição Recebida ---")
            print(f"Usuário: {username}")
            print(f"Arquivo Recebido: {uploaded_file.filename}")

            # 3. Lê o conteúdo do arquivo
            try:
                # .read() retorna bytes, então decodificamos para string
                content_bytes = uploaded_file.read()
                content = content_bytes.decode('utf-8')
            except UnicodeDecodeError:
                return {"error": "Não foi possível ler o arquivo. Verifique a codificação (deve ser UTF-8)."}, 400
            except Exception as e:
                return {"error": f"Erro ao ler o arquivo: {e}"}, 500

            # --- [FIM DAS MUDANÇAS NO POST] ---

            # 2. Cria um "hash" (usando o 'content' lido do arquivo)
            doc_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]

            # 3. [CHAMADA À IA]
            print("Executando classificador de sigilo (Rede Neural Keras)...")
            secrecy_level = classify_with_neural_network(content)
            print(f"  -> Nível de Sigilo determinado: {secrecy_level}")

            # 4. [CHAMADA AO UBA]
            print("Registrando acesso e analisando comportamento (UBA/SQLite)...")
            # A lógica UBA já está pronta para tratar "estagiario"
            uba_result = log_access_for_uba(username, doc_hash, secrecy_level, action="api_access")
            print("--- Processamento da API Concluído ---")

            # 5. Retorna uma resposta JSON
            response = {
                "username": username,
                "doc_hash": doc_hash,
                "classified_level": secrecy_level,
                "uba_analysis": uba_result,
                "processed_filename": uploaded_file.filename
            }
            # Em flask-restx, você pode retornar o dicionário diretamente
            return response, 200

        except Exception as e:
            print(f"[ERRO NA API] Ocorreu um erro: {e}")
            return {"error": f"Erro interno no servidor: {e}"}, 500

# --- (REMOVER O if __name__ == '__main__' DAQUI) ---