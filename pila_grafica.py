"""
Visualizador gráfico de una PILA (Stack / LIFO) con tkinter.
No necesita instalar nada: tkinter viene incluido con Python.
Ejecutar:  python pila_grafica.py
"""
import tkinter as tk

# ---------- Paleta (tema oscuro) ----------
BG = "#0f172a"
PANEL = "#1e293b"
TEXT = "#e2e8f0"
MUTED = "#64748b"
ACCENT = "#38bdf8"
OK, WARN, ERR = "#4ade80", "#facc15", "#f87171"
COLORS = ["#f87171", "#fb923c", "#facc15", "#4ade80",
          "#2dd4bf", "#38bdf8", "#818cf8", "#e879f9"]


# ---------- Funciones de animación (easing) ----------
def ease_out_bounce(t):
    n, d = 7.5625, 2.75
    if t < 1 / d:
        return n * t * t
    if t < 2 / d:
        t -= 1.5 / d
        return n * t * t + 0.75
    if t < 2.5 / d:
        t -= 2.25 / d
        return n * t * t + 0.9375
    t -= 2.625 / d
    return n * t * t + 0.984375


def ease_in_out(t):
    return 3 * t * t - 2 * t * t * t


class PilaApp:
    CAP = 8                       # capacidad máxima de la pila
    W, H, GAP = 220, 48, 6        # tamaño de cada bloque y separación
    CX, BASE = 240, 560           # centro horizontal y suelo de la pila
    SPAWN_Y = 62                  # donde aparece / desaparece cada bloque

    def __init__(self, root):
        self.root = root
        root.title("Pila (Stack) · LIFO")
        root.configure(bg=BG)
        root.resizable(False, False)

        self.stack = []           # cada elemento: dict con value, rect, text, y, color
        self.busy = False
        self.contador_color = 0

        self.canvas = tk.Canvas(root, width=480, height=600, bg=BG,
                                highlightthickness=0)
        self.canvas.pack()

        self.dibujar_contenedor()
        self.crear_controles()
        self.actualizar_info()
        self.mensaje("Escribe un valor y pulsa PUSH para apilarlo", MUTED)

    # ---------- Dibujo estático ----------
    def slot_y(self, i):
        return self.BASE - (i + 1) * (self.H + self.GAP)

    def dibujar_contenedor(self):
        c, W = self.canvas, self.W
        top = self.BASE - self.CAP * (self.H + self.GAP) - 10
        self.x_izq, self.x_der = self.CX - W / 2 - 10, self.CX + W / 2 + 10
        self.paredes = [
            c.create_line(self.x_izq, top, self.x_izq, self.BASE + 4,
                          fill=ACCENT, width=4, capstyle="round"),
            c.create_line(self.x_der, top, self.x_der, self.BASE + 4,
                          fill=ACCENT, width=4, capstyle="round"),
            c.create_line(self.x_izq, self.BASE + 4, self.x_der, self.BASE + 4,
                          fill=ACCENT, width=4, capstyle="round"),
        ]
        c.create_text(self.CX, 26, text="PILA  ·  LIFO", fill=TEXT,
                      font=("Segoe UI", 18, "bold"))
        c.create_text(self.CX, 46, text="Last In, First Out", fill=MUTED,
                      font=("Segoe UI", 10))

    def crear_controles(self):
        panel = tk.Frame(self.root, bg=PANEL, pady=12)
        panel.pack(fill="x")

        fila1 = tk.Frame(panel, bg=PANEL)
        fila1.pack()
        self.entry = tk.Entry(fila1, width=12, font=("Segoe UI", 14),
                              justify="center", bg=BG, fg=TEXT,
                              insertbackground=TEXT, relief="flat")
        self.entry.pack(side="left", padx=8, ipady=4)
        self.entry.bind("<Return>", lambda e: self.push())
        self.entry.focus()

        self.botones = [
            self.boton(fila1, "PUSH", OK, self.push),
            self.boton(fila1, "POP", ERR, self.pop),
            self.boton(fila1, "PEEK", WARN, self.peek),
            self.boton(fila1, "LIMPIAR", MUTED, self.limpiar),
        ]
        self.lbl_msg = tk.Label(panel, text="", bg=PANEL, font=("Segoe UI", 11))
        self.lbl_msg.pack(pady=(10, 0))

    def boton(self, parent, texto, color, comando):
        b = tk.Button(parent, text=texto, command=comando, bg=color, fg=BG,
                      font=("Segoe UI", 10, "bold"), relief="flat",
                      activebackground=TEXT, cursor="hand2", padx=10, pady=4)
        b.pack(side="left", padx=4)
        b.bind("<Enter>", lambda e: b.config(bg=TEXT))      # efecto hover
        b.bind("<Leave>", lambda e: b.config(bg=color))
        return b

    # ---------- Info dinámica (puntero TOP, índices, tamaño) ----------
    def actualizar_info(self):
        c = self.canvas
        c.delete("info")
        # índices a la derecha de cada bloque
        for i in range(len(self.stack)):
            c.create_text(self.x_der + 14, self.slot_y(i) + self.H / 2,
                          text=f"[{i}]", fill=MUTED, anchor="w",
                          font=("Consolas", 11), tags="info")
        # puntero TOP a la izquierda
        if self.stack:
            y = self.slot_y(len(self.stack) - 1) + self.H / 2
            c.create_text(self.x_izq - 10, y, text="TOP ➜", fill=WARN,
                          anchor="e", font=("Segoe UI", 13, "bold"), tags="info")
        else:
            c.create_text(self.CX, self.BASE - 30, text="(pila vacía)",
                          fill=MUTED, font=("Segoe UI", 12, "italic"), tags="info")
        # tamaño
        c.create_text(20, 580, anchor="w", fill=TEXT, tags="info",
                      text=f"Tamaño: {len(self.stack)} / {self.CAP}",
                      font=("Segoe UI", 11, "bold"))

    def mensaje(self, texto, color=TEXT):
        self.lbl_msg.config(text=texto, fg=color)

    def set_busy(self, valor):
        self.busy = valor
        for b in self.botones:
            b.config(state="disabled" if valor else "normal")

    # ---------- Bloques y animación ----------
    def crear_bloque(self, valor, y, color):
        x0, x1 = self.CX - self.W / 2, self.CX + self.W / 2
        rect = self.canvas.create_rectangle(x0, y, x1, y + self.H,
                                            fill=color, outline="")
        txt = self.canvas.create_text(self.CX, y + self.H / 2, text=valor,
                                      fill=BG, font=("Segoe UI", 16, "bold"))
        return {"value": valor, "rect": rect, "text": txt, "y": y, "color": color}

    def mover(self, bloque, destino, ease, frames, al_terminar):
        inicio = bloque["y"]

        def frame(n=1):
            nueva = inicio + (destino - inicio) * ease(n / frames)
            dy = nueva - bloque["y"]
            self.canvas.move(bloque["rect"], 0, dy)
            self.canvas.move(bloque["text"], 0, dy)
            bloque["y"] = nueva
            if n < frames:
                self.root.after(15, frame, n + 1)
            else:
                al_terminar()

        frame()

    def parpadear(self, ids, color, veces=3):
        """Hace parpadear el contorno de unos items (para PEEK y errores)."""
        def paso(n):
            for i in ids:
                self.canvas.itemconfig(i, fill=color if n % 2 == 0 else ACCENT)
            if n < veces * 2:
                self.root.after(120, paso, n + 1)
        paso(0)

    # ---------- Operaciones de la pila ----------
    def push(self):
        if self.busy:
            return
        if len(self.stack) >= self.CAP:
            self.parpadear(self.paredes, ERR)
            self.mensaje("¡Stack Overflow! La pila está llena", ERR)
            return
        valor = self.entry.get().strip()[:10]
        if not valor:
            self.mensaje("Escribe un valor antes de hacer PUSH", WARN)
            self.entry.focus()
            return
        self.entry.delete(0, "end")
        color = COLORS[self.contador_color % len(COLORS)]
        self.contador_color += 1

        bloque = self.crear_bloque(valor, self.SPAWN_Y, color)
        self.set_busy(True)

        def listo():
            self.stack.append(bloque)
            self.actualizar_info()
            self.set_busy(False)
            self.mensaje(f"PUSH → se apiló '{valor}' en la cima", OK)

        self.mover(bloque, self.slot_y(len(self.stack)), ease_out_bounce, 35, listo)

    def pop(self):
        if self.busy:
            return
        if not self.stack:
            self.parpadear(self.paredes, ERR)
            self.mensaje("¡Stack Underflow! La pila está vacía", ERR)
            return
        bloque = self.stack.pop()
        self.actualizar_info()
        self.set_busy(True)

        def listo():
            self.canvas.delete(bloque["rect"])
            self.canvas.delete(bloque["text"])
            self.set_busy(False)
            self.mensaje(f"POP → salió '{bloque['value']}' (el último en entrar)", ERR)

        self.mover(bloque, self.SPAWN_Y, ease_in_out, 25, listo)

    def peek(self):
        if self.busy:
            return
        if not self.stack:
            self.mensaje("PEEK → no hay nada que mirar, la pila está vacía", WARN)
            return
        tope = self.stack[-1]
        self.mensaje(f"PEEK → la cima es '{tope['value']}' (no se elimina)", WARN)

        def paso(n):
            self.canvas.itemconfig(tope["rect"],
                                   outline=TEXT if n % 2 == 0 else "", width=4)
            if n < 6:
                self.root.after(150, paso, n + 1)
        paso(0)

    def limpiar(self):
        if self.busy:
            return
        for b in self.stack:
            self.canvas.delete(b["rect"])
            self.canvas.delete(b["text"])
        self.stack.clear()
        self.actualizar_info()
        self.mensaje("Pila vaciada", MUTED)


if __name__ == "__main__":
    ventana = tk.Tk()
    PilaApp(ventana)
    ventana.mainloop()
