import os

if 'Ambiente' in os.environ:
    if os.environ['Ambiente'] == 'PROD':
        URL_Gestion = os.environ['URL_Gestion']
else:
    URL_Gestion = "http://monibot.agpsau.gob.ar/"
    #URL_Gestion = "http://127.0.0.1:9000"

def Principal(message_data, JData_Plugins):
    Rta = []
    # Bucket 1: Encabezado
    bucket_uno = {
        "Tipo": "texto",
        "Mensaje": "Tienes acceso a los siguientes menues:\n"
    }
    Rta.append(bucket_uno)
    for Menu in message_data['JToken']['menus']:
        Mensaje_txt = "Menu: " + Menu['nombre']
        keyboard = []
        for item in Menu['items']:
            Descripcion = item['nombre']
            Plugin = item['plugin'] + " menu"
            # Fila 1: Un solo botón
            fila1 = [{"text": Descripcion, "callback_data": Plugin}]
            keyboard.append(fila1)
            reply_markup_in = {"inline_keyboard": keyboard}
            reply_markup = {
                "reply_markup": reply_markup_in,
                "txt_mensaje": Mensaje_txt
            }
            bucket_Menu = {
                "Tipo": "reply_markup",
                "Mensaje": reply_markup
            }
        Rta.append(bucket_Menu)
    return Rta

