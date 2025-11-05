import os
import sys

# Verificar dependências antes de importar
try:
    import numpy as np
    import pickle
    from tensorflow.keras.preprocessing.text import Tokenizer
    from tensorflow.keras.preprocessing.sequence import pad_sequences
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import Embedding, GlobalAveragePooling1D, Dense
    from tensorflow.keras.utils import to_categorical
    from sklearn.model_selection import train_test_split
    import matplotlib.pyplot as plt
except ImportError as e:
    print("="*60)
    print("❌ ERRO: Dependências não instaladas!")
    print("="*60)
    print(f"\nErro: {e}")
    print("\n📦 Para instalar as dependências, execute:")
    print("   pip install -r requirements.txt")
    print("\nOu instale manualmente:")
    print("   pip install tensorflow numpy scikit-learn matplotlib")
    print("="*60)
    sys.exit(1)


# --- 1. Dados de Treinamento (Carregados de Ficheiros) ---
print("--- Iniciando Treinamento do Modelo (Lendo Ficheiros) ---")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRAINING_DATA_DIR = os.path.join(BASE_DIR, 'training_data')

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
        # --- [CORREÇÃO] Use 'file_path' em vez de 'filename' aqui ---
        with open(file_path, 'r', encoding='utf-8') as f:
            # Lê o ficheiro linha por linha
            for line in f:
                line = line.strip() # Remove espaços em branco e quebras de linha
                if line: # Ignora linhas em branco
                    texts.append(line)
                    labels.append(label)
        print(f"  -> Carregado com sucesso: {filename} (Rótulo: {label})")
    except FileNotFoundError:
        print(f"[ERRO] Ficheiro não encontrado: {file_path}. Certifique-se que ele está no mesmo diretório.")
        # Pode querer parar a execução aqui se o ficheiro for crítico
    except Exception as e:
        print(f"[ERRO] Não foi possível ler {file_path}: {e}")

if not texts:
    print("[ERRO FATAL] Nenhum dado de treino foi carregado. Terminando.")
    exit()

print(f"\nTotal de {len(texts)} exemplos de treino carregados.")


# --- 2. Pré-processamento de Texto ---
tokenizer = Tokenizer(num_words=1000, oov_token="<UNK>")
tokenizer.fit_on_texts(texts)

MODELS_DIR = os.path.join(BASE_DIR, 'models')
os.makedirs(MODELS_DIR, exist_ok=True)
TOKENIZER_PATH = os.path.join(MODELS_DIR, 'tokenizer.pkl')

# --- [CORREÇÃO] Use a variável TOKENIZER_PATH, não a string 'TOKENIZER_PATH' ---
with open(TOKENIZER_PATH, 'wb') as handle:
    pickle.dump(tokenizer, handle, protocol=pickle.HIGHEST_PROTOCOL)
    print(f"Tokenizer salvo em {TOKENIZER_PATH}")

sequences = tokenizer.texts_to_sequences(texts)
MAX_SEQUENCE_LEN = 20
X = pad_sequences(sequences, maxlen=MAX_SEQUENCE_LEN)
y = to_categorical(labels, num_classes=3)

# --- [NOVO] Divisão de Treino e Validação ---
# Separa 20% dos dados para validação (teste)
X_treino, X_val, y_treino, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
print(f"Dados divididos: {len(X_treino)} para treino, {len(X_val)} para validação.")
# --- [FIM NOVO] ---


# --- 3. Arquitetura da Rede Neural (Classificação) ---
print("Construindo arquitetura do modelo...")
model = Sequential()
model.add(Embedding(input_dim=len(tokenizer.word_index) + 1,
                    output_dim=16,
                    input_length=MAX_SEQUENCE_LEN))
model.add(GlobalAveragePooling1D())
model.add(Dense(units=8, activation='relu'))
model.add(Dense(units=3, activation='softmax'))

# --- 4. Compilação e Treinamento ---
model.compile(loss='categorical_crossentropy',
              optimizer='adam',
              metrics=['accuracy'])

print("Treinando o modelo...")
# --- [MODIFICADO] Adicionado 'validation_data' e salvo em 'resultado' ---
resultado = model.fit(X_treino, y_treino,
                      epochs=50,
                      batch_size=2,
                      validation_data=(X_val, y_val), # <-- Chave para o gráfico
                      verbose=0)
# --- [FIM MODIFICADO] ---

print("Treinamento concluído.")

# --- [NOVO] CÓDIGO DO GRÁFICO DE OVERFITTING ---
print("Gerando gráficos de overfitting...")

# Gráfico de Acurácia
plt.plot(resultado.history['accuracy'])
plt.plot(resultado.history['val_accuracy'])
plt.title('Acurácia do Modelo (Overfitting Check)')
plt.ylabel('Acurácia')
plt.xlabel('Época')
plt.legend(['Treino', 'Validação'], loc='upper left')
plt.grid(True)
plt.savefig(os.path.join(MODELS_DIR, 'grafico_acuracia.png'))
plt.clf() # Limpa a figura

# Gráfico de Perda (Loss)
plt.plot(resultado.history['loss'])
plt.plot(resultado.history['val_loss'])
plt.title('Perda (Loss) do Modelo (Overfitting Check)')
plt.ylabel('Perda (Loss)')
plt.xlabel('Época')
plt.legend(['Treino', 'Validação'], loc='upper left')
plt.grid(True)
plt.savefig(os.path.join(MODELS_DIR, 'grafico_perda.png'))
plt.clf() # Limpa a figura

print(f"Gráficos 'grafico_acuracia.png' e 'grafico_perda.png' salvos em {MODELS_DIR}")
# --- [FIM NOVO] ---


# --- 5. Salvar o Modelo ---
MODEL_PATH = os.path.join(MODELS_DIR, 'text_classifier_model.keras')
model.save(MODEL_PATH)
print(f"Modelo salvo em '{MODEL_PATH}'")
print("--- Treinamento Finalizado ---")