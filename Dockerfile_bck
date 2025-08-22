# Escollim la imatge base (Python 3.9 slim).
FROM python:3.9-slim

# Actualitzem i instal·lem els paquets bàsics necessaris:
# - mkvtoolnix (per mkvmerge, mkvextract, etc.)
# - curl (per descarregar l'script)
# - apt-utils (a vegades evita problemes en instal·lacions)
# - gnupg (per gestionar claus GPG)
# - lsb-release (necessari per determinar la versió de la distro)
# - apt-transport-https (per si de cas es fan servir repos HTTPS)
RUN apt-get update && apt-get install -y \
    mkvtoolnix \
    curl \
    apt-utils \
    gnupg \
    lsb-release \
    apt-transport-https \
 && rm -rf /var/lib/apt/lists/*

# Instal·lem el repositori d'Apertium
RUN curl -sS https://apertium.projectjj.com/apt/install-release.sh | bash

# Instal·lem els paquets necessaris d'Apertium
RUN apt-get update && apt-get install -y \
    apertium-all-dev \
    apertium-spa-cat \
	apertium-eng-cat \
 && rm -rf /var/lib/apt/lists/*

# Creem el directori per l'app
WORKDIR /app

# Copiem i instal·lem requeriments de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiem el fitxer de l'script
COPY traductor_subtitols.py .

# Punt d'entrada per defecte: executa l'script de Python
ENTRYPOINT ["python", "traductor_subtitols.py"]
