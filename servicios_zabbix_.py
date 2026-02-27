# V3.0 - Metodología Unificada + Estilos Premium Restaurados + Botón MENU
import requests
import html
import shlex
import time
import logging
import sys

# ==============================================================================
# 0. CONFIGURACIÓN DE LOGS (DINÁMICO)
# ==============================================================================
logger = logging.getLogger("servicios_zabbix")
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter('%(asctime)s | %(name)s | %(levelname)-7s | %(message)s'))
logger.addHandler(console_handler)

MAPEO_LOGS = {"DEBUG": logging.DEBUG, "INFO": logging.INFO, "WARN": logging.WARNING, "ERROR": logging.ERROR}


def loguea(linea, nivel="info"):
    nivel = nivel.lower()
    if nivel == "error":
        logger.error(linea)
    elif nivel in ["warn", "warning"]:
        logger.warning(linea)
    elif nivel == "debug":
        logger.debug(linea)
    else:
        logger.info(linea)


# ==============================================================================
# 1. CONFIGURACIÓN Y CONSTANTES
# ==============================================================================
VERIFY_SSL = False
HOSTNAME = "Firewall_Perimetral"
ENLACES_GROUPID = "112"
AP_SEARCH_NAME = "Clientes WiFi"

WAN_ITEMS = [
    {"group": "Claro", "label": "Disponibilidad DNS Público", "key": "icmpping[8.8.4.4]", "type": "avail"},
    {"group": "Claro", "label": "Disponibilidad Gateway", "key": "icmpping[190.221.179.194]", "type": "avail"},
    {"group": "Claro", "label": "Latencia DNS Público", "key": "icmppingsec[8.8.4.4]", "type": "lat"},
    {"group": "Claro", "label": "Latencia Gateway", "key": "icmppingsec[190.221.179.194]", "type": "lat"},
    {"group": "Telecom", "label": "Disponibilidad DNS Público", "key": "icmpping[8.8.8.8]", "type": "avail"},
    {"group": "Telecom", "label": "Disponibilidad Gateway", "key": "icmpping[186.125.135.162]", "type": "avail"},
    {"group": "Telecom", "label": "Latencia DNS Público", "key": "icmppingsec[8.8.8.8]", "type": "lat"},
    {"group": "Telecom", "label": "Latencia Gateway", "key": "icmppingsec[186.125.135.162]", "type": "lat"},
]


# ==============================================================================
# 2. CORE ZABBIX API
# ==============================================================================

def _zabbix_call(method, params, z_url, z_token):
    api_url = f"{z_url.rstrip('/')}/api_jsonrpc.php"
    payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
    headers = {"Content-Type": "application/json-rpc", "Authorization": f"Bearer {z_token}"}
    start_api = time.time()
    try:
        resp = requests.post(api_url, json=payload, headers=headers, timeout=12, verify=VERIFY_SSL)
        resp.raise_for_status()
        loguea(f"API {method} respondió en {time.time() - start_api:.3f}s", "debug")
        data = resp.json()
        if "error" in data:
            err = data['error'].get('data', data['error'].get('message'))
            loguea(f"Zabbix RECHAZÓ {method}: {err}", "error")
            raise RuntimeError(f"Zabbix Error: {err}")
        return data.get("result")
    except Exception as e:
        loguea(f"CRÍTICO: Fallo de red en {method} -> {str(e)}", "error")
        raise


# ==============================================================================
# 3. UTILIDADES Y FORMATEO
# ==============================================================================

def _parse_args(message_text):
    if not message_text: return "", []
    try:
        parts = shlex.split(message_text.strip())
    except:
        parts = message_text.strip().split()
    cmd = parts[0] if parts else ""
    args = [p.upper() for p in parts[1:]]
    return cmd, args


def _fmt_avail(v): return "🟢 UP" if str(v) == "1" else "🔴 DOWN"


def _fmt_latency_ms(v):
    try:
        return f"{float(v) * 1000.0:.2f} ms"
    except:
        return "N/A"


def _get_ts_label(clocks):
    if not clocks: return "<code>Actualizado: N/A</code>"
    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(max(clocks)))
    return f"<code>Actualizado: {ts}</code>"


# ==============================================================================
# 4. CONSTRUCCIÓN DE REPORTES (ESTILOS RESTAURADOS)
# ==============================================================================

