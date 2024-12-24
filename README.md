# Traductor de Subtítols al Català

Aquesta eina permet traduir automàticament els subítols d'arxius `.mkv` al català mitjançant l'API de ChatGPT. Funciona dins d'un contenidor Docker, la qual cosa assegura un entorn controlat i fàcil d'executar en qualsevol màquina.

**Els subtítols del fitxer han d'estar en format SRT**

---

## **Requisits previs**

Abans de començar, assegura’t de tenir instal·lat el següent:

1. **Docker**
2. **Clau API de OpenAI**: Necessitaràs una clau d'API vàlida per utilitzar el model `gpt-4o-mini`. Pots obtenir-ne una a [OpenAI](https://platform.openai.com/).
3. **Fitxers `.mkv`** amb subítols: L'aplicació busca fitxers `.mkv` en la carpeta local que especifiquis.

---

## **Instal·lació**

Segueix aquests passos per configurar el projecte:

### 1. **Clona el repositori**

Descarrega el codi font del repositori al teu ordinador:

```bash
git clone https://github.com/naudor/Traductor-subtitols-al-catala.git
cd Traductor-subtitols-al-catala
```

### 2. **Construeix la imatge Docker**

Crea la imatge Docker necessària per executar l’aplicació:

```bash
docker build -t traductor_subtitols .
```

---

## **Com utilitzar-ho**

### 1. **Prepara els teus fitxers**

Assegura’t que tens els teus fitxers `.mkv` en una carpeta local al teu ordinador. Per exemple, `C:\Videos\`.

### 2. **Executa el contenidor**

Utilitza el següent comandament per executar el traductor:

```bash
docker run --rm -e OPENAI_API_KEY="LA_TEVA_CLAU_API" -v "C:\\Videos:/data" traductor_subtitols /data
```

#### Explicació del comandament:
- **`--rm`**: Elimina el contenidor automàticament després de l'execució.
- **`-e OPENAI_API_KEY="LA_TEVA_CLAU_API"`**: Passa la teva clau API com a variable d'entorn.
- **`-v "C:\\Videos:/data"`**: Munta la carpeta local `C:\Videos` dins del contenidor com a `/data`.
- **`traductor_subtitols /data`**: Inicia el programa i processa els fitxers `.mkv` dins de la carpeta `/data`.

### 3. **Resultats**

Els subítols traduïts es desaran al mateix directori que els teus fitxers `.mkv`, amb el sufix `_cat.str`. Per exemple:

```
Original: video.mkv
Traducció: video_cat.str
```

Per veure els subtítols mentres veieu el contingut, ho podeu fer fer de dues maneres:
- Configurant el vostre reproductorbfe vidro perque inclogui el nou subtitol
- Utilitzant el programa [MKVMerge](https://mkvtoolnix.download/downloads.html) per sfrgir el dubtitol al fitxer .mkv
---

## **Exemples**

### Exemple bàsic
Si tens els teus fitxers `.mkv` a `C:\Users\Naudor\Videos`, executa:

```bash
docker run --rm -e OPENAI_API_KEY="sk-xxxxxxx" -v "C:\\Users\\Naudor\\Videos:/data" traductor_subtitols /data
```

---

## **Resolució de problemes**

- Vigilar que les rutes no tinguin espai ni caràcters especials.

- Els subtítols del fitxer han d'estar en format SRT.

- Heu de tenir permisos d'escriptura en la carpeta dels fitxers MKV, ja que el subtítol traduït es guardarà allí.

### “No s'han trobat fitxers .mkv a la carpeta /data”
- Comprova que la carpeta especificada conté fitxers `.mkv`.
- Assegura’t que has utilitzat cometes dobles si la ruta conté espais.

### “Error: OPENAI_API_KEY no definida”
- Verifica que has passat la clau API correctament amb `-e OPENAI_API_KEY="LA_TEVA_CLAU_API"`.

### Problemes de xarxa o muntatge
- Si estàs utilitzant una carpeta de xarxa o unitats mapejades, assegura’t que està correctament compartida amb Docker.
- Pots provar de copiar els fitxers a una carpeta local.

---

## **Contribució**

Les contribucions són benvingudes! Si vols afegir funcionalitats o reportar problemes, obre un **issue** o envia un **pull request**.

---

## **Llicència**

Aquest projecte està llicenciat sota la llicència MIT. Consulta el fitxer `LICENSE` per més informació.

---

## **Contacte**

Si tens preguntes o suggeriments, no dubtis a contactar amb mi mitjançant el repositori de GitHub.

