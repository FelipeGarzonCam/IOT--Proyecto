from machine import ADC, Pin
from time import sleep
from hx711 import HX711          # copia hx711.py al Pico

# ---------- Sensores 0-2 (ADC interno) ----------
ADC_PINS = [26, 27, 28]          # GP26-28  = ADC0-2
R_FIXED  = 20000                 # Ω en cada divisor

# ← Sustituye M y B tras tu propia calibración
M = [0.00516, 0.00516, 0.00516]  # g/Ω  (pendiente)
B = [-70.0,   -70.0,   -70.0]    # g    (offset)

adcs = [ADC(p) for p in ADC_PINS]

def read_voltage(adc):
    return adc.read_u16() * 3.3 / 65535

def velostat_resistance(v):
    return (3.3 - v) * R_FIXED / v

# ---------- Sensor 3 (Velostat #4 + HX711) ----------
DT_PIN  = 16                      # GP2 → DT
SCK_PIN = 17                      # GP3 → SCK
hx = HX711(d_out=Pin(DT_PIN), pd_sck=Pin(SCK_PIN))
hx.set_gain(128)                 # Ganancia por defecto

# Coeficientes de calibración del canal HX711 (ajústalos con pesas)
M3 = 0.00210         # g por cuenta
B3 = -10.0           # g offset

def peso_hx(n=5):
    """Promedia n lecturas del HX711 y aplica la curva M3,B3."""
    total = 0
    for _ in range(n):
        total += hx.read()
    raw = total / n
    return M3 * raw + B3

# ---------- Función de tara general ----------
def tare(n=60):
    global B, B3
    # Tara sensores 0-2
    for idx, adc in enumerate(adcs):
        acc = 0
        for _ in range(n):
            acc += velostat_resistance(read_voltage(adc))
            sleep(0.005)
        r0 = acc / n
        B[idx] = -M[idx] * r0
    # Tara sensor 3
    raw0 = sum(hx.read() for _ in range(n)) / n
    B3 = -M3 * raw0
    print("Tara OK  ->  B =", ["%.1f" % b for b in B], "  B3 = %.1f" % B3)

# --- Ejecuta tara automática al arrancar (puedes comentar) ---
tare()

# ---------- Bucle principal ----------
while True:
    pesos = []
    for idx, adc in enumerate(adcs):
        v    = read_voltage(adc)
        r    = velostat_resistance(v)
        p    = M[idx] * r + B[idx]
        pesos.append(p)
        print("S%u  V=%.3f V  R=%6.0f Ω  P=%6.1f g" % (idx, v, r, p))
    # Sensor 3
    p3 = peso_hx()
    pesos.append(p3)
    print("S3  HX711  P=%6.1f g" % p3)
    print("-" * 60)
    sleep(1)