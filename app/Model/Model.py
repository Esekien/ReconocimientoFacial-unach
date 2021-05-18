import sys
sys.path.append(".")
from app import db
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Table, Column, Integer, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship



class Usuario(db.Model):
    __tablename__ = 'Usuario'
    id = db.Column(db.Integer, primary_key=True)
    correo = db.Column(db.String(50))
    contraseña = db.Column(db.String(50))
    Matricula = db.Column(db.String(50))

    Examen = relationship("Examen")
class Examen(db.Model):
    __tablename__ = 'Examen'
    id = db.Column(db.Integer, primary_key=True)
    Materia = db.Column(db.String(50))
    Reconocido = db.Column(db.Boolean, default=False)
    idUsuario = Column(Integer, ForeignKey('Usuario.id'))







#PREGUNTAR SI YA EXISTEN PARA NO CREARLO DE NUEVO
db.create_all()