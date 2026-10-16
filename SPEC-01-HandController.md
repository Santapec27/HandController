# SPEC-01: Background Vision-Based Hand Controller (Windows)

## 1. Visión General
Servicio en segundo plano para Windows que captura video desde la cámara web con OpenCV[cite: 9], procesa puntos clave articulares con MediaPipe Hands y traduce interacciones espaciales a eventos nativos de mouse y teclado mediante `pydirectinput`. 

El servicio corre minimizado en la bandeja del sistema (`pystray`), no despliega ventanas de consola y desacopla la captura de video del hilo principal mediante concurrencia (`threading`).

---

## 2. Dependencias y Entorno
* **Gestor de entorno:** Miniconda (Python 3.10).
* **Visión por computador:** `opencv-python`, `mediapipe`, `numpy`[cite: 2, 5].
* **Emulación de entradas OS:** `pydirectinput`, `pyautogui`.
* **Bandeja del sistema:** `pystray`, `Pillow`[cite: 8].

---

## 3. Estructura del Repositorio
```text
hand_controller/
│── assets/
│   └── icon.ico
│── core/
│   │── __init__.py
│   │── camera.py          # Hilo de captura continua sin buffer lag
│   │── detector.py        # Inferencia MediaPipe Hands
│   │── gestures.py        # ROI, suavizado EMA y distancias
│   └── input_emitter.py   # Despacho de clics y movimiento
│── tray/
│   │── __init__.py
│   └── tray_app.py        # Menú contextual pystray
│── config.py              # Umbrales, resolución y estados
│── environment.yml        # Configuración conda
│── requirements.txt       # Dependencias pip
└── main.pyw               # Entry point sin consola
```

---

## 4. Tareas de Implementación

### Task 1: Pipeline de Cámara Concurrente (`core/camera.py`)
* Implementar la clase `ThreadedCamera` usando `threading.Thread` para leer fotogramas continuamente en segundo plano y descartar buffers antiguos[cite: 13].
* Configurar `cv2.VideoCapture(0, cv2.CAP_DSHOW)`[cite: 9] a 640x480 o 1280x720 para balancear latencia y precisión.

### Task 2: Detección y Extracción de Puntos Clave (`core/detector.py`)
* Instanciar `mediapipe.solutions.hands.Hands` con `max_num_hands=1`, `min_detection_confidence=0.7` y `min_tracking_confidence=0.7`.
* Convertir el fotograma de BGR a RGB antes de la inferencia (`cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)`)[cite: 7, 8].

### Task 3: Normalización, ROI y Suavizado (`core/gestures.py`)
* Delimitar una Región de Interés (ROI) virtual dentro del encuadre (márgenes del 20% al 80%)[cite: 5, 7].
* Escalar la posición $(x, y)$ del índice (`INDEX_FINGER_TIP`, ID 8) a la resolución del monitor mediante `np.interp`[cite: 5].
* Mitigar el temblor (*jitter*) aplicando filtro EMA:
  $$x_{\text{smooth}} = \alpha \cdot x_{\text{actual}} + (1 - \alpha) \cdot x_{\text{previo}} \quad (\alpha \approx 0.25)$$
* Calcular la distancia euclidiana entre el pulgar (ID 4) y el índice (ID 8) para activar el clic izquierdo si la distancia cae por debajo del umbral de activación.

### Task 4: Emisión de Eventos (`core/input_emitter.py`)
* Mapear las coordenadas filtradas a `pydirectinput.moveTo(int(x), int(y))`.
* Implementar una máquina de estados para evitar eventos continuos de pulsación: emitir `pydirectinput.mouseDown()` al cruzar el umbral y `pydirectinput.mouseUp()` al separarse.

### Task 5: Bandeja del Sistema y Salida Limpia (`tray/tray_app.py` y `main.pyw`)
* Crear el menú con `pystray.Icon`:
  * *Activar / Pausar Tracking* (cambia una bandera atómica booleana).
  * *Salir* (cierra hilos y libera la cámara con `cap.release()`)[cite: 9].
* El archivo principal debe usar la extensión `.pyw` para que el intérprete de Windows no abra la ventana de comandos (`pythonw.exe`).

---

## 5. Criterios de Aceptación
* El cursor debe responder con una latencia perceptible inferior a **40 ms**.
* No debe levantarse ninguna ventana en la barra de tareas de Windows mientras el programa rastrea en segundo plano.
* La cámara debe liberarse limpiamente al pulsar "Salir" desde el icono de la bandeja del sistema[cite: 9].