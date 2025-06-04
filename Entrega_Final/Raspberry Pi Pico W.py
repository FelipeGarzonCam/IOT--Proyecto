from machine import Pin, ADC, time_pulse_us
from time import sleep
import network, socket, urequests, ujson, time as utime

# -------- WI-FI y Endpoints --------
SSID      = 'Edge50FusiondeFelipe'
PASSWORD  = 'Hola1345'
HOST_NODE = '192.168.247.110'
PORT_NODE = 8266
URL_PC    = 'http://192.168.247.116:5000/sensores'

# -------- Pines GPIO --------
TRIG_PIN, ECHO_PIN = 3, 2
coin_sensors = {
    "$100":  Pin(5, Pin.IN, Pin.PULL_DOWN),
    "$200":  Pin(6, Pin.IN, Pin.PULL_DOWN),
    "$1000": Pin(7, Pin.IN, Pin.PULL_DOWN),
}
ADC_PINS = [26, 27, 28]

# -------- Constantes ultrasónico --------
UMBRAL_C = 3.65
DELTA    = 0.20
MIN_US   = UMBRAL_C - DELTA  # 2.45 cm
MAX_US   = UMBRAL_C + DELTA  # 2.85 cm

# -------- Coeficientes Velostat --------
R_FIXED = 20000
M       = [0.00516]*3
B       = [-70.0]*3

# -------- Instancias hardware --------
trig = Pin(TRIG_PIN, Pin.OUT)
echo = Pin(ECHO_PIN, Pin.IN)
adcs = [ADC(p) for p in ADC_PINS]

# -------- Funciones auxiliares --------
def conectar_wifi():
    wlan = network.WLAN(network.STA_IF); wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(SSID, PASSWORD)
        for _ in range(15):
            if wlan.isconnected(): break
            sleep(1)
    print("Wi-Fi:", wlan.ifconfig() if wlan.isconnected() else "⚠ sin conexión")
    return wlan.isconnected()

def medir_distancia():
    trig.low(); sleep(0.002)
    trig.high(); sleep(0.00001)
    trig.low()
    dur = time_pulse_us(echo, 1, 12000)
    return None if dur < 0 else (dur/2)/29.1

def read_voltage(adc):
    return adc.read_u16() * 3.3 / 65535

def velostat_resistance(v):
    return (3.3 - v) * R_FIXED / v

def tare(n=60):
    global B
    for i, adc in enumerate(adcs):
        acc = 0
        for _ in range(n):
            acc += velostat_resistance(read_voltage(adc))
            sleep(0.01)
        r0 = acc / n
        B[i] = -M[i] * r0
    print("Tara aplicada. Offsets B =", ["%.1f" % b for b in B])

def enviar_comando_node(cmd):
    try:
        addr = socket.getaddrinfo(HOST_NODE, PORT_NODE)[0][-1]
        s = socket.socket()
        s.connect(addr)
        s.send((cmd + "\n").encode())
        s.close()
        print(f"[IR] Enviado comando: {cmd}")
    except:
        print(f"[ERROR] No se pudo enviar '{cmd}'")

def enviar_a_pc(paquete):
    try:
        r = urequests.post(URL_PC,
            data=ujson.dumps(paquete),
            headers={'Content-Type':'application/json'})
        r.close()
    except:
        print("[ERROR] Envío a PC falló")

# -------- Estados iniciales --------
paso_monedas_total = 0
coin_counts        = {d:0 for d in coin_sensors}
prev_ir_state      = {}
prev_us_dentro     = False

for d, sen in coin_sensors.items():
    prev_ir_state[d] = sen.value()
d0 = medir_distancia()
prev_us_dentro = (d0 is not None) and (MIN_US <= d0 <= MAX_US)

# -------- Arranque --------
tare()
if not conectar_wifi():
    raise RuntimeError("No se pudo conectar al Wi-Fi")
print("Sistema iniciado. (Ctrl+C para detener)")

try:
    while True:
        # — Ultrasonido (flanco fuera→dentro) —
        d = medir_distancia()
        dentro = (d is not None) and (MIN_US <= d <= MAX_US)
        if dentro and not prev_us_dentro:
            paso_monedas_total += 1
        prev_us_dentro = dentro
        print(f"Ultrasonido: {d if d is not None else '—'} cm | Tot pasos: {paso_monedas_total}")

        # — Sensores IR (flanco 0→1, reset a 0 al llegar a 10) —
        for denom, sensor in coin_sensors.items():
            curr = sensor.value()
            if curr == 1 and prev_ir_state[denom] == 0:
                coin_counts[denom] += 1
                print(f"[IR] {denom} detectada → {coin_counts[denom]}")
                sleep(0.05)  # debounce
                if coin_counts[denom] == 10:
                    enviar_comando_node(denom.strip("$"))
                    coin_counts[denom] = 0
            prev_ir_state[denom] = curr
        print("Conteo IR:", " ".join(f"{d}:{c}" for d,c in coin_counts.items()))

        # — Galgas Velostat —
        pesos = []
        for i, adc in enumerate(adcs):
            v = read_voltage(adc); r = velostat_resistance(v)
            peso = M[i]*r + B[i]
            pesos.append(round(peso,1))
            print(f"S{i}: V={v:.3f} V | R={r:6.0f} Ω | Peso≈{peso:6.1f} g")
        print("-"*50)

        # — Envío JSON al PC —
        paquete = {
            "ir":               {d.strip("$"): coin_counts[d] for d in coin_counts},
            "monedas_totales":  paso_monedas_total,
            "ultrasonido":      d or 0,
            "velostat":         pesos,
            "timestamp":        utime.time()
        }
        enviar_a_pc(paquete)

        sleep(0.1)

except KeyboardInterrupt:
    print("Detenido por usuario.")
