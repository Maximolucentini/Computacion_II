# Trabajo Práctico 1 - Análisis Biométrico Concurrente
Nombre: Máximo Lucentini

## Estructura del Trabajo

- `Tareas.py`: contiene la generación de muestras biométricas, procesos concurrentes, análisis por señal y la construcción de la blockchain.
- `verificar_cadena.py`: verifica la integridad de la blockchain y genera un reporte.
- `TP_1/blockchain.json`: archivo generado con los bloques validados.
- `TP_1/reporte.txt`: resumen estadístico de la cadena y alertas detectadas.


## Descripción del desarrollo

### Tarea 1: Generación y analisis concurrente

Se simulan 60 muestras biométricas, una por segundo, usando `random`. Cada muestra contiene:

- `frecuencia`: entre 60 y 210
- `presion`: lista [sistólica, diastólica] con sistólica entre 110 y 220
- `oxigeno`: entre 85 y 100
> **Nota**: Los rangos definidos originalmente por el enunciado no permiten generar ningún valor que dispare una alerta (ya que los máximos están por debajo de los umbrales definidos). Por eso, para validar el funcionamiento del sistema de alertas y la construcción de bloques, decidí ampliar ligeramente los rangos de generación. Esto me permitió observar alertas reales (`True`) y confirmar que el sistema responde correctamente ante anomalías.


Las muestras se envían mediante `Pipe` a 3 procesos hijos:

- Analizador de frecuencia
- Analizador de presión
- Analizador de oxígeno

Cada analizador implementa una ventana móvil de 30 valores y calcula:

- Media
- Desviación estándar

Estos resultados se envían a un proceso verificador por medio de `Queue`, cumpliendo con los requisitos de IPC.
Utilicé `multiprocessing.Pipe` para la comunicación entre el generador y cada analizador, y `Queue` para compartir los resultados con el verificador.
Se maneja la salida limpia con `Ctrl+C` usando el módulo `signal`.

### Tarea 2: Verificador y Blockchain

El proceso verificador:

- Recibe los resultados
- Evalúa condiciones de alerta:
  - Frecuencia media ≥ 200
  - Presión sistólica media ≥ 200
  - Oxígeno fuera de 90 a 100
- Crea un bloque con los datos, un timestamp y el hash del bloque anterior (tipo blockchain)
- Calcula el hash SHA-256 del bloque actual
- Guarda todo en `blockchain.json` dentro de `TP_1/`

Usé `hashlib` y `json` para implementar una estructura tipo blockchain como forma de auditar los datos biométricos en tiempo real. Esto permite detectar corrupciones o alteraciones.

### Tarea 3: Verificación e informe

Se implementa `verificar_cadena.py` que:

- Lee `TP_1/blockchain.json`
- Verifica integridad de hashes y encadenamiento
- Cuenta alertas y bloques corruptos
- Calcula promedios de cada señal
- Genera `TP_1/reporte.txt` con los resultados

simular una auditoría externa a la captura de datos.

## Instrucciones de ejecución

1. Ejecutar el sistema principal:

   ```bash
   python Tarea_1.py
   ```

   Esto generará `TP_1/blockchain.json`

2. Ejecutar el verificador para generar el informe:

   ```bash
   python verificar_cadena.py
   ```

   Esto generará `TP_1/reporte.txt`

