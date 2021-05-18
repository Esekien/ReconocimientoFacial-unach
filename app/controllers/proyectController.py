from flask import Flask, request, redirect, url_for, flash,Response, stream_with_context
from flask import session as sesion
from flask import Blueprint, render_template
import face_recognition
import cv2
import numpy as np
from app import db
from app import app


import time

import os
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, desc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

from app.Model.Model import Examen
from app.Model.Model import Usuario


engine = create_engine('mysql+pymysql://root:@localhost/reconocimiento')
Session = sessionmaker(bind=engine)
session = Session()



camera = cv2.VideoCapture(0)




#SEGUIR CON LA LIBRERIA LOGIN

#DEFINICIÓN DE TODAS LAS FUNCIONES
face_recognition_Route = Blueprint('face_recognition',__name__)

class Loging():
    #DEFINICION DE LA RUTA RAIZ DE LOGIN
    @face_recognition_Route.route('/',methods=['GET','POST'])
    def login():
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']
            user = session.query(Usuario.id).filter_by(correo=email,contraseña=password).scalar()
            print('entro2')
            if user:
                sesion['user'] = user
                return redirect('/home')
            if not user:
                flash('Contraseña incorrecta')
                return render_template('login.html')
        return render_template('login.html')

    #DEFINICION DE LA RUTA DE HOME, PANTALLA PRINCIPAL
    @face_recognition_Route.route('/home')
    def index():
        if 'user' in sesion:
            print(sesion['user'])
            return render_template('index.html')
        return redirect('/')
    #DEFINICION DEL TEMPLATE DE INDICACIONES
    @face_recognition_Route.route('/indicaciones')
    def indicaciones():
        if 'user' in sesion:
            #LE INDICAMOS AL PROGRAMA QUE EN LA BD EL ATRIBUTO RECONOCIDO ES UN FALSE
            id_de_sesion= sesion['user']
            user = session.query(Examen).filter_by(idUsuario=id_de_sesion).first()
            print(user)
            user.Reconocido = False
            session.commit()
            return render_template('indicaciones.html')
        return redirect('/')
    
    #DEFINICION DE LA RUTA DE DONDE SE SUBE LA FOTO DEL USUARIO 
    @face_recognition_Route.route('/inicio')
    def inicio():
        if 'user' in sesion:
            return render_template('inicio.html')
        return redirect('/')
    
    @face_recognition_Route.route('/activar')
    def activar():
        if 'user' in sesion:
            print(sesion['user'])
            return render_template('activar.html')
        return redirect('/')

    #VALIDACION DEL ROSTRO DEL USUARIO
    @face_recognition_Route.route('/validacion')
    def validarFace():
        time.sleep(5)
        user = session.query(Examen).filter_by(idUsuario=sesion['user']).first()
        if user.Reconocido:
           return redirect('https://www.educa-t.unach.mx/login/index.php')
        else:
            flash('Rostro no reconocido vuelve a intentarlo...')
            return redirect('/activar')


    #GUARDAR LA IMAGEN DEL USUARIO EN FORMATO ESPECIFICADO
    @face_recognition_Route.route('/aceptar', methods=['POST'])
    def aceptar():
        ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
        _matricula=request.form['txtmatricula']
        _nombre=request.form['txtnombre']
        _archivo=request.files['customFile']
        #print(_archivo)
        if _matricula =='' or _nombre =='' or _archivo.filename=='':
            flash('Recuerda Llenar Todos los Campos')
            return redirect('registrar')
        filename = secure_filename(str(_matricula) +".jpg")
        print(filename)
        # Guardamos el archivo en el directorio "Archivos PDF"
        _archivo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        # Retornamos una respuesta satisfactoria
        return redirect('/home')
    #REDIRECCIONAMIENTO AL TEMPLATE DE GUARDAR FOTO
    @face_recognition_Route.route('/registrar')
    def registrar():
        if 'user' in sesion:
            return render_template('registrar.html')
        return redirect('/')


    #aQUI OCURRE LA MAGIA DEL RECONOCIMIENTO FACIAL
    @face_recognition_Route.route('/video_feed')
    def video_feed():
        id_de_sesion= sesion['user']
        def gen_frames():  
            
            flag = 0
            matricula = session.query(Usuario.Matricula).filter_by(id=id_de_sesion).first()
            print(matricula)
            #LE PASAMOS EL VALOR DE LA SESION DEL USUARIO PARA BUSCAR SU ROSTRO
            obama_image = face_recognition.load_image_file("./app/static/alumnos/"+matricula[0]+".jpg")
            print(obama_image)
            obama_face_encoding = face_recognition.face_encodings(obama_image)[0]


            # Create arrays of known face encodings and their names
            known_face_encodings = [
                obama_face_encoding
            ]
            known_face_names = [
                #AQUI PONEMOS EL NOMBRE DE LA MATRICULA EN LA PANTALLA DE RECONOCIMIENTO FACIAL
                matricula[0],
            ]

            # Initialize some variables
            face_locations = []
            face_encodings = []
            face_names = []
            process_this_frame = True
            var = True
            flag = 0
            while var :
                success, frame = camera.read()  # read the camera frame

                small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

                rgb_small_frame = small_frame[:, :, ::-1]

                if process_this_frame:
                    # Find all the faces and face encodings in the current frame of video
                    face_locations = face_recognition.face_locations(rgb_small_frame)
                    face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

                    face_names = []
                    #FOR QUE BUSCA EL ROSTRO ENTRE LAS IMAGENES DADAS
                    for face_encoding in face_encodings:
                        # See if the face is a match for the known face(s)
                        matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                        name = "Unknown"

                        # # If a match was found in known_face_encodings, just use the first one.
                        # if True in matches:
                        #     first_match_index = matches.index(True)
                        #     name = known_face_names[first_match_index]

                        # Or instead, use the known face with the smallest distance to the new face
                        face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                        best_match_index = np.argmin(face_distances)
                        if matches[best_match_index]:
                            name = known_face_names[best_match_index]

                        face_names.append(name)
                        
                        for item in face_names:
                            #CONVERTIMOS EN TRUE EL ATRIBUTO RECONOCIMIENTO, Y SE VALIDA EL USUARIO
                            if item == matricula[0] and flag == 0:
                                user = session.query(Examen).filter_by(idUsuario=id_de_sesion).first()
                                user.Reconocido = True
                                session.commit()
                                print('entro')
                                flag = 1
                                
                process_this_frame = not process_this_frame   
                for (top, right, bottom, left), name in zip(face_locations, face_names):
                    # Scale back up face locations since the frame we detected in was scaled to 1/4 size
                    top *= 4
                    right *= 4
                    bottom *= 4
                    left *= 4
                    # SE DEFINE EL TAMAÑO DEL FRAME DE LA CAMARA
                    # Draw a box around the face
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

                    # Draw a label with a name below the face
                    cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
                    font = cv2.FONT_HERSHEY_DUPLEX
                    cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)
                    
                if not success:

                    break
                    
                else:
                    ret, buffer = cv2.imencode('.jpg', frame)
                    frame = buffer.tobytes()
                    yield (b'--frame\r\n'
                        b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result

        

        return  Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
        
        #SE RESUELVE AL INSERTAR TRUE EN UNA BD Y LUEGO PREGUNTAR SI YA ESTA TRUE PARA QUE PROSIGA EL EXAMEN