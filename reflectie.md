# Reflectienota StudieBuddy

*Trends in AI*

*Jonas Lemmens & Kemal Yilmaz · 2026*

## Wat we gebouwd hebben
StudieBuddy is een kleine proof of concept: een chatbot die vragen beantwoordt over onze eigen vakken. Een algemeen taalmodel (`openai/gpt-oss-120b` via de gratis Groq-API) weet niets over onze opleiding. Wij geven het die kennis zelf mee via de ECTS-fiches in `context/` en een geheugen in `geschiedenis/geheugen.json`. Er is een terminalversie (`assistent.py`) en een webversie (`app.py`) die dezelfde logica gebruikt.

Alle context komt samen in één system prompt die bij elke vraag opnieuw wordt opgebouwd, in vijf lagen:

1. **Rol**: kort antwoorden, in het Nederlands, de student bij naam aanspreken.
2. **Kennis**: de ECTS-fiches.
3. **Tijd en locatie**: dag, uur, semester en locatie.
4. **Gebruikersgeschiedenis**: naam, aantal sessies, laatste bezoek en de laatste 5 vragen.
5. **Sessiegegevens**: sessie-id, starttijd en de chat van de huidige sessie.

## Bevindingen

### 1. Meer context is niet altijd beter
Onze eerste reflex was om alle fiches mee te sturen. Samen zijn dat ongeveer 52 kB tekst, terwijl de gratis tier maar 8.000 tokens per minuut toelaat. We liepen dus snel tegen Groq-fouten aan. De oplossing was zelf kiezen welke context meegaat:

- Altijd een kort overzicht van elk vak (titularis, studiepunten, semester).
- De volledige fiche enkel voor vakken die in de laatste 2 vragen genoemd worden.
- Maximaal 2 fiches tegelijk (`MAX_FICHES = 2`).

Dit is in feite handmatige context-selectie. 

Het belangrijkste dat het ons leerde was dat de juist context meegeven het belangerijkste deel is van een chatbot

### 2. Privacy en kosten
Het geheugen staat lokaal, maar elke vraag gaat samen met naam en vorige vragen naar een externe API. Voor ECTS-fiches is dat geen probleem; met gevoeligere gegevens (punten, persoonlijke planning) zou dat wel een aandachtspunt zijn. De API-sleutel staat in `.env` en wordt via `.gitignore` uit de repository gehouden.

## Volgende stap: MCP
Onze uitwerking staat in `mcp.md` en op slide 7–8. Kort: een WebUntis-MCP-server met tools als `get_rooster(datum)`, `get_volgende_les()` en `get_wijzigingen()` zou het lessenrooster live aan StudieBuddy geven. Dat lost meerdere bevindingen tegelijk op:

- **Actuele context** in plaats van statische bestanden (bevinding 5).
- **Minder tokens**, omdat het model zelf opvraagt wat het nodig heeft (bevinding 2 en 3).
- **Uitbreidbaar**: een agenda of deadlines toevoegen is een extra MCP-server, zonder de code van StudieBuddy te wijzigen.
- **Proactief**: StudieBuddy kan waarschuwen als een les uitvalt, in plaats van te wachten tot we iets vragen.

Dit voorstel is theoretisch.

## Wat we meenemen
- **Context is king.** Hetzelfde model wordt pas nuttig zodra het de juiste, actuele context krijgt.
- **Context engineering is kiezen.** Door de tokenlimiet moesten we nadenken over wat relevant is. Die beperking was eigenlijk de meest leerrijke bevinding van het project.
- **Statische context veroudert.** Bestanden en een JSON-geheugen werken voor een PoC, maar een echte assistent heeft live bronnen nodig. MCP is daar een gestandaardiseerde manier voor.
- **Eenvoudig beginnen werkt.** Met één Python-script, een map Markdown-bestanden en een JSON-bestand konden we snel aantonen wat context doet, en zagen we daardoor ook duidelijk waar de grenzen liggen.

## Gebruikte bronnen
- **Groq**: LLM-provider voor StudieBuddy, met het model `openai/gpt-oss-120b` via de gratis API. Documentatie en limieten: https://console.groq.com/docs
- **Claude Opus (Anthropic)**: gebruikt als hulp bij het schrijven en debuggen van de code (`assistent.py`, `app.py`, `static/index.html`) en bij het nalezen en verbeteren van de teksten (README, `mcp.md`, presentatie en deze reflectienota). https://claude.ai
- **ECTS-fiches AP Hogeschool 2026-2027**: bron van de vakinformatie in `context/`.
