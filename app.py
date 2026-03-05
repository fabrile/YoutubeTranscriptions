import os
import json
import re
import urllib.request
from flask import Flask, request, jsonify, send_from_directory
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled, VideoUnavailable

app = Flask(__name__, static_folder="static")

# Directory where transcripts will be saved
TRANSCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "transcripts")
os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)

# Proxy config (leído desde variables de entorno para no exponer credenciales)
# Formato esperado: http://usuario:password@host:puerto
PROXY_URL = os.environ.get("PROXY_URL", None)
PROXIES = {"http": PROXY_URL, "https": PROXY_URL} if PROXY_URL else None


def fetch_video_metadata(video_id: str) -> dict:
    """
    Fetches video title and channel name from YouTube's oEmbed API.
    Returns a dict with 'title' and 'channel'. Falls back to empty strings on error.
    """
    url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return {
                "title": data.get("title", ""),
                "channel": data.get("author_name", ""),
                "channel_url": data.get("author_url", ""),
            }
    except Exception:
        return {"title": "", "channel": "", "channel_url": ""}


def extract_video_id(input_str: str) -> str:
    """
    Accepts either a plain video ID or a full YouTube URL and returns the video ID.
    """
    input_str = input_str.strip()
    # Try to extract from URL patterns
    patterns = [
        r"(?:v=|youtu\.be/|shorts/)([A-Za-z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, input_str)
        if match:
            return match.group(1)
    # Assume it's already a plain video ID (11 chars alphanumeric / - / _)
    if re.match(r"^[A-Za-z0-9_-]{11}$", input_str):
        return input_str
    return input_str  # Return as-is and let the API handle the error


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/transcript", methods=["POST"])
def get_transcript():
    data = request.get_json(force=True)
    raw_input = data.get("video_id", "").strip()

    if not raw_input:
        return jsonify({"error": "No se proporcionó ningún código o URL de video."}), 400

    video_id = extract_video_id(raw_input)

    try:
        # Instantiate the API (required in v1.2+)
        ytt_api = YouTubeTranscriptApi(proxies=PROXIES) if PROXIES else YouTubeTranscriptApi()
        transcript_list = ytt_api.list(video_id)

        transcript = None
        language_used = None

        # Priority: manual Spanish > manual English > auto Spanish > auto English > any
        for lang in ["es", "en"]:
            try:
                transcript = transcript_list.find_manually_created_transcript([lang])
                language_used = lang + " (manual)"
                break
            except Exception:
                pass

        if transcript is None:
            for lang in ["es", "en"]:
                try:
                    transcript = transcript_list.find_generated_transcript([lang])
                    language_used = lang + " (auto-generado)"
                    break
                except Exception:
                    pass

        if transcript is None:
            # Grab whatever is available
            for t in transcript_list:
                transcript = t
                language_used = t.language_code
                break

        if transcript is None:
            return jsonify({"error": "No se encontró ninguna transcripción disponible para este video."}), 404

        raw_transcript = transcript.fetch()

        # Fetch metadata from oEmbed
        metadata = fetch_video_metadata(video_id)

        # Build structured data
        result = {
            "video_id": video_id,
            "video_url": f"https://www.youtube.com/watch?v={video_id}",
            "title": metadata["title"],
            "channel": metadata["channel"],
            "channel_url": metadata["channel_url"],
            "language": language_used,
            "segments": [
                {
                    "start": round(entry.start, 3),
                    "duration": round(entry.duration, 3),
                    "text": entry.text,
                }
                for entry in raw_transcript
            ],
            "full_text": " ".join(entry.text for entry in raw_transcript),
        }

        # Save to JSON file
        filename = f"{video_id}.json"
        filepath = os.path.join(TRANSCRIPTS_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        return jsonify({
            "success": True,
            "video_id": video_id,
            "language": language_used,
            "segments_count": len(result["segments"]),
            "saved_as": filename,
            "transcript": result,
        })

    except VideoUnavailable:
        return jsonify({"error": f"El video '{video_id}' no está disponible o no existe."}), 404
    except TranscriptsDisabled:
        return jsonify({"error": "Las transcripciones están deshabilitadas para este video."}), 403
    except NoTranscriptFound:
        return jsonify({"error": "No se encontró ninguna transcripción para este video."}), 404
    except Exception as e:
        return jsonify({"error": f"Error inesperado: {str(e)}"}), 500


@app.route("/api/saved", methods=["GET"])
def list_saved():
    """Return a list of all saved transcript JSON files."""
    files = []
    for fname in sorted(os.listdir(TRANSCRIPTS_DIR), reverse=True):
        if fname.endswith(".json"):
            fpath = os.path.join(TRANSCRIPTS_DIR, fname)
            size = os.path.getsize(fpath)
            files.append({"filename": fname, "video_id": fname[:-5], "size_bytes": size})
    return jsonify(files)


if __name__ == "__main__":
    import os as _os
    port = int(_os.environ.get("PORT", 5000))
    print("🎬 YouTube Transcript Capturer")
    print(f"📁 Transcripts guardadas en: {TRANSCRIPTS_DIR}")
    print(f"🌐 Abre http://127.0.0.1:{port} en tu navegador")
    app.run(debug=False, host="0.0.0.0", port=port)
