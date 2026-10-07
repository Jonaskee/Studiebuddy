"""
StudieBuddy - een simpele AI-assistent met een eigen contextgeheugen (PoC).

Context die we zelf toevoegen:
  1. Rol                     -> hoe de assistent zich gedraagt
  2. Kennis                  -> context/<vak>/*.md (ECTS-fiches)
  3. Tijd / locatie          -> huidige dag, uur, semester en locatie
  4. Gebruikersgeschiedenis  -> geheugen.json (blijft bewaard tussen sessies)
  5. Sessiegegevens          -> sessie-id, starttijd en chatgeschiedenis van deze sessie

Starten: python assistent.py
"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from groq import APIStatusError, Groq

MODEL = "openai/gpt-oss-120b"
LOCATIE = "Campus, België"

MAP = Path(__file__).parent
CONTEXT_MAP = MAP / "context"
GEHEUGEN_BESTAND = MAP / "geschiedenis" / "geheugen.json"

INFO_VELDEN = ("Titularis", "Co-titularis(sen)", "Studieomvang", "Kalender", "Semester")
MAX_FICHES = 2  # gratis Groq-limiet is 8000 tokens per minuut, alle fiches samen is te veel

DAGEN = ["maandag", "dinsdag", "woensdag", "donderdag", "vrijdag", "zaterdag", "zondag"]

# Sessiegegevens: bestaan enkel zolang het programma draait
sessie = {
    "id": uuid.uuid4().hex[:8],
    "start": datetime.now(),
    "berichten": [],  # volledige chat van deze sessie
    "vragen": [],     # enkel de vragen van de gebruiker
}


def laad_geheugen():
    """Gebruikersgeschiedenis uit geheugen.json, of een nieuw profiel bij de eerste run."""
    if GEHEUGEN_BESTAND.exists():
        return json.loads(GEHEUGEN_BESTAND.read_text(encoding="utf-8"))
    naam = input("Eerste keer hier! Hoe heet je? ").strip().capitalize() or "Student"
    return {"naam": naam, "aantal_sessies": 0, "laatste_bezoek": None, "vorige_vragen": []}


def bewaar_geheugen(geheugen):
    geheugen["aantal_sessies"] += 1
    geheugen["laatste_bezoek"] = sessie["start"].strftime("%d/%m/%Y %H:%M")
    geheugen["vorige_vragen"] = (geheugen["vorige_vragen"] + sessie["vragen"])[-5:]
    GEHEUGEN_BESTAND.parent.mkdir(exist_ok=True)
    GEHEUGEN_BESTAND.write_text(json.dumps(geheugen, indent=2, ensure_ascii=False), encoding="utf-8")


def laad_vakken():
    """Elke submap van context/ is een vak, met de ECTS-fiche(s) als .md erin."""
    vakken = {}
    for vak_map in sorted(CONTEXT_MAP.iterdir()):
        if vak_map.is_dir():
            fiches = [p.read_text(encoding="utf-8") for p in sorted(vak_map.glob("*.md"))]
            vakken[vak_map.name.replace("_", " ")] = "\n\n".join(fiches)
    return vakken


def overzicht(vakken):
    """Korte samenvatting per vak (titularis, studiepunten, semester) uit de fiches."""
    blokken = []
    for naam, fiche in vakken.items():
        info = [regel.replace("*", "").strip() for regel in fiche.splitlines()
                if any(regel.startswith(f"* **{veld}:**") for veld in INFO_VELDEN)]
        blokken.append(f"### {naam}\n" + "\n".join(f"- {i}" for i in info))
    return "\n\n".join(blokken)


def relevante_vakken(vakken):
    """Vakken die in de laatste 2 vragen genoemd worden (nieuwste vraag eerst)."""
    gevonden = []
    for vraag in reversed(sessie["vragen"][-2:]):
        for naam in vakken:
            woorden = [w for w in naam.lower().split() if len(w) > 3]
            if naam not in gevonden and any(w in vraag.lower() for w in woorden):
                gevonden.append(naam)
    return gevonden[:MAX_FICHES]


def bouw_context(geheugen, context_aan):
    """Stelt de system prompt samen. Zonder context krijgt het model niets extra."""
    if not context_aan:
        return "Je bent een behulpzame assistent."

    nu = datetime.now()
    semester = 1 if nu.month >= 9 or nu.month == 1 else 2
    vakken = laad_vakken()
    fiches = "\n\n".join(vakken[naam] for naam in relevante_vakken(vakken)) or "(geen specifiek vak gevraagd)"
    vorige_vragen = "\n".join(f"- {v}" for v in geheugen["vorige_vragen"]) or "- (nog geen)"

    return f"""## Rol
