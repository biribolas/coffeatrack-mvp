import streamlit as st
import sqlite3
import os
from datetime import datetime

# ---------------- CONFIG ----------------
DB_NAME = "lotes.db"
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

FIRMAS = [
    "NKG Stockler", "Cofco", "Sucafina", "Volcafé", "Elam",
    "Mitsui", "Olam", "Louis Dreyfus", "Tristão", "Comexim", "Neumann"
]

# ---------------- DATABASE ----------------
def get_conn():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS lotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_lote TEXT,
            sacas INTEGER,
            total_vias INTEGER
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS vias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lote_id INTEGER,
            numero_via INTEGER,
            status TEXT,
            firma TEXT,
            corretor TEXT,
            timestamp TEXT,
            FOREIGN KEY (lote_id) REFERENCES lotes(id)
        )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- HELPERS ----------------
def criar_lote(numero_lote, sacas, vias):
    conn = get_conn()
    c = conn.cursor()

    c.execute(
        "INSERT INTO lotes (numero_lote, sacas, total_vias) VALUES (?, ?, ?)",
        (numero_lote, sacas, vias)
    )
    lote_id = c.lastrowid

    for i in range(1, vias + 1):
        c.execute("""
            INSERT INTO vias (lote_id, numero_via, status)
            VALUES (?, ?, 'Pendente')
        """, (lote_id, i))

    conn.commit()
    conn.close()

def vias_pendentes():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT v.id, l.numero_lote, l.sacas, v.numero_via
        FROM vias v
        JOIN lotes l ON v.lote_id = l.id
        WHERE v.status = 'Pendente'
    """)
    rows = c.fetchall()
    conn.close()
    return rows

def entregar_via(via_id, firma, corretor):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        UPDATE vias
        SET status='Entregue',
            firma=?,
            corretor=?,
            timestamp=?
        WHERE id=?
    """, (firma, corretor, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), via_id))
    conn.commit()
    conn.close()

def relatorio():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT l.numero_lote, l.sacas, v.numero_via, v.status, v.firma, v.corretor, v.timestamp, v.id
        FROM vias v
        JOIN lotes l ON v.lote_id = l.id
        ORDER BY l.id DESC, v.numero_via
    """)
    rows = c.fetchall()
    conn.close()
    return rows

def atualizar_via(via_id, firma, corretor):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        UPDATE vias SET firma=?, corretor=? WHERE id=?
    """, (firma, corretor, via_id))
    conn.commit()
    conn.close()

def apagar_via(via_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM vias WHERE id=?", (via_id,))
    conn.commit()
    conn.close()

# ---------------- UI ----------------
st.set_page_config(page_title="CoffeaTrack", layout="centered")
st.title("☕ CoffeaTrack - Rastreamento de Amostras")

pagina = st.sidebar.selectbox("Menu", ["Corretor", "Admin", "Relatório"])

# ---------------- CORRETOR ----------------
if pagina == "Corretor":
    st.header("🚚 Entrega de Via")

    corretor = st.text_input("Nome do Corretor")
    vias = vias_pendentes()

    if not vias:
        st.info("Nenhuma via pendente.")
    else:
        opcoes = {
            f"Lote {v[1]} | {v[2]} sacas | Via {v[3]}": v[0]
            for v in vias
        }
        escolha = st.selectbox("Selecione a Via", opcoes.keys())
        firma = st.selectbox("Firma", FIRMAS)

        if st.button("Confirmar Entrega"):
            if corretor.strip() == "":
                st.error("Informe o nome do corretor.")
            else:
                entregar_via(opcoes[escolha], firma, corretor)
                st.success("Entrega registrada.")
                st.rerun()

# ---------------- ADMIN ----------------
elif pagina == "Admin":
    senha = st.text_input("Senha do Admin", type="password")

    if senha != ADMIN_PASSWORD:
        st.warning("Acesso restrito.")
    else:
        st.header("🔐 Admin")

        st.subheader("Criar Lote")
        numero = st.text_input("Número do Lote")
        sacas = st.number_input("Sacas", min_value=1)
        vias = st.number_input("Quantidade de Vias", min_value=1)

        if st.button("Criar Lote"):
            criar_lote(numero, sacas, vias)
            st.success("Lote criado com sucesso.")
            st.rerun()

# ---------------- RELATÓRIO ----------------
elif pagina == "Relatório":
    st.header("📊 Relatório de Vias")

    dados = relatorio()

    for d in dados:
        with st.expander(f"Lote {d[0]} | Via {d[2]}"):
            st.write(f"Sacas: {d[1]}")
            st.write(f"Status: {d[3]}")
            st.write(f"Firma: {d[4]}")
            st.write(f"Corretor: {d[5]}")
            st.write(f"Horário: {d[6]}")

            senha = st.text_input("Senha Admin", type="password", key=f"senha_{d[7]}")
            if senha == ADMIN_PASSWORD:
                nova_firma = st.selectbox("Editar Firma", FIRMAS, index=FIRMAS.index(d[4]) if d[4] in FIRMAS else 0)
                novo_corretor = st.text_input("Editar Corretor", d[5] or "")

                if st.button("Salvar Alterações", key=f"salvar_{d[7]}"):
                    atualizar_via(d[7], nova_firma, novo_corretor)
                    st.success("Atualizado.")
                    st.rerun()

                if st.button("Apagar Via", key=f"apagar_{d[7]}"):
                    apagar_via(d[7])
                    st.error("Via apagada.")
                    st.rerun()
