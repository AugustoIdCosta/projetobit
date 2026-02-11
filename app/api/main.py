from flask import Flask, request, jsonify
import os
import psycopg2
from datetime import datetime


app = Flask(__name__)


# Realiza a conecção com o banco 
def get_db_connection():
    url = os.environ.get('DATABASE_URL')
    if not url:
        raise RuntimeError("DATABASE_URL não definida")
    conn = psycopg2.connect(url)
    return conn

def ensure_schema():
    #GARANTE QUE A TABELA EXISTA
    print("Verificando schema do banco ... ")
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS registro_valores(
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(10),
                valor NUMERIC,
                created_at timestamp DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"erro ao criar a tabela: {e}")

@app.route('/')
def health_check():
    """Rota raiz só para ver se a API está viva"""
    return jsonify({"status": "API is running!", "service": "CryptoTracker"})

@app.route('/history')
def get_history():
    """Rota principal: Vai no banco e busca os dados"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT symbol, valor, timestamp FROM registro_valores ORDER BY timestamp DESC LIMIT 100;')
        rows = cursor.fetchall()
        
        # Transforma a lista do Banco em JSON bonitinho
        results = []
        for row in rows:
            results.append({
                "symbol": row[0],
                "price": row[1],
                "timestamp": row[2]
            })
        cursor.close()
        conn.close()
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
if __name__ == '__main__':
    # host='0.0.0.0' é OBRIGATÓRIO para rodar dentro do Docker
    ensure_schema()
    app.run(host='0.0.0.0', port=5000)