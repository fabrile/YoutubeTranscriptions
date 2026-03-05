# 🎬 Capturador de Transcripciones de YouTube

Una aplicación web local que extrae la transcripción de cualquier video de YouTube, la muestra en pantalla y la guarda automáticamente como archivo JSON.

## ¿Qué hace?

- Acepta el **ID del video** (ej. `rkZzg7Vowao`) o la **URL completa** de YouTube.
- Busca la transcripción con prioridad: español manual → inglés manual → español auto-generado → inglés auto-generado → cualquier idioma disponible.
- Obtiene los metadatos del video (título y canal) vía la API oEmbed de YouTube.
- **Guarda el resultado** en `transcripts/<video_id>.json`.
- Presenta la transcripción en dos vistas: **segmentos con tiempo** y **texto completo**.
- Lista todos los archivos JSON guardados previamente y permite recargarlos.

## Estructura del proyecto

```
Transcripciones de Youtube/
├── app.py              # Servidor Flask (backend + API REST)
├── static/
│   └── index.html      # Interfaz web (frontend)
├── transcripts/        # Archivos JSON generados (se crea automáticamente)
├── venv/               # Entorno virtual de Python
└── README.md
```

## Requisitos

- Python 3.8 o superior
- Conexión a internet (para consultar YouTube)

## Instalación

### 1. Clonar / abrir el proyecto

```bash
cd "Transcripciones de Youtube"
```

### 2. Crear y activar el entorno virtual

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install flask youtube-transcript-api
```

## Cómo correrlo

```bash
source venv/bin/activate
python app.py
```

La terminal mostrará:

```
🎬 YouTube Transcript Capturer
📁 Transcripts guardadas en: .../transcripts
🌐 Abre http://127.0.0.1:5000 en tu navegador
```

Abrí **http://127.0.0.1:5000** en el navegador, pegá el ID o URL de un video y hacé clic en **Capturar**.

## API REST

| Método | Endpoint          | Descripción                                                          |
| ------ | ----------------- | -------------------------------------------------------------------- |
| `POST` | `/api/transcript` | Descarga la transcripción de un video. Body: `{ "video_id": "..." }` |
| `GET`  | `/api/saved`      | Lista los archivos JSON guardados en `transcripts/`.                 |

### Ejemplo de respuesta (`/api/transcript`)

```json
{
  "video_id": "rkZzg7Vowao",
  "video_url": "https://www.youtube.com/watch?v=rkZzg7Vowao",
  "title": "Título del video",
  "channel": "Nombre del canal",
  "channel_url": "https://www.youtube.com/@canal",
  "language": "es (manual)",
  "segments": [{ "start": 0.0, "duration": 4.5, "text": "Hola a todos..." }],
  "full_text": "Hola a todos ..."
}
```

## Detener el servidor

Presioná `Ctrl + C` en la terminal donde corre `python app.py`.
