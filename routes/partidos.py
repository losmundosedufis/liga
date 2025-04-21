from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Partido, Equipo, Liga
import random

partidos_bp = Blueprint("partidos", __name__)

@partidos_bp.route("/calendario/<int:liga_id>")
@login_required
def calendario(liga_id):
    liga = Liga.query.filter_by(id=liga_id, usuario_id=current_user.id).first()
    if not liga:
        flash("Liga no encontrada.")
        return redirect(url_for("ligas.dashboard"))

    partidos = Partido.query.filter_by(liga_id=liga.id).all()
    return render_template("calendario.html", liga=liga, partidos=partidos)

@partidos_bp.route("/liga/<int:liga_id>/clasificacion")
@login_required
def clasificacion(liga_id):
    liga = Liga.query.filter_by(id=liga_id, usuario_id=current_user.id).first()
    if not liga:
        flash("Liga no encontrada.")
        return redirect(url_for("ligas.dashboard"))

    partidos = Partido.query.filter_by(liga_id=liga_id, finalizado=True).all()
    equipos = Equipo.query.filter_by(liga_id=liga_id).all()

    clasificacion = {}

    # Inicializar cada equipo
    for equipo in equipos:
        clasificacion[equipo.id] = {
            "nombre": equipo.nombre,
            "puntos_totales": 0,
            "ganados": 0,
            "empatados": 0,
            "perdidos": 0,
            "goles_favor": 0,
            "goles_contra": 0,
            "puntos_juego_limpio": 0,
            "puntos_arbitro": 0,
            "puntos_grada": 0,
        }

    # Calcular los datos desde los partidos finalizados
    for p in partidos:
        cl = clasificacion[p.equipo_local_id]
        cv = clasificacion[p.equipo_visitante_id]

        # Goles
        cl["goles_favor"] += p.goles_local
        cl["goles_contra"] += p.goles_visitante
        cv["goles_favor"] += p.goles_visitante
        cv["goles_contra"] += p.goles_local

        # Resultado
        if p.goles_local > p.goles_visitante:
            cl["ganados"] += 1
            cv["perdidos"] += 1
        elif p.goles_local < p.goles_visitante:
            cv["ganados"] += 1
            cl["perdidos"] += 1
        else:
            cl["empatados"] += 1
            cv["empatados"] += 1

        # Puntos totales
        cl["puntos_totales"] += p.puntos_local
        cv["puntos_totales"] += p.puntos_visitante

        # Puntos educativos
        cl["puntos_juego_limpio"] += p.puntos_juego_limpio_local or 0
        cv["puntos_juego_limpio"] += p.puntos_juego_limpio_visitante or 0
        clasificacion[p.arbitro_id]["puntos_arbitro"] += p.puntos_arbitro or 0
        clasificacion[p.tutor_grada_local_id]["puntos_grada"] += p.puntos_grada_local or 0
        clasificacion[p.tutor_grada_visitante_id]["puntos_grada"] += p.puntos_grada_visitante or 0

    # Convertir a lista ordenada
    clasificacion_ordenada = sorted(
        clasificacion.values(),
        key=lambda x: (-x["puntos_totales"], -(x["goles_favor"] - x["goles_contra"]))
    )

    return render_template("clasificacion.html", liga=liga, clasificacion=clasificacion_ordenada)

@partidos_bp.route("/liga/<int:liga_id>/generar_calendario")
@login_required
def generar_calendario(liga_id):
    liga = Liga.query.filter_by(id=liga_id, usuario_id=current_user.id).first()
    if not liga:
        flash("Liga no encontrada.")
        return redirect(url_for("ligas.dashboard"))

    # Verificar que la liga tiene equipos antes de generar el calendario
    equipos = Equipo.query.filter_by(liga_id=liga_id).all()
    if len(equipos) < 2:
        flash("Necesitas al menos dos equipos en la liga para generar el calendario.")
        return redirect(url_for("ligas.gestionar_equipos", liga_id=liga_id))

    # Lógica para generar los partidos automáticamente (round robin)
    partidos_generados = []
    for i in range(len(equipos)):
        for j in range(i + 1, len(equipos)):
            equipo_local = equipos[i]
            equipo_visitante = equipos[j]
            arbitro = random.choice([e for e in equipos if e != equipo_local and e != equipo_visitante])
            tutor_grada_local = random.choice([e for e in equipos if e != equipo_local and e != equipo_visitante and e != arbitro])
            tutor_grada_visitante = random.choice([e for e in equipos if e != equipo_local and e != equipo_visitante and e != arbitro and e != tutor_grada_local])

            partido = Partido(
                liga_id=liga.id,
                equipo_local_id=equipo_local.id,
                equipo_visitante_id=equipo_visitante.id,
                arbitro_id=arbitro.id,
                tutor_grada_local_id=tutor_grada_local.id,
                tutor_grada_visitante_id=tutor_grada_visitante.id
            )
            db.session.add(partido)
            partidos_generados.append(partido)

    db.session.commit()

    flash(f"{len(partidos_generados)} partidos generados con éxito.")
    return redirect(url_for("partidos.calendario", liga_id=liga.id))

