#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import glob
import subprocess
import json
from tqdm import tqdm
from openai import OpenAI

###############################################################################
#                  Detecció automàtica de la pista de subtítols              #
###############################################################################

def trobar_pista_subtitols(mkv_path: str) -> int:
    """
    Retorna el número de pista de subtítols més adequat seguint l'ordre de prioritat:
      1. Castellà (spa/es) no hearing impaired, no commentary
      2. Anglès (eng/en) no hearing impaired, no commentary
    Retorna -1 si no troba cap pista que compleixi el criteri.
    """
    try:
        result = subprocess.run(
            ["mkvmerge", "-J", mkv_path],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"Error executant mkvmerge -J sobre {mkv_path}: {e}")
        return -1

    try:
        info = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        print(f"No s'ha pogut parsejar el JSON de {mkv_path}: {e}")
        return -1

    if "tracks" not in info:
        print(f"No hi ha informació de 'tracks' al JSON de {mkv_path}")
        return -1

    pistes_subtitols = [t for t in info["tracks"] if t.get("type") == "subtitles"]

    def es_valida(track, idioma_buscat):
        """Comprova si la pista coincideix amb l'idioma i no és SDH/Comentari."""
        props = track.get("properties", {})
        lang = props.get("language", "").lower()
        track_name = props.get("track_name", "") or ""

        if not (lang.startswith(idioma_buscat)):
            return False

        hearing_impaired = props.get("hearing_impaired", False)
        sdh_indicadors = ["sdh", "hearing", "discapacitat"]
        commentary_indicadors = ["commentary", "director", "comentarios", "comment"]

        if hearing_impaired:
            return False

        track_name_lower = track_name.lower()
        for word in sdh_indicadors + commentary_indicadors:
            if word in track_name_lower:
                return False

        return True

    # 1) Castellà
    pistes_castella = [
        p for p in pistes_subtitols 
        if es_valida(p, "es") or es_valida(p, "spa")
    ]
    if pistes_castella:
        return pistes_castella[0]["id"]

    # 2) Anglès
    pistes_angles = [
        p for p in pistes_subtitols
        if es_valida(p, "en") or es_valida(p, "eng")
    ]
    if pistes_angles:
        return pistes_angles[0]["id"]

    return -1

###############################################################################
#                         Funcions d'extracció i traducció                   #
###############################################################################

