import os
import json
import base64
import secrets
import hashlib
import requests
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, session

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", secrets.token_hex(32))

# ==================== CONFIGURACIÓN ====================
CUTY_API_KEY = os.environ.get("CUTY_API_KEY")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_OWNER = os.environ.get("GITHUB_OWNER")
GITHUB_REPO = os.environ.get("GITHUB_REPO")
GITHUB_PATH = os.environ.get("GITHUB_PATH", "main/users.json")
CUTY_API_URL = "https://cuty.io/api"

# ==================== FUNCIONES AUXILIARES ====================

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generar_key_temporal():
    usuario = "DEX_" + secrets.token_hex(3).upper()
    password = secrets.token_hex(4).upper()
    ahora = datetime.now()
    expira = ahora + timedelta(hours=1)
    return {
        "usuario": usuario,
        "password": password,
        "creado": ahora.isoformat(),
        "expira_en": expira.isoformat(),
        "temporal": True
    }

def actualizar_users_json(key_data):
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{GITHUB_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return False, "No se pudo leer users.json en GitHub"
    sha = response.json()["sha"]
    contenido_actual = json.loads(base64.b64decode(response.json()["content"]).decode())
    if "users" not in contenido_actual:
        contenido_actual["users"] = {}
    contenido_actual["users"][key_data["usuario"]] = {
        "password": hash_password(key_data["password"]),
        "role": "user",
        "device_id": "",
        "device_locked": False,
        "created": key_data["creado"],
        "expira_en": key_data["expira_en"],
        "temporal": True
    }
    nuevo_contenido = base64.b64encode(
        json.dumps(contenido_actual, indent=2).encode()
    ).decode()
    payload = {
        "message": f"Key temporal generada: {key_data['usuario']}",
        "content": nuevo_contenido,
        "sha": sha
    }
    response = requests.put(url, json=payload, headers=headers)
    if response.status_code in [200, 201]:
        return True, key_data
    return False, response.json().get("message", "Error desconocido")

def generar_enlace_cuty(destino):
    params = {"api": CUTY_API_KEY, "url": destino}
    response = requests.get(CUTY_API_URL, params=params)
    if response.status_code == 200:
        data = response.json()
        if data.get("status") == "success":
            return data.get("shortenedUrl")
        else:
            print(f"Error Cuty.io: {data.get('message', 'desconocido')}")
    return None

# ==================== RUTAS ====================

@app.route("/")
def home():
    return "Backend Dexter Modz activo ✅"

@app.route("/api/step/<int:step>")
def get_short_link(step):
    if step < 1 or step > 10:
        return jsonify({"error": "Paso inválido"}), 400
    current = session.get("current_step", 0)
    if step > current + 1:
        return jsonify({"error": "Debes completar los pasos en orden"}), 403
    session["current_step"] = step
    # ⚠️ CAMBIA ESTO POR LA URL DE TU WEB (Netlify, GitHub Pages, etc.)
    destino = f"https://TU_WEB_URL/?step={step}"
    short_url = generar_enlace_cuty(destino)
    if short_url:
        return jsonify({"url": short_url, "step": step})
    return jsonify({"error": "No se pudo generar el acortador"}), 500

@app.route("/api/generate-key", methods=["POST"])
def generate_key():
    current = session.get("current_step", 0)
    if current < 10:
        return jsonify({"error": "Debes completar los 10 pasos primero"}), 403
    key_data = generar_key_temporal()
    success, result = actualizar_users_json(key_data)
    if success:
        session.pop("current_step", None)
        return jsonify({
            "key": f"{key_data['usuario']}:{key_data['password']}",
            "usuario": key_data["usuario"],
            "password": key_data["password"],
            "expira_en": key_data["expira_en"]
        })
    return jsonify({"error": result}), 500

# ==================== EJECUCIÓN ====================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)