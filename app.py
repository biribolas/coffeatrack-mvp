import streamlit as st
import sqlite3
from datetime import datetime

# ------------------ CONFIG ------------------
DB_NAME = "lotes.db"

FIRMAS = [
    "NKG Stockler", "Cofco", "Sucafina", "Volcafé", "Eisa",
    "Mitsui", "Olam", "Ocramar", "Comexim"
]

# ------------------ DATABASE ------------------
def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def create_table():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS lotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_lote TEXT NOT NULL,
            status TEXT NOT NULL,
            firma TEXT,
            corretor TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

create_table()

# ------------------ HELPERS ------------------
def inserir_lote(numero_lote):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO lotes (numero_lote, status)
        VALUES (?, 'Pendente')
    """, (numero_lote,))
    conn.commit()
    conn.close()

def buscar_lotes_pendentes():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, numero_lote FROM lotes WHERE status = 'Pendente'")
    rows = c.fetchall()
    conn.close()
    return rows

def confirmar_entrega(lote_id, firma, corretor):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        UPDATE lotes
        SET status = 'Entregue',
            firma = ?,
            corretor = ?,
            timestamp = ?
        WHERE id = ?
    """, (firma, corretor, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), lote_id))
    conn.commit()
    conn.close()

def buscar_todos_lotes():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT numero_lote, status, firma, corretor, timestamp
        FROM lotes
        ORDER BY id DESC
    """)
    rows = c.fetchall()
    conn.close()
    return rows

# ------------------ UI ------------------
st.set_page_config(page_title="Corretora de Café - MVP", layout="centered")

st.title("☕ Rastreamento de Amostras - Corretora de Café")

pagina = st.sidebar.selectbox(
    "Navegação",
    ["Admin (Escritório)", "Corretor (Rua)", "Relatório"]
)

# ------------------ ADMIN ------------------
if pagina == "Admin (Escritório)":
    st.header("📋 Gerar Lote")

    numero_lote = st.text_input("Número do Lote")

    if st.button("Gerar Lote"):
        if numero_lote.strip() == "":
            st.error("Informe o número do lote.")
        else:
            inserir_lote(numero_lote)
            st.success(f"Lote {numero_lote} criado com status Pendente.")

# ------------------ CORRETOR ------------------
elif pagina == "Corretor (Rua)":
    st.header("🚚 Entrega de Amostras")

    corretor = st.text_input("Nome do Corretor")

    lotes = buscar_lotes_pendentes()

    if not lotes:
        st.info("Nenhum lote pendente.")
    else:
        lote_dict = {f"Lote {l[1]}": l[0] for l in lotes}
        lote_selecionado = st.selectbox("Selecione o Lote", lote_dict.keys())

        firma = st.selectbox("Selecione a Firma", FIRMAS)

        if st.button("Confirmar Entrega"):
            if corretor.strip() == "":
                st.error("Informe o nome do corretor.")
            else:
                confirmar_entrega(
                    lote_dict[lote_selecionado],
                    firma,
                    corretor
                )
                st.success("Entrega registrada com sucesso.")
                st.rerun()

# ------------------ RELATÓRIO ------------------
elif pagina == "Relatório":
    st.header("📊 Relatório de Lotes")

    dados = buscar_todos_lotes()

    st.table([
        {
            "Lote": d[0],
            "Status": d[1],
            "Firma": d[2],
            "Corretor": d[3],
            "Horário": d[4]
        }
        for d in dados
    ])
