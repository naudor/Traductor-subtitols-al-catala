- Heu de tenir un compte GPT Plus
- Vigilar que les rutes no tinguin espai ni caracters especials
- Heu de tenir  permisos d'escriptura en la carpeta dels fitxers MKV ja que el subtitol traudit es guardara allí
- Millor si teniu els fitxers en una carpeta del mateix ordinador on esteu executant el docker per evitar problemes de xarxa entre la del ordinador i la propia del docker
- Per descarregar la imatge:
            
- Per executar-lo:
            docker run --rm -e OPENAI_API_KEY="la_teva_API_KEY" -v directori_on_estiguin_els_fitxers_MKV:/data traductor_subtitols /data
