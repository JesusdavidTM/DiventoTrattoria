from dotenv import load_dotenv
from flask import Flask, render_template, jsonify, request
import json
import mysql.connector
import requests
import os
load_dotenv()


app = Flask(__name__)

# Carga el menú desde un JSON para facilitar edición
with open('data/menu.json', encoding='utf-8') as f:
    menu = json.load(f)

# Carga de variables de entorno
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

db_config = {
    'host':     os.getenv('MYSQL_HOST', 'localhost'),
    'user':     os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASS', ''),
    'database': os.getenv('MYSQL_DB', 'divento'),
    'charset':  'utf8mb4'
}


def get_db():
    return mysql.connector.connect(**db_config)


@app.route('/')
def index():
    return render_template('index.html', menu=menu)


@app.route('/api/cart', methods=['POST'])
def api_cart():
    data = request.get_json() or {}
    cart = data.get('cart', {})
    total = 0.0
    items = []

    for dish in menu:
        qty = cart.get(str(dish['id']), 0)
        if qty:
            subtotal = round(dish['price'] * qty, 2)
            total += subtotal
            items.append({
                'id':       dish['id'],
                'name':     dish['name'],
                'price':    dish['price'],
                'qty':      qty,
                'subtotal': subtotal
            })

    return jsonify({
        'items': items,
        'total': round(total, 2)
    })


@app.route('/checkout', methods=['POST'])
def checkout():
    data = request.get_json() or {}
    cart = data.get('cart', {})
    name = data.get('name', '').strip()
    phone = data.get('phone', '').strip()
    address = data.get('address', '').strip()

    # Validación básica
    if not all([cart, name, phone, address]):
        return jsonify({'error': 'Faltan datos obligatorios'}), 400

    # Total de comida
    food_total = sum(
        dish['price'] * cart.get(str(dish['id']), 0)
        for dish in menu
    )
    food_total = round(food_total, 2)

    # Cálculo de envío con Google Maps
    try:
        resp = requests.get(
            "https://maps.googleapis.com/maps/api/distancematrix/json",
            params={
                'origins':      "Area+51+Monter%C3%ADa,+Colombia",
                'destinations': address,
                'key':          GOOGLE_MAPS_API_KEY
            },
            timeout=5
        )
        resp.raise_for_status()
        data_map = resp.json()

        if data_map.get('status') != 'OK':
            return jsonify({'error': 'Error en API de Google Maps'}), 500

        element = data_map['rows'][0]['elements'][0]
        if element.get('status') != 'OK':
            return jsonify({'error': 'Dirección no válida'}), 400

        dist_km = element['distance']['value'] / 1000.0
        if dist_km <= 0.5:
            delivery_cost = 3.00
        elif dist_km <= 1.9:
            delivery_cost = 4.00
        elif dist_km <= 2.4:
            delivery_cost = 5.00
        else:
            delivery_cost = 6.00

    except requests.RequestException as e:
        return jsonify({'error': 'Error al llamar a Google Maps', 'detail': str(e)}), 500

    delivery_cost = round(delivery_cost, 2)
    grand_total = round(food_total + delivery_cost, 2)

    # Guardar pedido en MySQL
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO orders
                (customer_name, customer_phone, customer_address,
                cart_json, food_total, delivery_cost, grand_total)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (
            name, phone, address,
            json.dumps(cart, ensure_ascii=False),
            food_total, delivery_cost, grand_total
        ))
        order_id = cursor.lastrowid
        conn.commit()
    except mysql.connector.Error as err:
        return jsonify({'error': 'Error de base de datos', 'detail': str(err)}), 500
    finally:
        cursor.close()
        conn.close()

    # Responder al cliente
    return jsonify({
        'order_id':      order_id,
        'food_total':    food_total,
        'delivery_cost': delivery_cost,
        'grand_total':   grand_total
    })


if __name__ == '__main__':
    # Verificación de conexión a MySQL
    try:
        db = get_db()
        print("✅ Conexión a MySQL OK")
        db.close()
    except Exception as e:
        print("❌ Error conectando a MySQL:", e)

    app.run(debug=True)
