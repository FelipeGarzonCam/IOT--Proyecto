#include <ESP8266WiFi.h>

// ---------- Wi-Fi ----------
const char* ssid     = "Edge50FusiondeFelipe";
const char* password = "Hola1345";
WiFiServer server(8266);

// ---------- Pines Puente-H ----------
#define M_A1 5   // D1
#define M_A2 4   // D2
#define M_B1 0   // D3
#define M_B2 2   // D4

WiFiClient client;

void detener() {
  digitalWrite(M_A1, LOW); digitalWrite(M_A2, LOW);
  digitalWrite(M_B1, LOW); digitalWrite(M_B2, LOW);
}
void avanzar() {
  digitalWrite(M_A1, HIGH); digitalWrite(M_A2, LOW);
  digitalWrite(M_B1, HIGH); digitalWrite(M_B2, LOW);
}
void retroceder() {
  digitalWrite(M_A1, LOW); digitalWrite(M_A2, HIGH);
  digitalWrite(M_B1, LOW); digitalWrite(M_B2, HIGH);
}
void giroDerecha() {
  digitalWrite(M_A1, HIGH); digitalWrite(M_A2, LOW);
  digitalWrite(M_B1, LOW); digitalWrite(M_B2, HIGH);
}

void setup() {
  Serial.begin(115200);
  pinMode(M_A1, OUTPUT); pinMode(M_A2, OUTPUT);
  pinMode(M_B1, OUTPUT); pinMode(M_B2, OUTPUT);
  detener();

  WiFi.begin(ssid, password);
  Serial.print("Conectando a "); Serial.println(ssid);
  while (WiFi.status() != WL_CONNECTED) {
    delay(300); Serial.print('.');
  }
  Serial.println();
  Serial.printf("Conectado — IP: %s\n", WiFi.localIP().toString().c_str());
  server.begin();
  Serial.println("Servidor TCP iniciado en puerto 8266");
}

void loop() {
  if (server.hasClient()) {
    if (client) client.stop();
    client = server.available();
    Serial.println("🟢 Cliente conectado");
  }

  if (client && client.connected()) {
    String cmd = client.readStringUntil('\n');
    cmd.trim();
    if (cmd.length()) {
      Serial.println("⟶ Recibido: " + cmd);
      if (cmd == "100") {
        Serial.println("→ Avanzar");
        avanzar(); delay(5000); detener();
      }
      else if (cmd == "200") {
        Serial.println("→ Retroceder");
        retroceder(); delay(5000); detener();
      }
      else if (cmd == "1000") {
        Serial.println("→ Giro derecha");
        giroDerecha(); delay(5000); detener();
      }
      else {
        Serial.println("⚠ Comando desconocido: " + cmd);
      }
    }
  }

  if (client && !client.connected()) {
    Serial.println("Cliente desconectado");
    client.stop();
  }

  delay(1);
}
