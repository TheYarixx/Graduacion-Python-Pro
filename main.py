"""EcoEvolución: laboratorio gráfico de ecosistemas, hecho en Python."""
from __future__ import annotations

import random
import tkinter as tk
from dataclasses import dataclass
from tkinter import messagebox, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


@dataclass
class Parametros:
    plantas: float = 850
    herbivoros: float = 110
    carnivoros: float = 22
    capacidad: float = 1200
    crecimiento: float = .85
    pastoreo: float = .0015
    eficiencia_herbivoro: float = .45
    mortalidad_herbivoro: float = .18
    caza: float = .0075
    eficiencia_carnivoro: float = .40
    mortalidad_carnivoro: float = .15


ESCENARIOS = {
    "Equilibrio sostenible": Parametros(),
    "Sobrepastoreo": Parametros(plantas=500, herbivoros=320, carnivoros=2, capacidad=900,
                                 crecimiento=.50, pastoreo=.0035, eficiencia_herbivoro=.35,
                                 caza=.004, eficiencia_carnivoro=.30, mortalidad_carnivoro=.25),
    "Sin depredadores": Parametros(plantas=750, herbivoros=80, carnivoros=0, capacidad=1100,
                                    crecimiento=.75, pastoreo=.0018, eficiencia_herbivoro=.42,
                                    caza=0, eficiencia_carnivoro=0),
    "Ecosistema frágil": Parametros(plantas=360, herbivoros=155, carnivoros=9, capacidad=650,
                                    crecimiento=.42, pastoreo=.003, mortalidad_carnivoro=.23),
}


