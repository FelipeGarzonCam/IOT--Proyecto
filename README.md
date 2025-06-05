## Segunda Entrega

En la segunda entrega se usó:

- Un sensor ultrasónico que detecta el paso de todas las monedas antes de ser separadas por valor; dicho sensor se refleja en la variable `Pasos Totales`.
- Tres sensores infrarrojos que cuentan la cantidad de monedas de cada denominación: `$1000`, `$200` y `$100`. Ubicados de izquierda a derecha en el montaje.
- Finalmente, tres sensores tipo galga fabricados con velostat y cable UTP, que utilizan los tres pines ADC de la Raspberry Pi Pico. Cada sensor está construido con tres capas de velostat y dos cables entre ellas, y se ubica bajo las cajas que almacenan las monedas ya separadas.
--- 
## Entrega Final
# Proyecto IoT: Conteo de Monedas y Control de Carrito

Este proyecto integra una **Raspberry Pi Pico** con sensores de infrarrojos, y tres Pseudo galgas fabricadas con velostat y un sensor ultrasónico, y un **NodeMCU ESP8266** conectado a un carrito. La Pico se encarga de:

- **Contar monedas** según su denominación (IR \$100, \$200, \$1000).  
- **Calcular el total de monedas** que pasan por un punto usando el sensor ultrasónico.
- **Calcula el peso de las monedas** Que caen en las cajitas ya separadas por denominacion, el peso se calcula segun la resistencia dada por los sensores tipo galga
- **Enviar datos** a un servidor web (Flask/Overleaf) y, simultáneamente,  
- **Enviar comandos TCP al NodeMCU** (“100”, “200” ó “1000”) cuando cada denominación alcanza 10 unidades.

El NodeMCU recibe esos tres posibles comandos y, según cuál llegue, realiza un movimiento distinto en el carrito (avanzar, retroceder o girar a la derecha).

---

## 🔧 Componentes de Hardware

1. **Raspberry Pi Pico W**  
   - Se programa en MicroPython.  
   - Tiene pines digitales para sensores IR y pines ADC para galgas Velostat.  
   - Convierte lecturas de sensores a valores numéricos.

2. **Sensor Ultrasónico (HC-SR04)**  
   - Mide distancia en centímetros.  
   - Genera un pulso en “Trig” y lee el eco en “Echo” (mediante un divisor de tensión para proteger 3.3 V).  
   - Sirve para calcular cuántas monedas han pasado por el eje: solo se cuenta si la distancia entra en el rango 2.45 cm – 2.85 cm, y detecta el instante en que ese rango se atraviesa.

3. **Tres Sensores Infrarrojos (p. ej. TCRT5000, CNY70, etc.)**  
   - Cada uno está alineado para detectar una sola denominación de moneda:  
     - Sensor IR “\$100”  
     - Sensor IR “\$200”  
     - Sensor IR “\$1000”  
   - Cuando cada sensor cambia de “no detecta” a “detecta” (flanco 0→1), suma 1 al contador de esa denominación.  
   - Cuando el contador llega a 10, la Pico envía por TCP el valor “100”, “200” o “1000” según corresponda, y reinicia ese contador a 0.

4. **Galgas Velostat (Opcional, para medición de peso)**  
   - Cada galga forma un divisor de tensión con una resistencia fija (20 kΩ).  
   - Se lee por los pines ADC (GP26, GP27, GP28).  
   - Tras una tara inicial, convierte la tensión medida a resistencia y luego calcula peso aproximado usando coeficientes de calibración. Esto permite saber el peso de una pila de monedas o un objeto que repose sobre la galga.

5. **NodeMCU ESP8266**  
   - Actúa como servidor TCP en el puerto 8266.  
   - Recibe uno de tres comandos:  
     - **“100”**  → Avanzar el carrito  
     - **“200”**  → Retroceder el carrito  
     - **“1000”** → Girar a la derecha  
   - Cada movimiento dura aproximadamente 5 segundos mediante la activación de un puente H conectado a cuatro pines digitales.

6. **Puente H (L298N, L293D, etc.)**  
   - Conecta cuatro señales del NodeMCU a dos motores del carrito.  
   - Al recibir “100”, “200” o “1000”, se activan las combinaciones de pines para avanzar, retroceder o girar.

7. **Divisor de Tensión para Echo**  
   - El pin Echo del HC-SR04 entrega ~5 V.  
   - Usar dos resistencias (1 kΩ y 2 kΩ) para bajar a ~3.3 V antes de llegar a GP2 de la Pico.

---

## 🔌 Diagrama de Conexiones
           ┌────────────────────────────────┐
           │   HC-SR04 (Ultrasónico)        │
           │  Vcc→3.3V   GND→GND            │
           │  Trig→GP3   Echo→R1→R2→GP2     │
           └────────────────────────────────┘

           ┌────────────────────────────────┐
           │    Sensores IR (TCRT5000)      │
           │  $100→GP5   $200→GP6   $1000→GP7 │
           │  (todos con pull-down interno) │
           └────────────────────────────────┘

           ┌──────────────────────────────────┐
           │   Galgas Velostat (Opcional)     │
           │  GP26→ADC0, GP27→ADC1, GP28→ADC2 │
           │  R_fixed=20 kΩ + Velostat        │
           └──────────────────────────────────┘

           ┌────────────────────────────────┐
           │ NodeMCU ESP8266 (Carrito)      │
           │  D1(G5)→M_A1, D2(G4)→M_A2      │
           │  D3(G0)→M_B1, D4(G2)→M_B2      │
           └────────────────────────────────┘