def extreure_subtitols(mkv_path: str, track_id: int) -> str:
    """
    Donat el camí d'un fitxer .mkv i un track_id, executa 'mkvextract tracks'
    per extreure la pista en un fitxer .srt (mateix nom que el .mkv).
    Retorna el camí del fitxer .srt generat o cadena buida si hi ha error.
    """
    if track_id < 0:
        return ""

    base_name = os.path.splitext(mkv_path)[0]
    srt_path = base_name + ".srt"

    command = [
        "mkvextract",
        "tracks",
        mkv_path,
        f"{track_id}:{srt_path}"
    ]
    try:
        subprocess.run(command, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print(f"Error en extreure la pista {track_id} de {mkv_path}: {e}")
        return ""

    # Comprovar si s'ha creat correctament
    if not os.path.isfile(srt_path):
        return ""

    return srt_path

def llegir_subtitols_per_blocs(nom_fitxer: str, mida_bloc=50):
    """
    Llegeix el fitxer .srt i retorna una llista de blocs,
    on cada bloc conté fins a 'mida_bloc' subtítols.
    """
    with open(nom_fitxer, 'r', encoding='utf-8') as f:
        linies = f.readlines()

    blocs = []
    bloc_actual = []
    contador_subtitols = 0

    for linia in linies:
        # Mirem si la línia és exactament un nombre
        try:
            numero = int(linia.strip())
            # Si hem arribat a 'mida_bloc' subtítols, tanquem bloc
            if contador_subtitols == mida_bloc:
                blocs.append("".join(bloc_actual))
                bloc_actual = []
                contador_subtitols = 0

            contador_subtitols += 1
            bloc_actual.append(linia)
        except ValueError:
            bloc_actual.append(linia)

    if bloc_actual:
        blocs.append("".join(bloc_actual))

    return blocs

def traduir_bloc_gpt4(text_bloc: str, client: OpenAI, model: str = "gpt-4o-mini") -> str:
    """
    Envia un bloc de subtítols al model GPT-4o-mini per obtenir la traducció al català.
    Retorna el text traduït.
    """
    prompt = (
        "Traduiex el següent text a català. "
        "No modifiquis la numeració ni els temps dels subtítols, només el text.\n\n"
        f"{text_bloc}"
    )
    try:
        resposta = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Ets un traductor expert de subtítols."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        text_traduit = resposta.choices[0].message.content
        return text_traduit
    except Exception as e:
        print("S'ha produït un error en connectar amb l'API d'OpenAI:", e)
        return ""

def traduir_fitxer_subtitols(nom_fitxer_srt: str, model: str = "gpt-4o-mini") -> str:
    """
    Llegeix un fitxer .srt, el divideix en blocs de 50 subtítols,
    tradueix cada bloc i retorna la concatenació final.
    """
    blocs_subtitols = llegir_subtitols_per_blocs(nom_fitxer_srt, mida_bloc=50)
    client = OpenAI()
    resultat_total = []

    for bloc in tqdm(blocs_subtitols, desc=f"Traduint blocs ({os.path.basename(nom_fitxer_srt)})"):
        text_traduit = traduir_bloc_gpt4(bloc, client, model=model)

        # Afegim un salt de línia final per evitar que l'últim subtítol
        # del bloc quedi enganxat amb el primer del bloc següent.
        if text_traduit and not text_traduit.endswith("\n"):
            text_traduit += "\n"

        resultat_total.append(text_traduit)

    return "".join(resultat_total)

###############################################################################
#                Funció extra: adjuntar subtítols traduïts al MKV            #
###############################################################################

def adjuntar_subtitols_mkv(mkv_path: str, srt_path: str, idioma: str = "cat") -> str:
    """
    Fa servir mkvmerge per afegir la pista de subtítols .srt al .mkv original.
    Retorna el path del nou fitxer .mkv generat, 
    que ara s'anomena igual que l'original però amb '_CAT' al final.
    """
    base_name = os.path.splitext(mkv_path)[0]
    nou_mkv = base_name + "_CAT.mkv"

    # --language 0:cat indica a mkvmerge que la pista té codi d'idioma 'cat'
    command = [
        "mkvmerge",
        "-o", nou_mkv,
        mkv_path,
        "--language", "0:cat",
        srt_path
    ]
    try:
        subprocess.run(command, check=True, capture_output=True)
        print(f"S'ha creat el nou fitxer MKV amb subtítols catalans: {nou_mkv}")
    except subprocess.CalledProcessError as e:
        print(f"Error en afegir subtítols a {mkv_path}: {e}")
        return ""

    return nou_mkv

###############################################################################
#                         Lògica principal: processar MKVs                    #
###############################################################################

def processar_carpeta_mkv(ruta_carpeta: str, embed_subs: bool = False):
    """
    - Agafa tots els fitxers .mkv de la carpeta.
    - Automàticament detecta la pista de subtítols en castellà (no SDH/commentary),
      si no n'hi ha, anglès (no SDH/commentary).
    - Extreu la pista en .srt.
    - Tradueix en blocs de 50 i desa la traducció a *_cat.srt.
    - Si embed_subs=True, crida mkvmerge per incrustar els subtítols traduïts
      en un nou fitxer MKV (amb '_CAT' al final del nom).
    """
    patrons = os.path.join(ruta_carpeta, "*.mkv")
    mkv_files = glob.glob(patrons)

    if not mkv_files:
        print(f"No s'han trobat fitxers .mkv a la carpeta {ruta_carpeta}")
        return

    for mkv_path in tqdm(mkv_files, desc="Processant fitxers MKV"):
        # 1) Determinar quina pista de subtítols cal extreure
        pista_id = trobar_pista_subtitols(mkv_path)
        if pista_id < 0:
            print(f"No s'ha trobat cap pista de subtítols en castellà ni anglès per {mkv_path}")
            continue

        # 2) Extreure la pista
        srt_path = extreure_subtitols(mkv_path, pista_id)
        if not srt_path or not os.path.isfile(srt_path):
            print(f"No s'ha pogut extreure la pista {pista_id} de {mkv_path}.")
            continue

        # 3) Traduir el fitxer .srt
        resultat_traduit = traduir_fitxer_subtitols(srt_path, model="gpt-4o-mini")

        # 4) Desa el resultat final com a *_cat.srt
        nom_arxiu_sense_ext, _ = os.path.splitext(srt_path)
        fitxer_sortida = nom_arxiu_sense_ext + "_cat.srt"
        with open(fitxer_sortida, 'w', encoding='utf-8') as f:
            f.write(resultat_traduit)

        print(f"  -> Fitxer traduït i guardat a: {fitxer_sortida}")

        # 5) Si embed_subs=True, fem mkvmerge per afegir subtítols
        if embed_subs:
            adjuntar_subtitols_mkv(mkv_path, fitxer_sortida)

def main():
    # 1) Comprovem que hi hagi clau d'API al sistema
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: No s'ha trobat la clau d'API a la variable d'entorn OPENAI_API_KEY.")
        sys.exit(1)

    # 2) Llegim si hi ha variable d'entorn EMBED_SUBS
    # Qualsevol valor no buit (true, yes, 1...) l'interpretarem com a True
    embed_subs = False
    env_embed = os.getenv("EMBED_SUBS", "").strip().lower()
    if env_embed:
        embed_subs = True

    # 3) Comprovem arguments
    if len(sys.argv) < 2:
        print("Ús: python traductor_subtitols.py <carpeta_on_hi_ha_els_MKV>")
        print("   (Opcional) estableix EMBED_SUBS=true si vols afegir els subtítols .srt al .mkv.")
        sys.exit(1)

    carpeta = sys.argv[1]
    if not os.path.isdir(carpeta):
        print(f"Error: {carpeta} no és una carpeta vàlida.")
        sys.exit(1)

    processar_carpeta_mkv(carpeta, embed_subs=embed_subs)


if __name__ == "__main__":
    main()