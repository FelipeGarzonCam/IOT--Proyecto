from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # permite peticiones desde Streamlit

ultimo = {
    "ir": {"100": 0, "200": 0, "1000": 0},
    "monedas_totales": 0,
    "ultrasonido": 0.0,
    "velostat": [0, 0, 0],
    "carrito": "",
    "timestamp": 0
}

@app.route('/sensores', methods=['POST'])
def recibir():
    global ultimo
    data = request.get_json(force=True)
    ultimo = data
    print("-> Datos recibidos:", data)
    return jsonify(ok=True)

@app.route('/ultimos', methods=['GET'])
def ultimos():
    return jsonify(ultimo)

if __name__ == "__main__":
    print(">>> SERVER FLASK VIVO: arrancando en http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)