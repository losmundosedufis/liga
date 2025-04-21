from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import Usuario, db

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        codigo = request.form["codigo"]
        password = request.form["password"]

        if Usuario.query.filter_by(codigo=codigo).first():
            flash("Este código ya está registrado.")
            return redirect(url_for("auth.register"))

        nuevo_usuario = Usuario(codigo=codigo)
        nuevo_usuario.set_password(password)
        db.session.add(nuevo_usuario)
        db.session.commit()
        flash("Registro exitoso. Ahora puedes iniciar sesión.")
        return redirect(url_for("auth.login"))

    return render_template("register.html")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        codigo = request.form["codigo"]
        password = request.form["password"]

        usuario = Usuario.query.filter_by(codigo=codigo).first()
        if usuario and usuario.check_password(password):
            login_user(usuario)
            return redirect(url_for("ligas.dashboard"))
        else:
            flash("Código o contraseña incorrectos.")
            return redirect(url_for("auth.login"))

    return render_template("login.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Sesión cerrada correctamente.")
    return redirect(url_for("auth.login"))

@auth_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("ligas.dashboard"))  # o donde quieras redirigir si está logueado
    return redirect(url_for("auth.login"))