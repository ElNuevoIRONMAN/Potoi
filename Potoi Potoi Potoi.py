import tkinter as tk
from PIL import Image, ImageTk
import random
import os
import pygame
import secrets

os.chdir(os.path.dirname(__file__))

class Juego:
    def __init__(self, parent, dificultad, volver_a_menu_callback):
        self.parent = parent
        self.dificultad = dificultad
        self.volver_a_menu_callback = volver_a_menu_callback

        self.frame = tk.Frame(self.parent, bg="#3bb371")
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(self.frame, width=800, height=600, highlightthickness=0, bd=0)
        self.canvas.pack()

        self.fondo_imagen = None
        self.cambiar_fondo("Images/fond.png")

        self.profesor = None
        self.alumnos = []
        self.alumnos_restantes = 50
        self.teclas_presionadas = set()

        self.profesor_skin = "Images/profesor.png"
        self.profesor_skin_alt = "Images/profesor1.png"
        self.profesor_pos = [400, 300]
        self.profesor_size = 50

        self.alumno_size = 40
        self.imagenes_guardadas = []

        self.crear_profesor()
        self.generar_alumnos(self.alumnos_restantes)

        if self.dificultad in ("normal", "difficile"):
            self.alumno_rebelde = self.crear_alumno_rebelde()

        if self.dificultad == "difficile":
            self.inspector_activo = False
            self.inspector_imagen_id = None
            self.inspector_texto_id = None
            self.inspector_imgtk = None
            self.texto_perdida_id = None
            self.imagen_inspector_visible = False

        self.marcador = self.canvas.create_text(
            400, 30, text=f"Élèves qui restent : {self.alumnos_restantes}",
            font=("Arial", 30), fill="black", tags="marcador"
        )

        self.boton_volver = tk.Button(self.frame, command=self.volver, relief="raised", bd=2)
        self.boton_volver.place(x=750, y=10, width=40, height=40)
        self.boton_volver.config(
            text="⮨",
            font=("Arial", 18, "bold"),
            bg="#ce985f",
            fg="white",
            activebackground="#2a8f57",
            activeforeground="white",
            cursor="hand2"
        )

        self.frame.focus_set()
        self.frame.bind("<KeyPress>", self.presionar_tecla)
        self.frame.bind("<KeyRelease>", self.soltar_tecla)

        self.juego_terminado = False

        pygame.mixer.init()
        pygame.mixer.music.load("Music/musica.mp3")
        pygame.mixer.music.play(-1)
        self.sonido_hum = pygame.mixer.Sound("Music/hum.mp3")

        self.actualizar_movimiento()
        self.mover_alumnos()
        if self.dificultad in ("normal", "difficile"):
            self.mover_alumno_rebelde()
        self.actualizar_juego()
        if self.dificultad == "difficile":
            self.verificar_inspector()

        self.boton_sortir = None
        self.boton_creditos = None

    def volver(self):
        pygame.mixer.music.stop()
        self.frame.destroy()
        self.volver_a_menu_callback()

    def cargar_imagen(self, ruta, tamaño=(50, 50)):
        imagen = Image.open(ruta).resize(tamaño, Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(imagen)

    def cambiar_fondo(self, ruta):
        imagen = Image.open(ruta).resize((800, 600), Image.Resampling.LANCZOS)
        fondo = ImageTk.PhotoImage(imagen)
        self.fondo_imagen = fondo
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.fondo_imagen, tags="fondo")
        self.canvas.tag_lower("fondo")

    def crear_profesor(self):
        x, y = self.profesor_pos
        profesor_img = self.cargar_imagen(self.profesor_skin, (self.profesor_size, self.profesor_size))
        self.profesor = self.canvas.create_image(x, y, image=profesor_img)
        self.imagenes_guardadas.append(profesor_img)

    def generar_alumnos(self, cantidad):
        for alumno, _ in self.alumnos:
            self.canvas.delete(alumno)
        self.alumnos.clear()

        ruta_carpeta = os.path.join(os.getcwd(), "Images/Eleves")
        imagenes_disponibles = [
            os.path.join(ruta_carpeta, archivo) for archivo in os.listdir(ruta_carpeta)
            if archivo.lower().endswith(('.png', '.jpg', '.jpeg'))
        ]

        random.shuffle(imagenes_disponibles)

        for i, ruta_imagen in enumerate(imagenes_disponibles):
            x = random.randint(0, 780)
            y = random.randint(0, 580)
            alumno_img = self.cargar_imagen(ruta_imagen, (self.alumno_size, self.alumno_size))
            if alumno_img:
                alumno = self.canvas.create_image(x, y, image=alumno_img)
                self.imagenes_guardadas.append(alumno_img)
                self.alumnos.append((alumno, ruta_imagen))

        restantes = cantidad - len(imagenes_disponibles)
        if restantes > 0:
            for _ in range(restantes):
                x = random.randint(0, 780)
                y = random.randint(0, 580)
                ruta_imagen = random.choice(imagenes_disponibles)
                alumno_img = self.cargar_imagen(ruta_imagen, (self.alumno_size, self.alumno_size))
                if alumno_img:
                    alumno = self.canvas.create_image(x, y, image=alumno_img)
                    self.imagenes_guardadas.append(alumno_img)
                    self.alumnos.append((alumno, ruta_imagen))

    def crear_alumno_rebelde(self):
        x, y = 750, 50
        rebelde_img = self.cargar_imagen("Images/bebe.png", (self.profesor_size, self.profesor_size))
        rebelde = self.canvas.create_image(x, y, image=rebelde_img)
        self.imagenes_guardadas.append(rebelde_img)
        return rebelde
    
    def mover_profesor(self, dx, dy):
        if self.juego_terminado:
            return
    
        nuevo_x = self.profesor_pos[0] + dx
        nuevo_y = self.profesor_pos[1] + dy

        if 0 <= nuevo_x <= 850 - self.profesor_size and 0 <= nuevo_y <= 650 - self.profesor_size:
            self.canvas.move(self.profesor, dx, dy)
            self.profesor_pos[0] += dx
            self.profesor_pos[1] += dy

            if dx < 0:
                self.actualizar_imagen_profesor(self.profesor_skin_alt)
            elif dx > 0:
                self.actualizar_imagen_profesor(self.profesor_skin)

    def actualizar_imagen_profesor(self, nueva_imagen):
        profesor_img = self.cargar_imagen(nueva_imagen, (self.profesor_size, self.profesor_size))
        if profesor_img:
            self.canvas.itemconfig(self.profesor, image=profesor_img)
            self.imagenes_guardadas.append(profesor_img)

    def presionar_tecla(self, event):
        self.teclas_presionadas.add(event.keysym)

    def soltar_tecla(self, event):
        self.teclas_presionadas.discard(event.keysym)

    def actualizar_movimiento(self):
        dx, dy = 0, 0
        if "Up" in self.teclas_presionadas:
            dy -= 5
        if "Down" in self.teclas_presionadas:
            dy += 5
        if "Left" in self.teclas_presionadas:
            dx -= 5
        if "Right" in self.teclas_presionadas:
            dx += 5
        self.mover_profesor(dx, dy)
        self.frame.after(50, self.actualizar_movimiento)

    def verificar_inspector(self):
        if self.juego_terminado or self.dificultad != "difficile":
            return

        if not self.inspector_activo and random.randint(1, 10) == 7:
            self.inspector_activo = True
            self.mostrar_texto_inspector()
            self.frame.after(1000, self.mostrar_imagen_inspector)

        self.frame.after(900, self.verificar_inspector)

    def mostrar_texto_inspector(self):
        self.inspector_texto_id = self.canvas.create_text(
            400, 300, text="J'écoute des pas dans les couloirs...",
            font=("Arial", 20), fill="red"
        )
        self.frame.after(1500, self.ocultar_texto_inspector)

    def mostrar_imagen_inspector(self):
        inspector_img = self.cargar_imagen("Images/inspector.png", (80, 102))
        self.inspector_imgtk = inspector_img
        self.inspector_imagen_id = self.canvas.create_image(
            10, 590, anchor=tk.SW, image=inspector_img
        )
        self.imagen_inspector_visible = True 
        self.frame.after(2000, self.ocultar_inspector)

    def ocultar_inspector(self):
        if self.inspector_imagen_id:
            self.canvas.delete(self.inspector_imagen_id)
            self.inspector_imagen_id = None
        self.imagen_inspector_visible = False
        self.inspector_activo = False

    def ocultar_texto_inspector(self):
        if self.inspector_texto_id:
            self.canvas.delete(self.inspector_texto_id)
            self.inspector_texto_id = None

    def mover_alumnos(self):
        for alumno, tipo in self.alumnos:
            dx = random.choice([-5, 0, 5])
            dy = random.choice([-5, 0, 5])
            self.canvas.move(alumno, dx, dy)

            x1, y1, x2, y2 = self.canvas.bbox(alumno)

            if x1 < 0 or x2 > 800:
                self.canvas.move(alumno, -dx, 0)
            if y1 < 0 or y2 > 600:
                self.canvas.move(alumno, 0, -dy)

        self.frame.after(100, self.mover_alumnos)

    def animar_alumnos_felices(self):
        for alumno, _ in self.alumnos:
            self.saltar_alumno(alumno)

    def saltar_alumno(self, alumno):
        if self.juego_terminado:
            def animacion_subir():
                self.canvas.move(alumno, 0, -10)
                self.frame.after(200, animacion_bajar)

            def animacion_bajar():
                self.canvas.move(alumno, 0, 10)
                self.frame.after(200, animacion_subir)

            animacion_subir()

    def mover_alumno_rebelde(self):
        if self.dificultad not in ("normal", "difficile") or self.juego_terminado:
            return

        px, py = self.profesor_pos
        rx, ry = self.canvas.coords(self.alumno_rebelde)

        dx = 4 if px > rx else -4 if px < rx else 0
        dy = 4 if py > ry else -4 if py < ry else 0

        self.canvas.move(self.alumno_rebelde, dx, dy)

        if self.verificar_colision_rebelde():
            self.terminar_juego(perdiste=True)
            return
        
        self.frame.after(100, self.mover_alumno_rebelde)

    def verificar_colisiones(self):
        if self.juego_terminado:
            return
        x1, y1, x2, y2 = self.canvas.bbox(self.profesor)
        for alumno, tipo in self.alumnos[:]:
            ax1, ay1, ax2, ay2 = self.canvas.bbox(alumno)
            if (x1 < ax2 and x2 > ax1 and y1 < ay2 and y2 > ay1):
                if self.dificultad == "difficile" and self.imagen_inspector_visible:
                    self.terminar_juego(perdiste=True, trahison=True)
                    return
                self.canvas.delete(alumno)
                self.alumnos.remove((alumno, tipo))
                self.alumnos_restantes -= 1
                self.canvas.itemconfig(self.marcador, text=f"Élèves qui restent : {self.alumnos_restantes}", font=("Arial", 30), fill="black")
            
                if self.sonido_hum:
                    self.sonido_hum.play()

    def verificar_colision_rebelde(self):
        if self.dificultad not in ("normal", "difficile"):
            return False
        x1, y1, x2, y2 = self.canvas.bbox(self.profesor)
        rx1, ry1, rx2, ry2 = self.canvas.bbox(self.alumno_rebelde)
        return x1 < rx2 and x2 > rx1 and y1 < ry2 and y2 > ry1

    def actualizar_juego(self):
        if self.alumnos_restantes > 0:
            self.verificar_colisiones()
            self.frame.after(50, self.actualizar_juego)
        else:
            self.terminar_juego()

    def terminar_juego(self, perdiste=False, trahison=False):
        pygame.mixer.music.stop()
        self.animar_alumnos_felices()
        self.juego_terminado = True

        if trahison:
            ruta_carpeta = os.path.join(os.getcwd(), "Music/Dodin")
            archivos_mp3 = [
                archivo for archivo in os.listdir(ruta_carpeta)
                if archivo.lower().endswith('.mp3')
            ]
            if archivos_mp3:
                archivo_seleccionado = secrets.choice(archivos_mp3)
                ruta_archivo = os.path.join(ruta_carpeta, archivo_seleccionado)
                pygame.mixer.music.load(ruta_archivo)
                pygame.mixer.music.play()
                nombre_sin_extension = os.path.splitext(archivo_seleccionado)[0]
                mensaje = f"{nombre_sin_extension} !"

        elif perdiste:
            pygame.mixer.Sound("Music/risas.mp3").play()
            self.animar_alumnos_felices()
            mensaje = "T'as perdu :("

        else:
            pygame.mixer.Sound("Music/suspiro.mp3").play()
            mensaje = "Finalement silence..."

        self.texto_perdida_id = self.canvas.create_text(400, 250, text=mensaje, font=("Arial", 30), fill="black")

        self.boton_sortir = tk.Button(self.frame, text="Sortir", font=("Arial", 16), bg="#618EF2", fg="white", command=self.salir)
        self.boton_sortir.place(x=300, y=300, width=100, height=40)

        self.boton_creditos = tk.Button(self.frame, text="Crédits", font=("Arial", 16), bg="#2196F3", fg="white", command=self.mostrar_creditos)
        self.boton_creditos.place(x=420, y=300, width=100, height=40)

    def mostrar_creditos(self):
        ventana_creditos = tk.Toplevel(self.frame)
        ventana_creditos.title("Crédits")
        ventana_creditos.geometry("200x450")
        ventana_creditos.resizable(False, False)

        nombres = ["M Genty", "Armel", "Matheo", "Louis", "Thomas", "Natan", "Arthur", "Jules",
                   "Aaron", "Djibril", "Owen", "Noa", "Emanuel", "Isabella", "Angelina FC", "Google"]

        for nombre in nombres:
            tk.Label(ventana_creditos, text=nombre, font=("Arial", 12)).pack(pady=2)

    def salir(self):
        self.frame.destroy()
        self.volver_a_menu_callback()

