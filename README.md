
# Traductor de Subtítols al Català

Aquesta eina permet traduir automàticament els subtítols dels arxius `.mkv` al català mitjançant un model LLM (per exemple, OpenAI o DeepSeek). Funciona dins d'un contenidor Docker, assegurant un entorn controlat i fàcil d'executar en qualsevol màquina.

> **Nota:** Els subtítols del fitxer han d'estar en format **SRT**.

---

## **Requisits previs**

Abans de començar, assegura’t de tenir:

1. **Docker** instal·lat al teu ordinador.
2. **Clau API vàlida**: Necessitaràs una clau d'API per utilitzar el model. La clau s'especifica a través de la variable d'entorn **API_KEY**.  
3. **Model LLM**: Selecciona el model que vols utilitzar (per exemple, `gpt-4o-mini` per OpenAI o `deepseek-chat` per DeepSeek). Aquest valor s'especifica amb la variable d'entorn **MODEL**.
4. **Fitxers `.mkv` amb subtítols** en format **SRT**.

> **Nota:** La URL de l'endpoint s'estableix automàticament segons el model triat (si el model comença per `deepseek` s'utilitzarà l'endpoint de DeepSeek, sinó es farà servir l'endpoint d'OpenAI).

---

## **Instal·lació**

### 1. **Clona el repositori**

Descarrega el codi font del repositori:

```bash
git clone https://github.com/naudor/Traductor-subtitols-al-catala.git
cd Traductor-subtitols-al-catala
```

### 2. **Construeix la imatge Docker**

Crea la imatge Docker necessària per executar l’eina:

```bash
docker build -t traductor_subtitols .
```

---

## **Com utilitzar-ho**

### 1. **Prepara els teus fitxers**

Assegura’t que tens els teus fitxers `.mkv` en una carpeta local. Per exemple, `C:\Videos\`.

### 2. **Executa el contenidor**

Utilitza el següent comandament per executar el traductor:

```bash
docker run --rm \
  -e API_KEY="LA_TEVA_CLAU_API" \
  -e MODEL="gpt-4o-mini" \
  -v "C:\\Videos:/data" \
  traductor_subtitols /data
```

*Amb aquest comandament es traduiran els subtítols dels fitxers `.mkv` i es desarà un fitxer SRT traduït amb el sufix `_cat.srt` en el mateix directori.*

### 3. **Opcions avançades: Adjuntar els subtítols traduïts al `.mkv`**

Si vols incrustar automàticament els subtítols traduïts al fitxer `.mkv` original, afegeix la variable d’entorn `EMBED_SUBS=true` al comandament:

```bash
docker run --rm \
  -e API_KEY="LA_TEVA_CLAU_API" \
  -e MODEL="gpt-4o-mini" \
  -e EMBED_SUBS=true \
  -v "C:\\Videos:/data" \
  traductor_subtitols /data
```

Amb aquesta opció, es crearà un nou fitxer `.mkv` que inclourà els subtítols en català, amb el mateix nom que l'original però amb el sufix `_CAT`.  
Exemple:

```
Original: video.mkv
Traducció: video_CAT.mkv
```

---

## **Resultats**

Els subtítols traduïts es desaran al mateix directori que els teus fitxers `.mkv`:

1. **Nom del subtítol traduït**: `video_cat.srt`.
2. **Nom del fitxer `.mkv` amb subtítols incrustats** (opcional): `video_CAT.mkv`.

Pots veure els subtítols traduïts:
- Configurant el reproductor de vídeo per carregar el subtítol manualment.
- Si has seleccionat l'opció d'incrustar, reproduint directament el fitxer `video_CAT.mkv`.

---

## **Resolució de problemes**

### “No s'han trobat fitxers .mkv a la carpeta /data”
- Comprova que la carpeta especificada conté fitxers `.mkv`.
- Si la ruta conté espais, assegura’t d’utilitzar cometes dobles.

### “Error: API_KEY no definida”
- Verifica que has passat la clau API correctament amb `-e API_KEY="LA_TEVA_CLAU_API"`.

### Subtítols no disponibles o incorrectes
- Assegura’t que els subtítols són en format SRT. Si no ho són, pots convertir-los manualment amb eines com [Subtitle Edit](https://github.com/SubtitleEdit/subtitleedit).

### Problemes amb la carpeta de fitxers
- Assegura’t que la carpeta especificada té permisos d’escriptura, ja que el subtítol traduït o el fitxer `.mkv` amb subtítols incrustats es desaran allí.

---

## **Contribució**

Si tens idees per millorar l'eina o vols reportar un problema, obre un **issue** o envia un **pull request** al repositori de GitHub.

---

## **Llicència**

Aquest projecte està llicenciat sota la llicència MIT. Consulta el fitxer `LICENSE` per més informació.

---

## **Contacte**

Si tens dubtes o suggeriments, pots contactar amb mi mitjançant el repositori de GitHub.

---

Aquest Readme reflecteix les noves funcionalitats i la configuració dinàmica del client API basat en el model triat.