Je bent StudieBuddy, een studieassistent voor een 3de-jaarsstudent.
Antwoord kort (1 à 2 zinnen) in het Nederlands en enkel op basis van de info hieronder.
Gebruik gewone tekst zonder opmaak (geen * of **), want het antwoord verschijnt in een terminal.
Spreek de student aan bij naam.

## Tijd en locatie
Vandaag is het {DAGEN[nu.weekday()]} {nu:%d/%m/%Y}, het is {nu:%H:%M}.
We zitten in semester {semester}.
Locatie: {LOCATIE}

## Gebruiker
Naam: {geheugen['naam']}
Aantal eerdere sessies: {geheugen['aantal_sessies']}
Laatste bezoek: {geheugen['laatste_bezoek'] or 'eerste bezoek'}
Vragen uit vorige sessies:
{vorige_vragen}

## Sessie
Sessie-id: {sessie['id']}
Gestart om: {sessie['start']:%H:%M}
Aantal vragen deze sessie: {len(sessie['vragen'])}

## Vakken van de student (overzicht)
{overzicht(vakken)}

## Volledige ECTS-fiche van het gevraagde vak
{fiches}"""


def vraag_ai(client, vraag, systeem, context_aan):
    nieuw = {"role": "user", "content": vraag}
    # Zonder context sturen we ook de chatgeschiedenis niet mee, enkel de vraag
    berichten = sessie["berichten"] + [nieuw] if context_aan else [nieuw]

    antwoord = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": systeem}] + berichten,
    ).choices[0].message.content

    sessie["berichten"] += [nieuw, {"role": "assistant", "content": antwoord}]
    return antwoord


def main():
    load_dotenv(MAP / ".env")
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key.startswith("plak"):
        raise SystemExit("Zet eerst je Groq API key in het .env bestand.")
    client = Groq(api_key=api_key)

    geheugen = laad_geheugen()
    context_aan = True

    groet = "welkom terug! Ik" if geheugen["aantal_sessies"] > 0 else "ik"
    print(f"StudieBuddy: Hallo {geheugen['naam']}, {groet} ben je StudieBuddy. Wat wil je weten?\n")

    try:
        while True:
            vraag = input("Jij: ").strip()
            if not vraag:
                continue
            if vraag == "/stop":
                break
            if vraag.startswith("/context"):
                keuze = vraag.removeprefix("/context").strip()
                context_aan = {"aan": True, "uit": False}.get(keuze, not context_aan)
                print(f"[Context staat nu {'AAN' if context_aan else 'UIT'}]\n")
                continue
            if vraag == "/toon":
                print(bouw_context(geheugen, context_aan) + "\n")
                continue

            sessie["vragen"].append(vraag)
            try:
                antwoord = vraag_ai(client, vraag, bouw_context(geheugen, context_aan), context_aan)
            except APIStatusError as fout:
                antwoord = f"[Groq-fout {fout.status_code}] Even te veel gevraagd, probeer het over een minuutje opnieuw."
            print(f"StudieBuddy: {antwoord}\n")
    except (KeyboardInterrupt, EOFError):
        print()

    bewaar_geheugen(geheugen)
    print("Sessie opgeslagen in geschiedenis/geheugen.json. Tot later!")


if __name__ == "__main__":
    main()
