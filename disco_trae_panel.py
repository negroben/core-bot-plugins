import ast
import json
import requests
import os
import logging
import sys
import html

# Crear logger
logger = logging.getLogger()
logger.setLevel(logging.ERROR)
# Crear manejador de consola (stdout)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
# Crear formateador
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
# Agregar manejador a logger
logger.addHandler(console_handler)

# Logueador
def loguea(linea):
  logger.error(linea)

if 'Ambiente' in os.environ:
    if os.environ['Ambiente'] == 'PROD':
        url_trae_panel = "http://trae_imagen:8001/captura_pantalla"
else:
    url_trae_panel = "http://localhost:8001/captura_pantalla"

def traemenu(plugins):
    msg = (
        "🧩 <b>Lista de paneles disponibles</b>\n"
        "📌 <i>Tocá un botón del menú (abajo) para ejecutarlo.</i>\n\n"
    )

    for item in plugins:
        panel = html.escape(str(item.get("ID")))
        desc  = html.escape(str(item.get("Desc", "")))

        msg += (
            f"🔹 <b>Panel {panel}</b>"
            f"   📝 {desc}\n"
            f"   ▶️ <code>trae_panel {panel}</code>\n\n"
        )
    return msg

def trae_imagen(URL,Headers,Resolucion):
    url = url_trae_panel
    data = {
        "URL": str(URL),
        "Headers": Headers,
        "Tamano": Resolucion
    }
    json_data = json.dumps(data)
    imagen = requests.request("POST", url, json=json_data)
    return imagen

def Arma_Pre_Msg(Pre_Msg,JToken):
    try:
        Pre_Msg = Pre_Msg.replace("{{$nombre}}",JToken['Nombre'])
    except:
        loguea("Fallo el reemplazo, sigo sin reemplazar")
    return Pre_Msg

def Principal(message_data,JData_Plugins):
    message_text = message_data['Mensaje']
    SToken = str(message_data['JToken'])
    JToken = ast.literal_eval(SToken)
    #JToken = json.loads(SToken)
    message_text = message_text.replace("trae_panel ","")
    LPalabras = message_text.split(" ")
    LpalabrasLen =LPalabras.__len__()
    try:
        Encontro = 0
        int(LPalabras[0])
        if LpalabrasLen == 1:
            for plugin in JData_Plugins:
                if plugin['ID'] == int(message_text.split(" ")[0]):
                    Encontro = 1
                    Pre_Msg = str(plugin['Pre_Msg'])
                    imagen = trae_imagen(plugin['URL'],plugin['Headers'],"800x600")
                    Jimagen = json.loads(imagen.text)
                    loguea(str(plugin['URL']))
                    loguea(Pre_Msg)
                    return [{
                                "Tipo": "texto",
                                "Mensaje": Arma_Pre_Msg(Pre_Msg,JToken)
                            },
                            {
                                "Tipo": Jimagen["Tipo"],
                                "Mensaje": Jimagen["Mensaje"]
                            },
                            {
                                "Tipo": "texto",
                                "Mensaje": "Chau, nos vemos la proxima"
                            }
                        ]
        else:
            return [{
                "Tipo": "texto",
                "Mensaje": traemenu(JData_Plugins)
            }]
        if Encontro ==0:
            return [{
                "Tipo": "texto",
                "Mensaje": traemenu(JData_Plugins)
            }]
    except Exception as e:
        return [{
                "Tipo": "texto",
                "Mensaje": traemenu(JData_Plugins)
            }]