class Ecosistema:
    """Modelo Lotka-Volterra tritrófico con clima y acciones humanas."""
    UMBRAL_EXTINCION = 1.0

    def __init__(self, parametros: Parametros) -> None:
        self.parametros = parametros
        self.reiniciar()

    def reiniciar(self) -> None:
        p = self.parametros
        self.P, self.H, self.C = p.plantas, p.herbivoros, p.carnivoros
        self.dia, self.lluvia, self.contaminacion, self.habitat, self.investigacion = 0, 1., 0., 1., 0.
        self.historial = [(0, self.P, self.H, self.C, self.salud())]

    def capacidad_efectiva(self) -> float:
        return max(20., self.parametros.capacidad * self.habitat * (.55 + .45 * self.lluvia))

    def _derivadas(self, p: float, h: float, c: float) -> tuple[float, float, float]:
        q = self.parametros
        p, h, c = max(0., p), max(0., h), max(0., c)
        crecimiento = q.crecimiento * self.lluvia * (1 - .70 * self.contaminacion)
        return (
            crecimiento * p * (1 - p / self.capacidad_efectiva()) - q.pastoreo * p * h,
            q.eficiencia_herbivoro * q.pastoreo * p * h - q.mortalidad_herbivoro * (1 + .22 * self.contaminacion) * h - q.caza * h * c,
            q.eficiencia_carnivoro * q.caza * h * c - q.mortalidad_carnivoro * (1 + .18 * self.contaminacion) * c,
        )

    def avanzar(self, dias: int = 1, dt: float = .05) -> None:
        """Resuelve cada día mediante Runge-Kutta de cuarto orden (RK4)."""
        for _ in range(dias):
            for _ in range(round(1 / dt)):
                estado = (self.P, self.H, self.C)
                k1 = self._derivadas(*estado)
                k2 = self._derivadas(*(v + dt * x / 2 for v, x in zip(estado, k1)))
                k3 = self._derivadas(*(v + dt * x / 2 for v, x in zip(estado, k2)))
                k4 = self._derivadas(*(v + dt * x for v, x in zip(estado, k3)))
                self.P, self.H, self.C = (max(0., v + dt / 6 * (a + 2*b + 2*c + d))
                                          for v, a, b, c, d in zip(estado, k1, k2, k3, k4))
            self.dia += 1
            self.historial.append((self.dia, self.P, self.H, self.C, self.salud()))

    def especies_vivas(self) -> int:
        return sum(x >= self.UMBRAL_EXTINCION for x in (self.P, self.H, self.C))

    def salud(self) -> float:
        """Índice didáctico: no equivale a una medición ecológica de campo."""
        vegetacion = min(1., self.P / self.capacidad_efectiva())
        diversidad = self.especies_vivas() / 3
        equilibrio = min(1., self.H / max(1., self.P * .22)) if self.P else 0
        return max(0., min(100., 100 * (.38*vegetacion + .30*diversidad + .17*self.habitat + .15*equilibrio) * (1 - .45*self.contaminacion)))

    def estado(self) -> tuple[str, str]:
        faltantes = [n for n, x in (("plantas", self.P), ("herbívoros", self.H), ("carnívoros", self.C)) if x < 1]
        if self.P < 1 or len(faltantes) >= 2:
            return "COLAPSO ECOLÓGICO", "#ef4444"
        if faltantes:
            return "EXTINCIÓN: " + ", ".join(faltantes).upper(), "#f97316"
        if self.salud() < 40:
            return "RIESGO CRÍTICO", "#ef4444"
        if self.salud() < 70:
            return "RIESGO AMBIENTAL", "#f59e0b"
        return "ECOSISTEMA SALUDABLE", "#22c55e"

    def aplicar_evento(self, evento: str) -> str:
        if evento == "Sequía":
            self.lluvia = max(.25, self.lluvia - .35); return "Sequía: disminuye el agua y el crecimiento vegetal."
        if evento == "Incendio":
            self.P *= .65; self.habitat = max(.20, self.habitat - .12); return "Incendio: se perdió vegetación y hábitat."
        if evento == "Contaminación":
            self.contaminacion = min(1., self.contaminacion + .25); return "Contaminación: baja el crecimiento y aumenta mortalidad."
        if evento == "Deforestación":
            self.P *= .80; self.habitat = max(.15, self.habitat - .20); return "Deforestación: se redujeron hábitat y productores."
        self.C *= .65; return "Caza furtiva: disminuyeron los depredadores."

    def conservar(self, accion: str) -> str:
        bono = 1 + .35 * self.investigacion
        if accion == "Plantar árboles":
            self.P += 90 * bono; self.habitat = min(1., self.habitat + .04 * bono); return "Reforestación: aumentaron productores y hábitat."
        if accion == "Limpiar contaminación":
            self.contaminacion = max(0., self.contaminacion - .22 * bono); return "Limpieza ambiental: disminuyó la contaminación."
        if accion == "Crear área protegida":
            self.habitat = min(1., self.habitat + .12 * bono); self.C += 3 * bono; return "Área protegida: se recupera hábitat y se protege fauna."
        self.investigacion = min(1., self.investigacion + .15); return "Investigación: las futuras acciones serán más eficaces."


