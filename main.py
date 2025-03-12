from flask import Flask, request, jsonify, render_template, url_for
import uuid
import time
import os  # Asegurar que 'os' está importado

app = Flask(__name__)

# Almacén temporal en memoria para mapear identificadores únicos a datos JSON
data_store = {}
EXPIRATION_SECONDS = 3600  # Los datos expiran después de 1 hora

def cleanup_expired_data():
    """Elimina datos expirados del almacenamiento."""
    now = time.time()
    keys_to_delete = [key for key, val in data_store.items() 
                      if now - val['timestamp'] > EXPIRATION_SECONDS]
    for key in keys_to_delete:
        del data_store[key]

@app.route('/generate', methods=['POST'])
def generate():
    """Recibe JSON y genera una URL corta con un identificador único."""
    data = request.get_json()
    if not data or not isinstance(data, list):
        return jsonify({"error": "Se espera una lista de competencias con entregables"}), 400

    # Transformar la estructura del JSON recibido
    competencias = []
    entregables = {}

    for item in data:
        if not isinstance(item, dict) or 'competencia' not in item or 'entregables' not in item:
            return jsonify({"error": "Cada objeto debe contener 'competencia' y 'entregables'"}), 400
        competencia = item['competencia']
        if not isinstance(item['entregables'], list) or len(item['entregables']) != 5:
            return jsonify({"error": f"La competencia '{competencia}' debe tener exactamente 5 entregables"}), 400
        competencias.append(competencia)
        entregables[competencia] = item['entregables']

    # Generar un identificador único (UUID corto)
    unique_id = str(uuid.uuid4())[:8]  # Solo los primeros 8 caracteres para hacerlo más corto

    # Almacenar datos en memoria
    data_store[unique_id] = {
        'competencias': competencias,
        'entregables': entregables,
        'timestamp': time.time()
    }

    # Limpiar datos expirados antes de devolver la URL
    cleanup_expired_data()

    # Obtener el puerto correcto para la URL
    port = os.environ.get('PORT', '5000')  # Usar 5000 por defecto si no está definido
    base_url = request.host_url.rstrip('/')  # Obtener la URL base sin la barra final
    if f":{port}" not in base_url:  # Asegurar que el puerto esté presente en la URL
        base_url += f":{port}"

    # Generar URL corta con el identificador y el puerto correcto
    short_url = f"{base_url}/display/{unique_id}"

    return jsonify({"url": short_url, "id": unique_id})

@app.route('/display/<identifier>')
def display(identifier):
    """Recupera y muestra los datos almacenados con el identificador único."""
    entry = data_store.get(identifier)
    if not entry:
        return "Datos no encontrados o expirados", 404

    # Verificar si los datos han expirado
    if time.time() - entry['timestamp'] > EXPIRATION_SECONDS:
        del data_store[identifier]  # Eliminar datos vencidos
        return "Datos no encontrados o expirados", 404

    competencias = entry['competencias']
    entregables = entry['entregables']

    # Mostrar en una plantilla HTML
    return render_template('display.html', competencias=competencias, entregables=entregables)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Corregido con la importación de 'os'
    app.run(host='0.0.0.0', port=port)