## 📐🔗 Flujo de Información

1. **Conteo de Monedas (IR):**  
   - Cada vez que un sensor IR detecta una moneda (flanco 0→1), se incrementa su contador interno.  
   - Al llegar a 10 monedas de esa denominación, se envía inmediatamente, por **socket TCP**, un mensaje de texto (“100”, “200” o “1000”) al NodeMCU y se reinicia ese contador a 0.

2. **Conteo Total de Monedas (Ultrasónico):**  
   - El sensor ultrasónico mide continuamente la distancia.  
   - Cada vez que un objeto (monedas en fila) atraviesa el rango 2.45 cm – 2.85 cm, se detecta el flanco “fuera→dentro” y se incrementa el contador global `monedas_totales`.

3. **Envío de Datos en Tiempo Real (HTTP):**  
   - Cada ciclo (aprox. cada 0.1 s), la Pico agrupa en un JSON:  
     - Conteos IR actuales por denominación (100, 200, 1000).  
     - Contador total de ultrasonido.  
     - Lecturas de Velostat (peso) en cada galga.  
     - “Timestamp” Unix.  
   - Este JSON se envía por **HTTP POST** al servidor Flask/Overleaf.

4. **NodeMCU ESP8266 (TCP → Carrito):**  
   - Queda escuchando en el puerto 8266.  
   - Cuando recibe una línea terminada en `\n` igual a “100”, “200” o “1000”, ejecuta el movimiento programado (avanzar, retroceder o girar).  
   - Cada movimiento dura 2 s y luego detiene los motores.

5. **Servidor HTTP (Flask/Overleaf):**  
   - Recibe en `POST /sensores` el JSON desde la Pico.  
   - Guarda la última lectura en memoria.  
   - Permite consultar en `GET /ultimos` el JSON actual para visualización en un dashboard web. 
   
```json
{
  "ir": { "100": <cnt100>, "200": <cnt200>, "1000": <cnt1000> },
  "monedas_totales": <paso_monedas_total>,
  "ultrasonido": <distancia_cm|0>,
  "velostat": [<peso0>, <peso1>, <peso2>],
  "timestamp": <unix_time>
}
```


---

## 🔄 Resumen de Funcionamiento

1. **Inicialización**  
   - La Pico hace una **tara** de las galgas para calibración.  
   - Conecta al Wi-Fi y al servidor HTTP.  
   - Configura lectura de sensores IR y ultrasónico.  

2. **Bucle Principal (cada 0.1 s)**  
   - **Ultrasonido**:  
     - Mide distancia; si cae en [2.45 cm, 2.85 cm] y antes estaba fuera, suma 1 a `monedas_totales`.  
   - **IR**:  
     - Para cada sensor IR, detecta cambio de 0→1.  
     - Si el contador llega a 10, envía comando TCP al NodeMCU (“100”, “200” o “1000”) y reinicia el contador.  
   - **Velostat (Opcional)**:  
     - Lee voltaje de cada ADC, convierte a resistencia y luego a peso aproximado.  
   - **HTTP → Servidor**:  
     - Crea JSON con conteos IR, total ultrasónico, lista de pesos y timestamp.  
     - Envía el JSON por POST a `http://<IP>:5000/sensores`.  

3. **NodeMCU (Servidor TCP)**  
   - Acepta clientes y, para cada línea recibida:  
     - Si es “100”, mueve el carrito hacia adelante 2 s.  
     - Si es “200”, mueve el carrito hacia atrás 2 s.  
     - Si es “1000”, gira el carrito a la derecha 2 s.  
     - Luego detiene los motores.  

4. **Visualización**  
   - El servidor Flask/Overleaf mantiene la última lectura JSON.  
   - (Opcional) Una interfaz Streamlit puede hacer `GET /ultimos` cada segundos y mostrar métricas en tiempo real, además de TTS o chat.

---

## 💻 Interfaz Streamlit

La **interfaz Streamlit** se conecta al endpoint `/ultimos` para obtener el último JSON que envía la Pico. Cada vez que recibe datos:

- **Actualiza métricas** en pantalla:  
  - Total de monedas contadas por el ultrasónico.  
  - Conteo de monedas por IR para \$100, \$200 y \$1000.  
  - Pesos calculados por cada galga Velostat.  

- **Muestra el JSON completo** en un panel que el usuario puede expandir.  

- **Detecta cambios en el campo “carrito”** del JSON. Si cambia, reproduce un mensaje de voz (TTS) anunciando la acción (por ejemplo: “Carrito salió por 100 pesos”).  

- **Permite al usuario preguntar por voz** (grabando directamente con el micrófono del navegador). La grabación se transcribe con SpeechRecognition, luego la consulta se envía al modelo (DeepSeek) junto con los datos en vivo, y la respuesta se reproduce también con TTS.

- **Ofrece un chat textual opcional**, donde el usuario escribe su pregunta y recibe respuesta hablada y escrita.

- Se **refresca automáticamente** cada 2 segundos para mostrar información en tiempo real y reproducir nuevos mensajes TTS.
