"""
StudieBuddy - webversie met een simpele chatinterface.

Hergebruikt alle logica uit assistent.py; enkel de in- en uitvoer verloopt
via de browser in plaats van de terminal.

Starten: python app.py  ->  http://127.0.0.1:5000
"""

import json
import os

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory
from groq import APIStatusError, Groq

from assistent import GEHEUGEN_BESTAND, MAP, bouw_context, sessie, vraag_ai

load_dotenv(MAP / ".env")
api_key = os.getenv("GROQ_API_KEY")
if not api_key or api_key.startswith("plak"):
    raise SystemExit("Zet eerst je Groq API key in het .env bestand.")
client = Groq(api_key=api_key)

# laad_geheugen() vraagt de naam via input(), dat kan niet in de browser
if GEHEUGEN_BESTAND.exists():
    geheugen = json.loads(GEHEUGEN_BESTAND.read_text(encoding="utf-8"))
else:
    geheugen = {"naam": "Student", "aantal_sessies": 0, "laatste_bezoek": None, "vorige_vragen": []}

context_aan = True
app = Flask(__name__, static_folder="static")


def recente_vragen():
    """Laatste 5 vragen: uit vorige sessies + deze sessie (geheugen zelf blijft ongewijzigd voor de prompt)."""
    return (geheugen["vorige_vragen"] + sessie["vragen"])[-5:]


def bewaar():
    """Zoals bewaar_geheugen(), maar veilig om na elke vraag op te roepen (1 serverrun = 1 sessie)."""
    nieuw = {
        **geheugen,
        "aantal_sessies": geheugen["aantal_sessies"] + 1,
        "laatste_bezoek": sessie["start"].strftime("%d/%m/%Y %H:%M"),
        "vorige_vragen": recente_vragen(),
    }
    GEHEUGEN_BESTAND.parent.mkdir(exist_ok=True)
    GEHEUGEN_BESTAND.write_text(json.dumps(nieuw, indent=2, ensure_ascii=False), encoding="utf-8")


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/api/info")
def info():
    return jsonify(
        naam=geheugen["naam"],
        terug=geheugen["aantal_sessies"] > 0,
        vorige_vragen=recente_vragen(),
        berichten=sessie["berichten"],
        context_aan=context_aan,
    )


@app.post("/api/chat")
def chat():
    global context_aan
    data = request.get_json(force=True)
    vraag = (data.get("vraag") or "").strip()
    if not vraag:
        return jsonify(fout="Lege vraag"), 400
    context_aan = bool(data.get("context", True))

    sessie["vragen"].append(vraag)
    try:
        antwoord = vraag_ai(client, vraag, bouw_context(geheugen, context_aan), context_aan)
    except APIStatusError as fout:
        antwoord = f"[Groq-fout {fout.status_code}] Even te veel gevraagd, probeer het over een minuutje opnieuw."
    bewaar()
    return jsonify(antwoord=antwoord, vorige_vragen=recente_vragen())


if __name__ == "__main__":
    app.run(debug=False)
