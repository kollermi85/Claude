# Vorlage für neue Projektnotizen

Beim Anlegen eines neuen Projekts als `<Projekt>.md` in den neuen
Ordner `10 Projekte/Arbeit/<Projekt>/` bzw. `10 Projekte/Privat/<Projekt>/` hochladen (`text/markdown`,
`disableConversionToGoogleType: true`). `<Projekt>`, das Datum und die
Stichworte ersetzen. Basiert auf `90 Vorlagen/Vorlage Projekt.md` des Nutzers,
ergänzt um `aliases` und `stichworte` für die automatische Zuordnung.

```markdown
---
typ: Projekt
bereich: <Arbeit|Privat>
status: aktiv
start: <JJJJ-MM-TT>
aliases: [<Projekt>]
stichworte: [<Adresse>, <EZ/KG>, <Projektcode>, <Bauherr>, <Architekt>]
---

# <Projekt>

> **Stichworte** (oben im Feld `stichworte`): Adresse, Straßenname, EZ/KG, Projektcode,
> Bauherr, Architekt – alles, woran man Dokumente zu diesem Projekt erkennt.
> Claude ordnet angehängte Dateien anhand dieser Begriffe automatisch hier ein.

## Eckdaten
- **Liegenschaft / Adresse:** 
- **EZ / KG / Grundstück:** 
- **Nutzung / Flächen:** 
- **Phase:** Akquisition / Planung / Einreichung / Bau / Verwertung
- **Nachhaltigkeit:** Zertifizierung, Energiekennwerte, Taxonomie

## Beteiligte
- Planer: 
- Konsulenten: 
- Behörde: 

## Meilensteine
- [ ] 

## Offene Punkte
- [ ] 

## Protokolle & Notizen
Umgewandelte Dokumente liegen in diesem Ordner und verlinken über `projekt: "[[<Projekt>]]"` hierher – siehe Rückverweise (Backlinks).
```

Bei **Privatprojekten** die Abschnitte an das Thema anpassen: „Eckdaten“ und
„Beteiligte“ frei formulieren (z. B. Budget, Anbieter, Fristen), die
immobilienspezifischen Felder (EZ/KG, Phase, Konsulenten) weglassen.