class Aplicacion:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Potoi Potoi Potoi")
        self.root.geometry("800x600")
        self.root.resizable(False, False)
        self.root.iconbitmap("Images/icono.ico")

        fondo_img = Image.open("Images/fond1.png")
        fondo_img = fondo_img.resize((800, 600), Image.LANCZOS)
        self.fondo_imgtk = ImageTk.PhotoImage(fondo_img)

        self.fondo_label = tk.Label(self.root, image=self.fondo_imgtk)
        self.fondo_label.place(relwidth=1, relheight=1)

        self.frame_menu = tk.Frame(self.root, bg="#3bb371", bd=2)
        self.frame_menu.pack(expand=True)

        tk.Button(self.frame_menu, text="Jouer", font=("Arial", 14), width=40, height=2, command=self.mostrar_modalidades).pack(pady=10)
        tk.Button(self.frame_menu, text="Crédits", font=("Arial", 14), width=40, height=2, command=self.mostrar_creditos).pack(pady=10)
        tk.Button(self.frame_menu, text="Sortir", font=("Arial", 14), width=40, height=2, command=self.root.quit).pack(pady=10)

        self.frame_modalidades = tk.Frame(self.root, bg="#3bb371", bd=2)

        tk.Label(self.frame_modalidades, text="Sélectionnez la difficulté", font=("Arial", 16), bg="#3bb371", fg="white").pack(pady=10)

        tk.Button(self.frame_modalidades, text="Facile", font=("Arial", 14), width=40, height=2, command=lambda: self.iniciar_juego("facile")).pack(pady=5)
        tk.Button(self.frame_modalidades, text="Normal", font=("Arial", 14), width=40, height=2, command=lambda: self.iniciar_juego("normal")).pack(pady=5)
        tk.Button(self.frame_modalidades, text="Difficile", font=("Arial", 14), width=40, height=2, command=lambda: self.iniciar_juego("difficile")).pack(pady=5)

        tk.Button(self.frame_modalidades, text="Retour", command=self.mostrar_menu, font=("Arial", 14), width=40, height=2).pack(pady=10)

    def mostrar_menu(self):
        self.frame_modalidades.pack_forget()
        self.frame_menu.pack(expand=True)

    def mostrar_modalidades(self):
        self.frame_menu.pack_forget()
        self.frame_modalidades.pack(expand=True)

    def mostrar_creditos(self):
        ventana_creditos = tk.Toplevel(self.root)
        ventana_creditos.title("Crédits")
        ventana_creditos.geometry("200x450")
        ventana_creditos.resizable(False, False)

        nombres = ["M Genty", "Armel", "Matheo", "Louis", "Thomas", "Natan", "Arthur",
                   "Jules", "Aaron", "Djibril", "Owen", "Noa", "Emanuel", "Isabella", "Angelina FC", "Google"]

        for nombre in nombres:
            tk.Label(ventana_creditos, text=nombre, font=("Arial", 12)).pack(pady=2)

    def iniciar_juego(self, dificultad):
        self.frame_modalidades.pack_forget()
        self.frame_menu.pack_forget()
        self.juego = Juego(self.root, dificultad, self.volver_al_menu)
    
    def volver_al_menu(self):
        if hasattr(self, "juego"):
            self.juego.frame.destroy()
            del self.juego
        self.mostrar_menu()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = Aplicacion()
    app.run()
