# Escullim una imatge base lleugera (ex: Debian slim o Alpine).
# Aquí faig servir Debian Slim per comoditat.
FROM python:3.9-slim

# Instal·lem mkvtoolnix (per tenir mkvmerge, mkvextract, etc.)
# A Debian-based: 
RUN apt-get update && apt-get install -y mkvtoolnix && rm -rf /var/lib/apt/lists/*

# Creem un directori per l'app
WORKDIR /app

# Copiem els fitxers necessaris
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY traductor_subtitols.py .
# Si vols copiar tot un directori, pots fer: COPY . .

# Punt d'entrada per defecte. 
# Aquí, com a exemple, fem que el contenidor executi "python traductor_subtitols.py"
# i esperi arguments. 
ENTRYPOINT ["python", "traductor_subtitols.py"]
# Amb això, si poses alguna cosa al final de "docker run", la interpretarà com a
# arguments. Ex: docker run <img> /data