def _get_alertas_criticas_html(z_url, z_token):
    problems = _zabbix_call("trigger.get",
                            {"output": ["priority"], "filter": {"value": 1}, "monitored": True, "only_true": True},
                            z_url, z_token)
    p_counts = {5: 0, 4: 0, 3: 0}
    for p in problems:
        pri = int(p.get("priority", 0))
        if pri in p_counts: p_counts[pri] += 1
    icon = "🟢"
    if p_counts[5] > 0 or p_counts[4] > 0:
        icon = "🔴"
    elif p_counts[3] > 3:
        icon = "🟡"
    return (f"{icon} <b>ALERTAS CRÍTICAS</b>\n"
            f"—————————————\n"
            f"🆘 Desastres: <b>{p_counts[5]}</b>\n"
            f"🔥 Alta Prioridad: <b>{p_counts[4]}</b>\n"
            f"⚠️ Advertencias: <b>{p_counts[3]}</b>")


def _build_wan_html(z_url, z_token):
    keys = [it["key"] for it in WAN_ITEMS]
    res = _zabbix_call("item.get",
                       {"output": ["key_", "lastvalue", "lastclock"], "host": HOSTNAME, "filter": {"key_": keys}},
                       z_url, z_token)
    data_map = {item["key_"]: item for item in res};
    clocks, by_group = [], {}
    for it in WAN_ITEMS:
        item_data = data_map.get(it["key"], {});
        v, c = item_data.get("lastvalue", "0"), item_data.get("lastclock")
        by_group.setdefault(it["group"], []);
        res_fmt = _fmt_avail(v) if it["type"] == "avail" else _fmt_latency_ms(v)
        by_group[it["group"]].append(f"• <b>{it['label']}</b>: {res_fmt}")
        if c: clocks.append(int(c))
    lineas = ["<b>🌐 Status WAN</b>", f"Host: <b>{HOSTNAME}</b>", "—————————————"]
    for grp in ["Claro", "Telecom"]:
        if grp in by_group: lineas.append(f"<b>{grp}</b>"); lineas.extend(by_group[grp]); lineas.append("")
    lineas.append(_get_ts_label(clocks))
    return "\n".join(lineas)


def _build_ap_html(z_url, z_token):
    res = _zabbix_call("item.get", {"output": ["name", "lastvalue", "lastclock"], "host": HOSTNAME,
                                    "search": {"name": AP_SEARCH_NAME}}, z_url, z_token)
    caidos, clocks = [], []
    for item in res:
        if item.get("lastclock"): clocks.append(int(item["lastclock"]))
        if int(float(item.get("lastvalue", 0))) == 0:
            name = item.get("name", "").replace(f":{AP_SEARCH_NAME}", "").strip()
            caidos.append(name)
    lineas = ["<b>📶 Access Point</b>", "—————————————"]
    if not caidos:
        lineas.append("🟢 Todos los AP operativos.")
    else:
        lineas[0] = "<b>📶 APs Caídos</b>"; [lineas.append(f"🔴 {html.escape(ap)}") for ap in caidos]
    lineas.append(f"\n{_get_ts_label(clocks)}")
    return "\n".join(lineas)


def _build_enlaces_html(z_url, z_token):
    items = _zabbix_call("item.get", {"output": ["lastvalue", "lastclock"], "groupids": [ENLACES_GROUPID],
                                      "filter": {"key_": ["icmpping"]}, "selectHosts": ["name", "status"]}, z_url,
                         z_token)
    lineas, clocks = ["<b>🔗 Reporte de Enlaces</b>", "—————————————"], [];
    ok, down, disabled = 0, 0, 0
    for it in items:
        host = it["hosts"][0];
        icmp = int(float(it.get("lastvalue", 0)))
        if it.get("lastclock"): clocks.append(int(it["lastclock"]))
        if int(host["status"]) == 0:
            icon = "🟢" if icmp == 1 else "🔴";
            ok += (1 if icmp == 1 else 0);
            down += (1 if icmp == 0 else 0)
            lineas.append(f"{icon} {html.escape(host['name'])}")
        else:
            disabled += 1; lineas.append(f"⚫ {html.escape(host['name'])} <code>(deshabilitado)</code>")
    lineas.append(f"\n<b>Resumen:</b> {ok} BIEN | {down} CAÍDOS | {disabled} DESHABILITADOS")
    lineas.append(_get_ts_label(clocks))
    return "\n".join(lineas)


