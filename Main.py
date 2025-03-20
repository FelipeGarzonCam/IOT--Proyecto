import machine
import utime
from hx711 import HX711  # Asegúrate de tener la versión de hx711.py adaptada para MicroPython

# Configuración del sensor infrarrojo (conectado al pin GP26)
ir_sensor = machine.ADC(26)

# Configuración del sensor ultrasónico:
# TRIG conectado a GP14 y ECHO a GP15
trig = machine.Pin(14, machine.Pin.OUT)
echo = machine.Pin(15, machine.Pin.IN)

# Configuración del módulo HX711 para la celda de carga (sensor de presión)
# Se usan GP16 para DT y GP17 para SCK
hx = HX711(machine.Pin(16), machine.Pin(17), 128)
utime.sleep(1)  # Espera para que el sensor se estabilice
hx.tare()       # Ajusta el cero de la celda de carga

# Factor de calibración (valor de ejemplo; calibra usando un peso conocido)
CALIBRATION_FACTOR = 1000

def measure_ultrasonic():
    # Envía pulso de disparo al sensor ultrasónico
    trig.value(0)
    utime.sleep_us(2)
    trig.value(1)
    utime.sleep_us(10)
    trig.value(0)
    
    try:
        duration = machine.time_pulse_us(echo, 1, 30000)
    except OSError:
        duration = -1  # Error de lectura
    if duration < 0:
        return -1
    # Calcula la distancia en centímetros (velocidad del sonido ~0.0343 cm/µs)
    distance_cm = (duration * 0.0343) / 2
    return distance_cm

def read_pressure():
    # Lee el valor bruto del HX711 y lo convierte usando el factor de calibración
    raw = hx.read()
    pressure = raw / CALIBRATION_FACTOR
    return pressure

# Verifica si ya existe "data.csv"; si no, crea el archivo y escribe la cabecera.
try:
    with open("data.csv", "r") as f:
        pass  # El archivo existe, no hacemos nada.
except OSError:
    with open("data.csv", "w") as f:
        f.write("Timestamp (seg),Sensor Infrarrojo (ADC),Sensor Ultrasónico (cm),Sensor de Presión (valor calibrado)\n")

while True:
    timestamp = utime.time()            # Tiempo actual (segundos)
    ir_value = ir_sensor.read_u16()      # Valor ADC del sensor infrarrojo (16 bits)
    ultrasonic_distance = measure_ultrasonic()  # Distancia en cm del sensor ultrasónico
    pressure_value = read_pressure()    # Valor calibrado del sensor de presión
    
    # Crea una línea en formato CSV
    line = "{},{},{},{}\n".format(timestamp, ir_value, ultrasonic_distance, pressure_value)
    
    # Imprime la línea por el puerto serie (útil para depuración)
    print(line, end="")
    
    # Abre el archivo "data.csv" en modo append y escribe la línea
    with open("data.csv", "a") as f:
        f.write(line)
    
    utime.sleep(1)
