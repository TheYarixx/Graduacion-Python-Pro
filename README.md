# EcoEvolución: laboratorio de ecosistemas

Aplicación de escritorio en **Python** para un proyecto de graduación. Simula plantas, herbívoros y carnívoros con ecuaciones tipo Lotka-Volterra y Runge-Kutta de cuarto orden (RK4).

## Incluye

- Interfaz gráfica: no se usan menús de consola.
- Iniciar, pausar, reiniciar y cambiar la velocidad.
- Vista animada y gráfica de población en tiempo real.
- Escenarios de equilibrio, sobrepastoreo, ausencia de depredadores y ecosistema frágil.
- Modificación de poblaciones, capacidad de carga y tasas ecológicas.
- Eventos: sequía, incendio, contaminación, deforestación y caza furtiva.
- Conservación: reforestación, limpieza, áreas protegidas e investigación.
- Salud ecológica (0–100%), alertas y detección de extinción/colapso.

> La salud ecológica es un indicador didáctico basado en vegetación, diversidad, hábitat, equilibrio y contaminación; no reemplaza una medición de campo.

## Ejecutarlo en otro PC (Windows)

1. Instala [Python 3.10 o posterior](https://www.python.org/downloads/) y marca **Add Python to PATH**.
2. En GitHub descarga el repositorio usando **Code → Download ZIP** y descomprímelo.
3. Abre PowerShell en la carpeta del proyecto.
4. Ejecuta:

   ```powershell
   python -m pip install -r requirements.txt
   python main.py
   ```

Python normalmente instala Tkinter; si la ventana no abre, reinstala Python y activa el componente **tcl/tk and IDLE**.

## Demostración sugerida

Carga **Equilibrio sostenible**, activa la simulación y aplica un evento ambiental. Antes del colapso, usa las acciones de conservación y explica el cambio en la salud, el hábitat y las gráficas.
