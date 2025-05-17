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
#       Funció de detecció del track_id i l'idioma (castellà o anglès)        #
###############################################################################

def trobar_pista_subtitols(mkv_path: str):
    """
    Retorna un tuple (track_id, track_lang) segons l'ordre de prioritat:
      1. Castellà (spa/es) no hearing impaired, no commentary
      2. Anglès (eng/en) no hearing impaired, no commentary
    Retorna (-1, None) si no troba cap pista que compleixi el criteri.
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
        return -1, None

    try:
        info = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        print(f"No s'ha pogut parsejar el JSON de {mkv_path}: {e}")
        return -1, None

    if "tracks" not in info:
        print(f"No hi ha informació de 'tracks' al JSON de {mkv_path}")
        return -1, None

    pistes_subtitols = [t for t in info["tracks"] if t.get("type") == "subtitles"]

    def es_valida(track, idioma_buscat):
        """Comprova si la pista coincideix amb l'idioma i no és SDH/Comentari."""
        props = track.get("properties", {})
        lang = props.get("language", "").lower()
        track_name = props.get("track_name", "") or ""

        if not (lang.startswith(idioma_buscat)):
            return False

        hearing_impaired = props.get("hearing_impaired", False)
        forced_track = props.get("forced_track", False)
        sdh_indicadors = ["sdh", "hearing", "discapacitat"]
        commentary_indicadors = ["commentary", "director", "comentarios", "comment"]

        if hearing_impaired:
            return False
        
        if forced_track:
            return False

        track_name_lower = track_name.lower()
        for word in sdh_indicadors + commentary_indicadors:
            if word in track_name_lower:
                return False

        return True

    # 1) Castellà
    pistes_castella = [
        p for p in pistes_subtitols
        if es_valida(p, "spa")
    ]
    if pistes_castella:
        # Retornem el primer track ID que hem trobat i l'idioma "spa"
        return pistes_castella[0]["id"], "spa"

    # 2) Anglès
    pistes_angles = [
        p for p in pistes_subtitols
        if es_valida(p, "eng")
    ]
    if pistes_angles:
        # Retornem el primer track ID que hem trobat i l'idioma "eng"
        return pistes_angles[0]["id"], "eng"

    return -1, None

###############################################################################
#                         Funcions d'extracció i de divisió                   #
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

def llegir_subtitols_per_blocs(nom_fitxer: str, mida_bloc=10):
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

###############################################################################
#   Funció unificada de traducció amb API (GPT4/DeepSeek via LangChain)       #
###############################################################################

def traduir_bloc(text_bloc: str, client, model: str) -> str:
    """
    Envia un bloc de subtítols al model indicat per obtenir la traducció al català.
    Utilitza el client proporcionat i el model especificat.
    
    El prompt és:
      "Tradueix el següent text a català:
      {text_bloc}
      
      No modifiquis la numeració ni els temps dels subtítols, només el text.
      No tradueixis noms propis de persones.
      Contesta únicament amb el text traduït, ni una paraula més."
    """
    messages = [
        {"role": "system", "content": "Ets un traductor al català expert en subtítols."},
        {"role": "user", "content": (
            f"Tradueix el següent text a català:\n{text_bloc}\n\n"
            "No modifiquis la numeració ni els temps dels subtítols, només el text.\n"
            "No tradueixis noms propis de persones.\n"
            "Contesta únicament amb el text traduït, ni una paraula més."
            "Tradueix 'Corazón Sombrio' per 'Cor tenebrós', 'garracuerno' per 'Garracorna', 'azotamentes' per 'flagell de ments', 'risa' per 'rialla', 'mentonáculo' per 'mentonacle', "
            "'a salvo' per 'fora de perill', 'Tarareo' per 'taral·leig', 'escueta' per 'concisa', 'en cuanto' per 'tant bon punt', 'amanezca' per 'surti el sol', 'ojo avizor' per 'ull viu'"
            "'cambion' per 'metàmorf', 'juguetes' per 'juguines', 'Ojalá' per 'Tant de bo', 'impia' per 'impietosa', 'engendro' per 'abominació', 'ladrones' per 'lladres', 'sedienta' per 'assedegada'"
            "'siervo' per 'vassall', 'podrida' per 'púdrida', 'labia' per 'eloqüència', 'cabeza hueca' per 'cap de suro', 'mente colmena' per 'ment enllaçada', 'nauseabunda' per 'repugnant'"
            "'frasco' per 'flascó', 'conseguido' per 'aconseguit', 'diablillo' per 'dimoniet'', 'Jarro' per 'Gerra', 'piel robliza' per 'pell de roure', 'cáliz' per 'càliz', 'compañeros' per 'companys'"
            "'trampilla' per 'trapa', 'pócima' per 'pòcima', 'jamas pense' per 'mai hauria pensat', 'al acecho' per 'a la guait', 'picaro' per 'brivall', 'salpicadura' per 'esquitx', 'pillan' per 'atrapen'"
            "'me las piro' per 'foto el camp', 'empujoncito' per 'empenteta', 'bicho' per 'bestiola', 'hacha' per 'destral', 'te diviertes' per 'et diverteixes', 'pandilla' per 'colla', 'pilla' per 'agafa'"
            "'lenyador' per 'llenyataire','sabe a' per 'te gust a ', 'hinchado' per 'inflat', 'conozco' per 'conec', 'pesadilla' per 'malson', 'acometida' per 'escomesa', 'tañido' per 'repic', 'enano' per 'nan'"
            "'yelmo' per 'elm', 'rindete' per 'rendeix-te', 'estupendo' per 'fantàstic', 'ahínco' per 'afany', 'pastizal' per 'dineral', 'merecido' per 'merescut', 'manos a la obra' per 'anem per feina'"
            "'usa' per 'utilitza', 'colinas' per 'turons', 'sendero' per 'camí', 'date prisa' per 'afanya't', 'se cuelan' per 's'escolen', 'macheta' per 'ganivet gros', 'en un santiamen' per 'en un instant'"
            "'Lunar' per 'de la Lluna', 'pretendes' per 'pretens', 'bicho' per 'bestiola', 'sufres' per 'pateixes', 'Fallo' per 'Fracàs','apestas' per 'fas pudor'"
            "Si detectes que una paraula com 'cielo' s'utilitza com a mot carinyós, tradueix-la com 'rei' o 'carinyo', segons convingui. Si és literal, fes servir 'cel'."
            "Quan es parli en el text original de 'saga' com a sinonim de 'bruja' tradueix-lo per 'bruixa'"
        )}
    ]
    try:
        resposta = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3
        )
        text_traduit = resposta.choices[0].message.content
        return text_traduit
    except Exception as e:
        print(f"S'ha produït un error en connectar amb l'API amb el model {model}: {e}")
        return ""

