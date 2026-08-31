"""
Sorteio de Fone de Ouvido + Curso Gratuito de Montagem e Manutenção de Computadores
------------------------------------------------------------------------------------
Aplicação web (Flask) para os alunos se inscreverem pelo link e para o professor
sortear um vencedor em uma área administrativa protegida por senha.
"""

import os
import random
import sqlite3
from functools import wraps

from flask import Flask, flash, g, redirect, render_template, request, session, url_for

DB_PATH = os.path.join(os.path.dirname(__file__), "participantes.db")

# Defina uma senha própria antes de publicar (ou use a variável de ambiente ADMIN_SENHA)
ADMIN_SENHA = os.environ.get("ADMIN_SENHA", "microlins123")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "troque-esta-chave-antes-de-publicar")


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def fechar_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    with sqlite3.connect(DB_PATH) as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS participantes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                telefone TEXT NOT NULL
            )
            """
        )


def login_obrigatorio(rota):
    @wraps(rota)
    def decorada(*args, **kwargs):
        if not session.get("admin_logado"):
            return redirect(url_for("admin_login"))
        return rota(*args, **kwargs)
    return decorada


@app.route("/", methods=["GET", "POST"])
def inscricao():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        telefone = request.form.get("telefone", "").strip()

        if not nome or not telefone:
            flash("Preencha nome e telefone para se inscrever.", "erro")
            return redirect(url_for("inscricao"))

        db = get_db()
        db.execute("INSERT INTO participantes (nome, telefone) VALUES (?, ?)", (nome, telefone))
        db.commit()
        flash("Inscrição realizada com sucesso! Boa sorte 🎧", "sucesso")
        return redirect(url_for("inscricao"))

    return render_template("inscricao.html")


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        senha = request.form.get("senha", "")
        if senha == ADMIN_SENHA:
            session["admin_logado"] = True
            return redirect(url_for("admin"))
        flash("Senha incorreta.", "erro")
    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logado", None)
    return redirect(url_for("admin_login"))


@app.route("/admin")
@login_obrigatorio
def admin():
    db = get_db()
    participantes = db.execute("SELECT nome, telefone FROM participantes ORDER BY id").fetchall()
    return render_template("admin.html", participantes=participantes)


@app.route("/admin/sortear", methods=["POST"])
@login_obrigatorio
def sortear():
    db = get_db()
    participantes = db.execute("SELECT nome, telefone FROM participantes").fetchall()

    if not participantes:
        flash("Ainda não há participantes inscritos.", "erro")
        return redirect(url_for("admin"))

    vencedor = random.choice(participantes)
    flash(f"🎉 Vencedor(a): {vencedor['nome']} — {vencedor['telefone']}", "vencedor")
    return redirect(url_for("admin"))


init_db()  # garante que a tabela existe tanto rodando localmente quanto via gunicorn no Render

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