def _build_salud_html(z_url, z_token):
    alertas = _get_alertas_criticas_html(z_url, z_token)
    # Reutilizamos los builders para chequear presencia de rojos
    status_wan = "🔴" if "🔴" in _build_wan_html(z_url, z_token) else "🟢"
    status_ap = "🔴" if "🔴" in _build_ap_html(z_url, z_token) else "🟢"
    status_en = "🔴" if "🔴" in _build_enlaces_html(z_url, z_token) else "🟢"
    return (f"{alertas}\n\n"
            f"<b>🔍 ESTADO POR SECTOR</b>\n"
            f"• WAN: {status_wan}\n"
            f"• AP: {status_ap}\n"
            f"• ENLACES: {status_en}")


# ==============================================================================
# 5. UI Y BOTONES (METODOLOGÍA UNIFICADA)
# ==============================================================================

def _build_keyboard_full(base):
    return {"inline_keyboard": [
        [{"text": "🏥 SALUD GENERAL", "callback_data": f"{base} SALUD"}],
        [{"text": "🌐 WAN", "callback_data": f"{base} WAN"}, {"text": "📶 AP", "callback_data": f"{base} AP"}],
        [{"text": "🔗 ENLACES", "callback_data": f"{base} ENLACES"}],
        [{"text": "🏠 MENU", "callback_data": f"{base} MENU"}]
    ]}


def _build_keyboard_footer(cmd_original, base):
    return {"inline_keyboard": [[
        {"text": "🔄 Repetir comando", "callback_data": cmd_original},
        {"text": "🏠 MENU", "callback_data": f"{base} MENU"}
    ]]}


# ==============================================================================
# 6. ENTRYPOINT PRINCIPAL
# ==============================================================================

def Principal(message_data, JData_Plugins):
    if not JData_Plugins: return [{"Tipo": "texto", "Mensaje": "⚠️ Error: Configuración ausente."}]

    config = JData_Plugins[0]
    # Configuración de logs dinámica
    nivel_config = config.get("LOG_LEVEL", "INFO").upper()
    logger.setLevel(MAPEO_LOGS.get(nivel_config, logging.INFO))
    console_handler.setLevel(MAPEO_LOGS.get(nivel_config, logging.INFO))

    usr = message_data.get("Usuario", "Anon");
    msg = message_data.get("Mensaje", "N/A")
    loguea(f"REQ de {usr}: {msg}", "info")

    start_total = time.time();
    z_url, z_token = config.get("ZABBIX_URL"), config.get("ZABBIX_TOKEN")
    cmd_base, args = _parse_args(msg)

    # A. MENU O SIN ARGUMENTOS
    if not args or args[0] == "MENU":
        return [{
            "Tipo": "reply_markup",
            "Mensaje": {
                "txt_mensaje": "👋 <b>Monitor de Infraestructura</b>\nSelecciona una opción:",
                "reply_markup": _build_keyboard_full(cmd_base)
            }
        }]

    try:
        opcion = args[0]
        # B. PROCESAR REPORTE SEGÚN OPCIÓN
        if opcion == "SALUD":
            res = _build_salud_html(z_url, z_token)
            markup = _build_keyboard_full(cmd_base)
        elif opcion == "WAN":
            res = _build_wan_html(z_url, z_token)
            markup = _build_keyboard_footer(msg, cmd_base)
        elif opcion == "AP":
            res = _build_ap_html(z_url, z_token)
            markup = _build_keyboard_footer(msg, cmd_base)
        elif opcion == "ENLACES":
            res = _build_enlaces_html(z_url, z_token)
            markup = _build_keyboard_footer(msg, cmd_base)
        else:
            return [{"Tipo": "texto", "Mensaje": "⚠️ Opción no válida."}]

        elapsed = time.time() - start_total
        loguea(f"SUCCESS: {opcion} en {elapsed:.2f}s", "info")

        # C. CUERPO FINAL UNIFICADO (Reporte + Instrucción + Tiempos + Botones)
        final_html = (
            f"{res}\n\n"
            f"<code>Respuesta en {elapsed:.2f}s</code>"
        )

        return [{
            "Tipo": "reply_markup",
            "Mensaje": {
                "txt_mensaje": final_html,
                "reply_markup": markup
            }
        }]

    except Exception as e:
        loguea(f"ERROR Crítico: {str(e)}", "error")
        return [{"Tipo": "texto", "Mensaje": f"⚠️ <b>Error Zabbix:</b>\n{html.escape(str(e))}"}]