###############################################################################
#    Funció que tradueix tot un fitxer SRT a partir de l'idioma detectat      #
###############################################################################

def traduir_fitxer_subtitols(nom_fitxer_srt: str, track_lang: str, model: str) -> str:
    """
    Llegeix un fitxer .srt, el divideix en blocs de 10 subtítols,
    tradueix cada bloc i retorna la concatenació final.
    S'obtindran la clau d'API i es configurarà la URL en funció del model triat.
    """
    # Obtenim la clau d'API
    api_key = os.getenv("API_KEY")
    if not api_key:
        print("Error: No s'ha trobat la clau d'API a la variable d'entorn API_KEY.")
        sys.exit(1)

    if model.lower().startswith("deepseek"):
        base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    else:
        base_url = os.getenv("BASE_URL", "https://api.openai.com/v1")

    client = OpenAI(api_key=api_key, base_url=base_url)

    blocs_subtitols = llegir_subtitols_per_blocs(nom_fitxer_srt, mida_bloc=10)
    resultat_total = []

    for bloc_original in tqdm(blocs_subtitols, desc=f"Traduint blocs ({os.path.basename(nom_fitxer_srt)})"):
        text_traduit = traduir_bloc(bloc_original, client, model)
        text_traduit = text_traduit.replace("'''", "")
        text_traduit += "\n\n"
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

    command = [
        "mkvmerge",
        "-o", nou_mkv,
        mkv_path,
        "--language", f"0:{idioma}",
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
    - Traduix en blocs de 10 i desa la traducció a *_cat.srt.
    - Si embed_subs=True, crida mkvmerge per incrustar els subtítols traduïts
      en un nou fitxer MKV (amb '_CAT' al final del nom).
    """
    # Obtenim el model a usar des de la variable d'entorn
    model = os.getenv("MODEL")
    if not model:
        print("Error: No s'ha trobat el model a la variable d'entorn MODEL.")
        sys.exit(1)

    patrons = os.path.join(ruta_carpeta, "*.mkv")
    mkv_files = glob.glob(patrons)

    if not mkv_files:
        print(f"No s'han trobat fitxers .mkv a la carpeta {ruta_carpeta}")
        return

    for mkv_path in tqdm(mkv_files, desc="Processant fitxers MKV"):
        # 1) Determinar quina pista de subtítols cal extreure i l'idioma
        pista_id, pista_lang = trobar_pista_subtitols(mkv_path)
        if pista_id < 0 or not pista_lang:
            print(f"No s'ha trobat cap pista de subtítols en castellà ni anglès per {mkv_path}")
            continue

        # 2) Extreure la pista
        srt_path = extreure_subtitols(mkv_path, pista_id)
        if not srt_path or not os.path.isfile(srt_path):
            print(f"No s'ha pogut extreure la pista {pista_id} de {mkv_path}.")
            continue

        # 3) Traduir el fitxer .srt (tenim en compte l'idioma original detectat)
        resultat_traduit = traduir_fitxer_subtitols(srt_path, pista_lang, model)

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
    # Comprovem que hi hagi clau d'API i model a les variables d'entorn
    if not os.getenv("API_KEY"):
        print("Error: No s'ha trobat la clau d'API a la variable d'entorn API_KEY.")
        sys.exit(1)
    if not os.getenv("MODEL"):
        print("Error: No s'ha trobat el model a la variable d'entorn MODEL.")
        sys.exit(1)

    # Llegim si hi ha variable d'entorn EMBED_SUBS
    embed_subs = False
    env_embed = os.getenv("EMBED_SUBS", "").strip().lower()
    if env_embed:
        embed_subs = True

    # Comprovem arguments
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