@partidos_bp.route("/gestionar_partido/<int:partido_id>", methods=["GET", "POST"])
@login_required
def gestionar_partido(partido_id):
    partido = Partido.query.get_or_404(partido_id)

    if request.method == "POST":
        accion = request.form.get("accion")

        if accion == "gol_local":
            partido.goles_local += 1
        elif accion == "restar_gol_local":
            partido.goles_local = max(0, partido.goles_local - 1)
        elif accion == "gol_visitante":
            partido.goles_visitante += 1
        elif accion == "restar_gol_visitante":
            partido.goles_visitante = max(0, partido.goles_visitante - 1)
        elif accion == "finalizar":
            partido.finalizado = True

            # Asignar puntos por resultado (3 victoria, 2 empate, 1 derrota)
            if partido.goles_local > partido.goles_visitante:
                partido.puntos_local = 3
                partido.puntos_visitante = 1
            elif partido.goles_local < partido.goles_visitante:
                partido.puntos_local = 1
                partido.puntos_visitante = 3
            else:
                partido.puntos_local = 2
                partido.puntos_visitante = 2

            # Puntos educativos
            partido.puntos_juego_limpio_local = int("juego_limpio_local" in request.form)
            partido.puntos_juego_limpio_visitante = int("juego_limpio_visitante" in request.form)
            partido.puntos_arbitro = int("arbitro_correcto" in request.form)
            partido.puntos_grada_local = int("grada_local" in request.form)
            partido.puntos_grada_visitante = int("grada_visitante" in request.form)

            db.session.commit()
            flash("✅ Partido finalizado correctamente. La clasificación ha sido actualizada.", "success")
            return redirect(url_for("partidos.calendario", liga_id=partido.liga_id))

        db.session.commit()
        flash("✅ Partido actualizado.", "success")
        return redirect(url_for("partidos.gestionar_partido", partido_id=partido.id))

    nombre_local = partido.equipo_local.nombre
    nombre_visitante = partido.equipo_visitante.nombre
    return render_template("gestionar_partido.html", partido=partido, nombre_local=nombre_local, nombre_visitante=nombre_visitante)

from flask import jsonify

@partidos_bp.route("/api/actualizar_gol", methods=["POST"])
@login_required
def actualizar_gol():
    data = request.get_json()
    partido_id = data.get("partido_id")
    equipo = data.get("equipo")
    accion = data.get("accion")

    partido = Partido.query.get_or_404(partido_id)

    if partido.finalizado:
        return jsonify({"error": "El partido ya está finalizado."}), 403

    if equipo == "local":
        if accion == "sumar":
            partido.goles_local += 1
        elif accion == "restar":
            partido.goles_local = max(0, partido.goles_local - 1)
    elif equipo == "visitante":
        if accion == "sumar":
            partido.goles_visitante += 1
        elif accion == "restar":
            partido.goles_visitante = max(0, partido.goles_visitante - 1)

    db.session.commit()
    return jsonify({
        "goles_local": partido.goles_local,
        "goles_visitante": partido.goles_visitante
    })

@partidos_bp.route("/api/estado_partido/<int:partido_id>")
@login_required
def estado_partido(partido_id):
    partido = Partido.query.get_or_404(partido_id)
    return jsonify({
        "goles_local": partido.goles_local,
        "goles_visitante": partido.goles_visitante,
        "finalizado": partido.finalizado
    })