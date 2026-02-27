import json

def Principal(message_data,JData_Plugins):
    # Iniciamos la estructura base
    keyboard = []
    # Fila 1: Un solo botón
    fila1 = [{"text": "ejecuta modelo", "callback_data": "modelo"}]
    keyboard.append(fila1)
    # armo objeto reply_markup
    reply_markup = {"inline_keyboard": keyboard}
    # Armo mensaje de vuelta
    Mensaje_txt = "Prueba de botones"
    # Unimos el objeto final
    reply_markup = {
        "reply_markup": reply_markup,
        "txt_mensaje" : Mensaje_txt
        }
    return [{
        "Tipo": "reply_markup",
        "Mensaje": reply_markup
    }
    ]