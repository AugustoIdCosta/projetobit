import time
import requests
import psycopg2
import os
from datetime import datetime

# --- CONFIGURAÇÕES ---
# O Worker também precisa saber onde fica o banco para guardar o ouro
DATABASE_URL = os.getenv('DATABASE_URL')

# Configuração da API externa (CoinGecko é grátis e pública)
COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"

def get_db_connection():
    """Conecta no banco de dados"""
    if not DATABASE_URL:
        print("Erro: DATABASE_URL não definida!")
        return None
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"Erro ao conectar no banco: {e}")
        return None

def fetch_bitcoin_price():
    """Vai na internet buscar o preço atual"""
    try:
        response = requests.get(COINGECKO_URL, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data['bitcoin']['usd']
        else:
            print(f"Erro na API CoinGecko: {response.status_code}")
            return None
    except Exception as e:
        print(f"Erro de conexão: {e}")
        return None

def save_price(price):
    """Salva o preço no banco"""
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        cur = conn.cursor()
        # Inserimos na mesma tabela usada pela API: registro_valores
        # Colunas: symbol, valor; id e created_at são gerados automaticamente
        cur.execute(
            "INSERT INTO registro_valores (symbol, valor) VALUES (%s, %s)",
            ('BTC', price)
        )
        conn.commit()
        cur.close()
        conn.close()
        print(f"💰 Preço salvo: ${price}")
    except Exception as e:
        print(f"Erro ao salvar no banco: {e}")


if __name__ == "__main__":
    print("🚀 Worker iniciado! Monitorando Bitcoin...")
    
    while True:
        # 1. Busca o preço
        price = fetch_bitcoin_price()
        
        # 2. Se conseguiu pegar, salva no banco
        if price:
            save_price(price)
        
        # 3. Dorme por 30 segundos (para não ser bloqueado pela API)
        print("💤 Dormindo 30 segundos...")
        time.sleep(30)