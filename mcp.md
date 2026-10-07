# Reflectie: hoe MCP StudieBuddy zou verbeteren

## Uitbereiding via MCP?
Een MCP-server biedt tools aan (bv. "haal lesrooster op") en de AI-toepassing beslist zelf wanneer ze er een nodig heeft.

## Waar StudieBuddy nu tekortschiet
Alle context zit in bestanden die ik zelf maak (ECTS-fiches, `geheugen.json`, een vaste locatie). StudieBuddy weet welke vakken ik heb, maar niet wanneer. Een vraag als "welk vak heb ik vandaag?" kan het dus niet beantwoorden. Bovendien stuur ik veel tekst mee bij elke vraag, waardoor ik tegen de gratis limiet van 8000 tokens per minuut aanloop.

## Idee: een WebUntis-MCP (theoretisch)
WebUntis is de app waarin ik mijn lessenrooster zie. Een MCP-server ervoor zou het rooster live aan StudieBuddy geven, met tools zoals:
- `get_rooster(datum)`: de lessen van een dag
- `get_volgende_les()`: de eerstvolgende les
- `get_wijzigingen()`: uitgevallen lessen en lokaalwijzigingen

Dan werken vragen als "Welk vak heb ik vandaag?" en "Moet ik morgen naar school?" wel.

**Meldingen:** de server zou elke avond het rooster van morgen ophalen en een bericht sturen wanneer ik naar school moet, of meteen als een les uitvalt. StudieBuddy wordt zo proactief en wacht niet meer tot ik iets vraag.

## Wat MCP zou verbeteren
1. **Actuele context:** het rooster komt live uit WebUntis en niet uit een bestand dat verouderd raakt.
2. **Minder tokens:** het model vraagt enkel op wat het nodig heeft, in plaats van alle context mee te sturen.
3. **Echte tijd en locatie:** het echte rooster en lokaal vervangen de vaste tekst "Campus".
4. **Uitbreidbaar:** een nieuwe bron (agenda, deadlines) is een extra MCP-server en de code van StudieBuddy blijft hetzelfde.

## Conclusie
Met bestanden en een JSON-geheugen beantwoordt StudieBuddy vragen over de inhoud van mijn vakken. Met een WebUntis-MCP weet het ook wanneer ik ze heb en kan het me waarschuwen. Daardoor wordt het een assistent die meedenkt.
