from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db

class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    # Relaciones futuras
    ligas = db.relationship("Liga", backref="usuario", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Liga(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)

    equipos = db.relationship("Equipo", back_populates="liga", lazy=True)
    partidos = db.relationship("Partido", backref="liga", lazy=True)

class Equipo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    liga_id = db.Column(db.Integer, db.ForeignKey("liga.id"), nullable=False)
    liga = db.relationship("Liga", back_populates="equipos")
    puntos_totales = db.Column(db.Integer, default=0)
    ganados = db.Column(db.Integer, default=0)
    empatados = db.Column(db.Integer, default=0)
    perdidos = db.Column(db.Integer, default=0)
    goles_favor = db.Column(db.Integer, default=0)
    goles_contra = db.Column(db.Integer, default=0)
    puntos_juego_limpio = db.Column(db.Integer, default=0)
    puntos_arbitro = db.Column(db.Integer, default=0)
    puntos_grada = db.Column(db.Integer, default=0)

class Partido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    liga_id = db.Column(db.Integer, db.ForeignKey('liga.id'))
    equipo_local_id = db.Column(db.Integer, db.ForeignKey('equipo.id'))
    equipo_visitante_id = db.Column(db.Integer, db.ForeignKey('equipo.id'))
    arbitro_id = db.Column(db.Integer, db.ForeignKey('equipo.id'))
    tutor_grada_local_id = db.Column(db.Integer, db.ForeignKey('equipo.id'))
    tutor_grada_visitante_id = db.Column(db.Integer, db.ForeignKey('equipo.id'))
    goles_local = db.Column(db.Integer, default=0)
    goles_visitante = db.Column(db.Integer, default=0)
    puntos_local = db.Column(db.Integer, default=0)
    puntos_visitante = db.Column(db.Integer, default=0)
    finalizado = db.Column(db.Boolean, default=False)
    puntos_juego_limpio_local = db.Column(db.Integer, default=0)
    puntos_juego_limpio_visitante = db.Column(db.Integer, default=0)
    puntos_arbitro = db.Column(db.Integer, default=0)
    puntos_grada_local = db.Column(db.Integer, default=0)
    puntos_grada_visitante = db.Column(db.Integer, default=0)

    equipo_local = db.relationship('Equipo', foreign_keys=[equipo_local_id])
    equipo_visitante = db.relationship('Equipo', foreign_keys=[equipo_visitante_id])
    arbitro = db.relationship('Equipo', foreign_keys=[arbitro_id])
    tutor_grada_local = db.relationship('Equipo', foreign_keys=[tutor_grada_local_id])
    tutor_grada_visitante = db.relationship('Equipo', foreign_keys=[tutor_grada_visitante_id])

    def calcular_puntos(self):
        """
        Este método calcula los puntos de un equipo después de un partido,
        sumando los puntos por juego limpio, arbitraje y grada.
        """
        puntos = self.puntos_local if self.equipo_local else 0
        if self.finalizado:
            if self.goles_local > self.goles_visitante:
                puntos += 3  # Ganador
            elif self.goles_local < self.goles_visitante:
                puntos += 0  # Perdedor
            else:
                puntos += 1  # Empate
        return puntos
