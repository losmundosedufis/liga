from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import db, Liga, Equipo, Partido
import random
from itertools import combinations, cycle

ligas_bp = Blueprint("ligas", __name__)

@ligas_bp.route("/dashboard")
@login_required
def dashboard():
    ligas_usuario = Liga.query.filter_by(usuario_id=current_user.id).all()
    return render_template("dashboard.html", usuario=current_user, ligas=ligas_usuario)

@ligas_bp.route("/crear_liga", methods=["GET", "POST"])
@login_required
def crear_liga():
    if request.method == "POST":
        nombre = request.form.get("nombre")
        if not nombre:
            flash("Debes escribir un nombre para la liga.")
            return redirect(url_for("ligas.crear_liga"))

        nueva_liga = Liga(nombre=nombre, usuario_id=current_user.id)
        db.session.add(nueva_liga)
        db.session.commit()
        flash("¡Liga creada con éxito!")
        return redirect(url_for("ligas.dashboard"))

    return render_template("crear_liga.html")

@ligas_bp.route("/liga/<int:liga_id>")
@login_required
def ver_liga(liga_id):
    liga = Liga.query.filter_by(id=liga_id, usuario_id=current_user.id).first()
    if not liga:
        flash("Liga no encontrada o no tienes acceso.")
        return redirect(url_for("ligas.dashboard"))
    return render_template("ver_liga.html", liga=liga)

@ligas_bp.route("/liga/<int:liga_id>/gestionar_equipos", methods=["GET", "POST"])
@login_required
def gestionar_equipos(liga_id):
    liga = Liga.query.filter_by(id=liga_id, usuario_id=current_user.id).first()
    if not liga:
        flash("Liga no encontrada.")
        return redirect(url_for("ligas.dashboard"))

    if request.method == "POST":
        nombre_equipo = request.form.get("nombre_equipo")
        if nombre_equipo:
            nuevo_equipo = Equipo(nombre=nombre_equipo, liga_id=liga.id)
            db.session.add(nuevo_equipo)
            db.session.commit()
            flash("Equipo añadido con éxito.")
            return redirect(url_for("ligas.gestionar_equipos", liga_id=liga.id))

    equipos = Equipo.query.filter_by(liga_id=liga.id).all()
    return render_template("equipos_liga.html", liga=liga, equipos=equipos)

@ligas_bp.route("/liga/<int:liga_id>/equipo/<int:equipo_id>/editar", methods=["GET", "POST"])
@login_required
def editar_equipo(liga_id, equipo_id):
    liga = Liga.query.filter_by(id=liga_id, usuario_id=current_user.id).first()
    equipo = Equipo.query.filter_by(id=equipo_id, liga_id=liga_id).first()

    if not liga or not equipo:
        flash("Liga o equipo no encontrado.")
        return redirect(url_for("ligas.gestionar_equipos", liga_id=liga_id))

    if request.method == "POST":
        equipo.nombre = request.form.get("nombre_equipo")
        db.session.commit()
        flash("Equipo actualizado con éxito.")
        return redirect(url_for("ligas.gestionar_equipos", liga_id=liga.id))

    return render_template("editar_equipo.html", liga=liga, equipo=equipo)

@ligas_bp.route("/liga/<int:liga_id>/equipo/<int:equipo_id>/eliminar", methods=["POST"])
@login_required
def eliminar_equipo(liga_id, equipo_id):
    liga = Liga.query.filter_by(id=liga_id, usuario_id=current_user.id).first()
    equipo = Equipo.query.filter_by(id=equipo_id, liga_id=liga_id).first()

    if not liga or not equipo:
        flash("Liga o equipo no encontrado.")
        return redirect(url_for("ligas.gestionar_equipos", liga_id=liga_id))

    db.session.delete(equipo)
    db.session.commit()
    flash("Equipo eliminado con éxito.")
    return redirect(url_for("ligas.gestionar_equipos", liga_id=liga.id))

@ligas_bp.route("/liga/<int:liga_id>/generar_calendario")
@login_required
def generar_calendario(liga_id):
    liga = Liga.query.filter_by(id=liga_id, usuario_id=current_user.id).first()
    if not liga:
        flash("Liga no encontrada.")
        return redirect(url_for("ligas.dashboard"))
    
    equipos = Equipo.query.filter_by(liga_id=liga_id).all()
    if len(equipos) < 2:
        flash("Necesitas al menos dos equipos en la liga para generar el calendario.")
        return redirect(url_for("ligas.gestionar_equipos", liga_id=liga_id))

    partidos_generados = []
    partidos_posibles = list(combinations(equipos, 2))
    random.shuffle(partidos_posibles)

    rotacion = cycle(equipos)
    en_juego = []

    for equipo_local, equipo_visitante in partidos_posibles:
        # Asegurarse de no repetir equipos inmediatamente
        if equipo_local in en_juego or equipo_visitante in en_juego:
            siguiente = next(rotacion)
            while siguiente in en_juego:
                siguiente = next(rotacion)
            en_juego = [siguiente]
            continue

        en_juego = [equipo_local, equipo_visitante]

        arbitro = random.choice([e for e in equipos if e not in en_juego])
        tutor_grada_local = random.choice([e for e in equipos if e not in en_juego and e != arbitro])
        posibles_grada_visitante = [e for e in equipos if e not in en_juego and e != arbitro and e != tutor_grada_local]
        tutor_grada_visitante = random.choice(posibles_grada_visitante) if posibles_grada_visitante else None

        partido = Partido(
            liga_id=liga.id,
            equipo_local_id=equipo_local.id,
            equipo_visitante_id=equipo_visitante.id,
            arbitro_id=arbitro.id,
            tutor_grada_local_id=tutor_grada_local.id,
            tutor_grada_visitante_id=tutor_grada_visitante.id if tutor_grada_visitante else None
        )
        db.session.add(partido)
        partidos_generados.append(partido)

    db.session.commit()

    flash(f"{len(partidos_generados)} partidos generados con éxito.")
    return redirect(url_for("partidos.calendario", liga_id=liga.id))

@ligas_bp.route("/liga/<int:liga_id>/eliminar", methods=["POST"])
@login_required
def eliminar_liga(liga_id):
    liga = Liga.query.filter_by(id=liga_id, usuario_id=current_user.id).first()
    if not liga:
        flash("Liga no encontrada.")
        return redirect(url_for("ligas.dashboard"))
    
    db.session.delete(liga)
    db.session.commit()
    flash("Liga eliminada con éxito.")
    return redirect(url_for("ligas.dashboard"))

@ligas_bp.route("/liga/<int:liga_id>/eliminar_partidos", methods=["POST"])
@login_required
def eliminar_partidos_de_liga(liga_id):
    liga = Liga.query.filter_by(id=liga_id, usuario_id=current_user.id).first()
    if not liga:
        flash("Liga no encontrada.")
        return redirect(url_for("ligas.dashboard"))

    partidos = Partido.query.filter_by(liga_id=liga_id).all()
    for p in partidos:
        db.session.delete(p)
    db.session.commit()

    flash("Todos los partidos de la liga han sido eliminados. Puedes generar un nuevo calendario.")
    return redirect(url_for("ligas.ver_liga", liga_id=liga.id))