class AplicacionEcoEvolucion(tk.Tk):
    FONDO, PANEL, TEXTO, SUAVE = "#0b1220", "#162033", "#edf7f0", "#9fb0c7"

    def __init__(self) -> None:
        super().__init__()
        self.title("EcoEvolución | Laboratorio de Ecosistemas")
        self.geometry("1400x860"); self.minsize(1180, 720); self.configure(bg=self.FONDO)
        self.eco, self.en_marcha, self.variables = Ecosistema(Parametros()), False, {}
        self._estilo(); self._interfaz(); self.actualizar()

    def _estilo(self) -> None:
        s = ttk.Style(self); s.theme_use("clam")
        s.configure("TFrame", background=self.FONDO); s.configure("Panel.TFrame", background=self.PANEL, padding=14)
        s.configure("TLabel", background=self.PANEL, foreground=self.TEXTO, font=("Segoe UI", 10))
        s.configure("Titulo.TLabel", background=self.FONDO, foreground=self.TEXTO, font=("Segoe UI", 22, "bold"))
        s.configure("Sub.TLabel", background=self.FONDO, foreground=self.SUAVE)
        s.configure("TButton", font=("Segoe UI", 10, "bold"), padding=7)
        s.configure("TEntry", fieldbackground="#233149", foreground=self.TEXTO)

    def panel(self, parent: tk.Widget, **kw: object) -> ttk.Frame:
        return ttk.Frame(parent, style="Panel.TFrame", **kw)

    def _interfaz(self) -> None:
        head = ttk.Frame(self, padding=(20, 14)); head.pack(fill="x")
        ttk.Label(head, text="EcoEvolución", style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(head, text="Simula, observa y protege un ecosistema. Hecho completamente en Python.", style="Sub.TLabel").pack(anchor="w")
        cuerpo = ttk.Frame(self, padding=(20, 0, 20, 18)); cuerpo.pack(fill="both", expand=True)
        cuerpo.columnconfigure(1, weight=1); cuerpo.rowconfigure(0, weight=1)
        self._controles(cuerpo).grid(row=0, column=0, sticky="nsw", padx=(0, 12))
        self._centro(cuerpo).grid(row=0, column=1, sticky="nsew")
        self._lateral(cuerpo).grid(row=0, column=2, sticky="nse", padx=(12, 0))

    def _controles(self, parent: ttk.Frame) -> ttk.Frame:
        f = self.panel(parent, width=270); f.grid_propagate(False)
        ttk.Label(f, text="Configuración", font=("Segoe UI", 13, "bold")).pack(anchor="w")
        self.escenario = tk.StringVar(value="Equilibrio sostenible")
        ttk.Combobox(f, textvariable=self.escenario, values=list(ESCENARIOS), state="readonly", width=26).pack(fill="x", pady=8)
        ttk.Button(f, text="Cargar escenario", command=self.cargar).pack(fill="x")
        ttk.Separator(f).pack(fill="x", pady=12)
        campos = [("plantas", "Plantas iniciales"), ("herbivoros", "Herbívoros iniciales"), ("carnivoros", "Carnívoros iniciales"), ("capacidad", "Capacidad de carga (K)"), ("crecimiento", "Crecimiento de plantas"), ("pastoreo", "Tasa de pastoreo"), ("caza", "Tasa de depredación")]
        for nombre, texto in campos:
            ttk.Label(f, text=texto).pack(anchor="w", pady=(4, 0))
            v = tk.StringVar(value=str(getattr(self.eco.parametros, nombre))); self.variables[nombre] = v
            ttk.Entry(f, textvariable=v).pack(fill="x")
        ttk.Button(f, text="Aplicar datos y reiniciar", command=self.aplicar).pack(fill="x", pady=(12, 5))
        ttk.Label(f, text="Los parámetros no visibles mantienen valores del escenario elegido.", foreground=self.SUAVE, wraplength=235).pack(anchor="w")
        return f

    def _centro(self, parent: ttk.Frame) -> ttk.Frame:
        f = ttk.Frame(parent)
        mundo = self.panel(f); mundo.pack(fill="x")
        fila = ttk.Frame(mundo, style="Panel.TFrame"); fila.pack(fill="x")
        ttk.Label(fila, text="Vista del mundo", font=("Segoe UI", 13, "bold")).pack(side="left")
        self.estado_lbl = tk.Label(fila, bg=self.PANEL, font=("Segoe UI", 11, "bold")); self.estado_lbl.pack(side="right")
        self.lienzo = tk.Canvas(mundo, height=245, highlightthickness=0); self.lienzo.pack(fill="x", pady=(8, 0))
        fila = ttk.Frame(mundo, style="Panel.TFrame"); fila.pack(fill="x", pady=(10, 0))
        self.inicio = ttk.Button(fila, text="▶ Iniciar", command=self.alternar); self.inicio.pack(side="left")
        ttk.Button(fila, text="↺ Reiniciar", command=self.reiniciar).pack(side="left", padx=6)
        ttk.Label(fila, text="Velocidad:").pack(side="left", padx=(14, 4)); self.velocidad = tk.StringVar(value="1 día")
        ttk.Combobox(fila, textvariable=self.velocidad, values=["1 día", "3 días", "7 días"], state="readonly", width=8).pack(side="left")
        self.dia_lbl = ttk.Label(fila, text="Día 0"); self.dia_lbl.pack(side="right")
        g = self.panel(f); g.pack(fill="both", expand=True, pady=(12, 0))
        ttk.Label(g, text="Evolución de poblaciones", font=("Segoe UI", 13, "bold")).pack(anchor="w")
        self.fig = Figure(figsize=(7, 3.5), dpi=100, facecolor=self.PANEL); self.ax = self.fig.add_subplot(111)
        self.grafico = FigureCanvasTkAgg(self.fig, master=g); self.grafico.get_tk_widget().pack(fill="both", expand=True)
        return f

    def _lateral(self, parent: ttk.Frame) -> ttk.Frame:
        f = ttk.Frame(parent, width=285); f.grid_propagate(False)
        indicadores = self.panel(f); indicadores.pack(fill="x")
        ttk.Label(indicadores, text="Salud del ecosistema", font=("Segoe UI", 13, "bold")).pack(anchor="w")
        self.salud_var = tk.StringVar(); ttk.Label(indicadores, textvariable=self.salud_var, font=("Segoe UI", 25, "bold"), foreground="#4ade80").pack(anchor="w")
        self.progreso = ttk.Progressbar(indicadores, maximum=100, length=240); self.progreso.pack(fill="x")
        self.metricas = tk.StringVar(); ttk.Label(indicadores, textvariable=self.metricas, justify="left").pack(anchor="w", pady=(10, 0))
        acciones = self.panel(f); acciones.pack(fill="x", pady=(12, 0)); ttk.Label(acciones, text="Acciones de conservación", font=("Segoe UI", 13, "bold")).pack(anchor="w")
        for a in ("Plantar árboles", "Limpiar contaminación", "Crear área protegida", "Investigar soluciones"):
            ttk.Button(acciones, text=a, command=lambda x=a: self.accion(x)).pack(fill="x", pady=(7, 0))
        eventos = self.panel(f); eventos.pack(fill="x", pady=(12, 0)); ttk.Label(eventos, text="Provocar evento ambiental", font=("Segoe UI", 13, "bold")).pack(anchor="w")
        self.evento = tk.StringVar(value="Sequía")
        ttk.Combobox(eventos, textvariable=self.evento, values=["Sequía", "Incendio", "Contaminación", "Deforestación", "Caza furtiva"], state="readonly", width=24).pack(fill="x", pady=(7, 5))
        ttk.Button(eventos, text="Aplicar evento", command=self.evento_aplicar).pack(fill="x")
        self.log = tk.Text(f, height=8, bg=self.PANEL, fg=self.TEXTO, wrap="word", relief="flat", font=("Segoe UI", 9), padx=10, pady=8); self.log.pack(fill="both", expand=True, pady=(12, 0))
        self.registrar("Bienvenido. Modifica valores o carga un escenario.")
        return f

    def cargar(self) -> None:
        self.eco = Ecosistema(Parametros(**ESCENARIOS[self.escenario.get()].__dict__)); self.sincronizar(); self.pausar(); self.registrar(f"Escenario cargado: {self.escenario.get()}."); self.actualizar()

    def sincronizar(self) -> None:
        for n, v in self.variables.items(): v.set(str(getattr(self.eco.parametros, n)))

    def aplicar(self) -> None:
        try:
            valores = {n: float(v.get().replace(",", ".")) for n, v in self.variables.items()}
            if any(x < 0 for x in valores.values()) or valores["capacidad"] <= 0 or valores["crecimiento"] <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("Dato inválido", "Usa números no negativos. La capacidad y el crecimiento deben ser mayores que cero."); return
        for n, x in valores.items(): setattr(self.eco.parametros, n, x)
        self.reiniciar("Datos personalizados aplicados.")

    def pausar(self) -> None:
        self.en_marcha = False; self.inicio.config(text="▶ Iniciar")

    def reiniciar(self, mensaje: str = "Simulación reiniciada.") -> None:
        self.pausar(); self.eco.reiniciar(); self.registrar(mensaje); self.actualizar()

    def alternar(self) -> None:
        self.en_marcha = not self.en_marcha; self.inicio.config(text="⏸ Pausar" if self.en_marcha else "▶ Iniciar")
        if self.en_marcha: self.ciclo()

    def ciclo(self) -> None:
        if not self.en_marcha: return
        self.eco.avanzar(int(self.velocidad.get().split()[0])); self.actualizar()
        if "COLAPSO" in self.eco.estado()[0]:
            self.pausar(); self.registrar("El mundo colapsó. Reinicia o evita el riesgo antes de continuar."); return
        self.after(420, self.ciclo)

    def accion(self, a: str) -> None:
        self.registrar(self.eco.conservar(a)); self.actualizar()

    def evento_aplicar(self) -> None:
        self.registrar(self.eco.aplicar_evento(self.evento.get())); self.actualizar()

    def registrar(self, texto: str) -> None:
        self.log.insert("end", f"• Día {self.eco.dia}: {texto}\n"); self.log.see("end")

    def actualizar(self) -> None:
        salud = self.eco.salud(); estado, color = self.eco.estado()
        self.estado_lbl.config(text=estado, fg=color); self.dia_lbl.config(text=f"Día {self.eco.dia}")
        self.salud_var.set(f"{salud:.0f}%"); self.progreso["value"] = salud
        self.metricas.set(f"Plantas: {self.eco.P:,.0f}\nHerbívoros: {self.eco.H:,.0f}\nCarnívoros: {self.eco.C:,.0f}\n\nHábitat: {self.eco.habitat*100:.0f}%\nContaminación: {self.eco.contaminacion*100:.0f}%\nLluvia: {self.eco.lluvia*100:.0f}%\nInvestigación: {self.eco.investigacion*100:.0f}%")
        self.dibujar_mundo(salud); self.dibujar_grafico()

    def dibujar_mundo(self, salud: float) -> None:
        # Antes del primer render Tkinter puede reportar un ancho de 1 px.
        # El mínimo evita rangos inválidos al crear la vista inicial.
        w, h = max(400, self.lienzo.winfo_width()), 245
        fondo = "#164e3d" if salud >= 70 else "#66520e" if salud >= 40 else "#57222b"
        self.lienzo.configure(bg=fondo); self.lienzo.delete("all"); random.seed(self.eco.dia)
        for _ in range(min(80, int(self.eco.P / 18))):
            x, y = random.randint(8, w-8), random.randint(35, h-8); self.lienzo.create_oval(x-3, y-3, x+3, y+3, fill="#55d37a", outline="")
        for _ in range(min(35, int(self.eco.H / 5))):
            x, y = random.randint(15, w-15), random.randint(45, h-15); self.lienzo.create_oval(x-5, y-3, x+5, y+3, fill="#e8f0f5", outline="#94a3b8")
        for _ in range(min(18, int(self.eco.C))):
            x, y = random.randint(15, w-15), random.randint(45, h-15); self.lienzo.create_polygon(x-7, y+5, x, y-7, x+7, y+5, fill="#f97316", outline="")
        self.lienzo.create_text(12, 14, anchor="w", text="Plantas ●   Herbívoros ●   Depredadores ▲", fill="#f8fafc", font=("Segoe UI", 9, "bold"))

    def dibujar_grafico(self) -> None:
        t, p, h, c, _ = zip(*self.eco.historial[-180:]); ax = self.ax; ax.clear(); ax.set_facecolor(self.PANEL)
        ax.plot(t, p, color="#55d37a", label="Plantas", linewidth=2.2); ax.plot(t, h, color="#78c7ee", label="Herbívoros", linewidth=2); ax.plot(t, c, color="#fb923c", label="Carnívoros", linewidth=2)
        ax.axhline(self.eco.capacidad_efectiva(), color="#facc15", linestyle="--", linewidth=1, label="Capacidad efectiva")
        ax.set_xlabel("Días", color=self.SUAVE); ax.set_ylabel("Población", color=self.SUAVE); ax.tick_params(colors=self.SUAVE, labelsize=8); ax.grid(alpha=.16, linestyle=":")
        for borde in ax.spines.values(): borde.set_color("#334155")
        leyenda = ax.legend(loc="upper right", fontsize=8, frameon=False)
        for texto in leyenda.get_texts(): texto.set_color(self.TEXTO)
        self.fig.tight_layout(pad=1.2); self.grafico.draw_idle()


if __name__ == "__main__":
    AplicacionEcoEvolucion().mainloop()
