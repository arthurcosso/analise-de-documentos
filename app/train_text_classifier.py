import numpy as np
import pickle
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Embedding, GlobalAveragePooling1D, Dense
from tensorflow.keras.utils import to_categorical
import os
# --- 1. Dados de Treinamento (Carregados de Ficheiros) ---
print("--- Iniciando Treinamento do Modelo (Lendo Ficheiros) ---")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRAINING_DATA_DIR = os.path.join(BASE_DIR, 'training_data')
MODELS_DIR = os.path.join(BASE_DIR, 'models')
os.makedirs(MODELS_DIR, exist_ok=True)

texts = []
labels = []

# Mapeamento: Ficheiro -> Rótulo (Label)
# 0 = PUBLICO, 1 = INTERNO, 2 = CONFIDENCIAL
files_to_load = {
    'doc_publico.txt': 0,
    'doc_interno.txt': 1,
    'doc_confidencial.txt': 2
}

print("Carregando dados dos ficheiros .txt...")
for filename, label in files_to_load.items():
    # Crie o caminho completo para o arquivo de dados
    file_path = os.path.join(TRAINING_DATA_DIR, filename)

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Lê o ficheiro linha por linha
            for line in f:
                line = line.strip() # Remove espaços em branco e quebras de linha
                if line: # Ignora linhas em branco
                    texts.append(line)
                    labels.append(label)
        print(f"  -> Carregado com sucesso: {filename} (Rótulo: {label})")
    except FileNotFoundError:
        print(f"[ERRO] Ficheiro não encontrado: {filename}. Certifique-se que ele está no mesmo diretório.")
        # Pode querer parar a execução aqui se o ficheiro for crítico
    except Exception as e:
        print(f"[ERRO] Não foi possível ler {filename}: {e}")

if not texts:
    print("[ERRO FATAL] Nenhum dado de treino foi carregado. Terminando.")
    exit()

print(f"\nTotal de {len(texts)} exemplos de treino carregados.")


# --- 2. Pré-processamento de Texto ---
# Tokenizer: Transforma palavras em índices numéricos (ex: "audiência" -> 5)
tokenizer = Tokenizer(num_words=1000, oov_token="<UNK>")
tokenizer.fit_on_texts(texts)

# Crie o caminho de salvamento correto para o tokenizer
TOKENIZER_PATH = os.path.join(MODELS_DIR, 'tokenizer.pkl')

# Salva o tokenizer para usá-lo no script principal
with open(TOKENIZER_PATH, 'wb') as handle:
    pickle.dump(tokenizer, handle, protocol=pickle.HIGHEST_PROTOCOL)
    print(f"Tokenizer salvo em {TOKENIZER_PATH}")

# texts_to_sequences: Converte as frases em listas de números
sequences = tokenizer.texts_to_sequences(texts)

# pad_sequences: Garante que todas as listas tenham o mesmo tamanho
MAX_SEQUENCE_LEN = 20  # O tamanho máximo de sequência que o modelo aceitará
X = pad_sequences(sequences, maxlen=MAX_SEQUENCE_LEN)

# Converte os rótulos para o formato "one-hot"
y = to_categorical(labels, num_classes=3)

# --- 3. Arquitetura da Rede Neural (Classificação) ---
print("Construindo arquitetura do modelo...")
model = Sequential()
model.add(Embedding(input_dim=len(tokenizer.word_index) + 1,
                    output_dim=16,
                    input_length=MAX_SEQUENCE_LEN))
model.add(GlobalAveragePooling1D())
model.add(Dense(units=8, activation='relu'))
model.add(Dense(units=3, activation='softmax')) # 3 classes, 'softmax' para classificação

# --- 4. Compilação e Treinamento ---
model.compile(loss='categorical_crossentropy',
              optimizer='adam',
              metrics=['accuracy'])

print("Treinando o modelo...")
model.fit(X, y, epochs=50, batch_size=2, verbose=0)
print("Treinamento concluído.")

# --- 5. Salvar o Modelo ---
# Crie o caminho de salvamento correto para o modelo
MODEL_PATH = os.path.join(MODELS_DIR, 'text_classifier_model.keras')

model.save(MODEL_PATH)
print(f"Modelo salvo em '{MODEL_PATH}'")
print("--- Treinamento Finalizado ---")

