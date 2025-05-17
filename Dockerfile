# Utilitzem una imatge base amb Python 3.9 slim
FROM python:3.9-slim-bookworm

# Actualitzem i instal·lem els paquets bàsics necessaris (mantenim mkvtoolnix per extreure els subtítols)
RUN apt-get update && apt-get install -y \
    mkvtoolnix \
    curl \
    apt-utils \
    gnupg \
    lsb-release \
    apt-transport-https \
 && rm -rf /var/lib/apt/lists/*

# Creem el directori per l'aplicació
WORKDIR /app

# Copiem el fitxer de requeriments de Python i instal·lem les dependències
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiem l'script de Python
COPY traductor_subtitols.py .

# Punt d'entrada: executa l'script de Python
ENTRYPOINT ["python", "traductor_subtitols.py"]
