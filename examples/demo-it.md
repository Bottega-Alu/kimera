Title: Stato della piattaforma Atlante
Subtitle: Memo di stato, sprint 24 (1-14 settembre)
Project: Atlante
Author: Squadra Piattaforma
Date: 2026-09-08
Label: Memo di stato — dati di esempio
Lang: it
Paper: A4
Confidential: Documento dimostrativo. Tutti i dati sono inventati e non descrivono alcun sistema reale.

# Stato della piattaforma Atlante

!!! warning "Dati di esempio"
    Questo documento serve a mostrare come Kimera 2.0 impagina un memo reale:
    intestazione, tabelle, codice, citazioni, callout ed elenchi. Nomi, numeri,
    date e incidenti sono **inventati**. Non usarlo come fonte per decisioni.

## Sintesi

Lo sprint 24 chiude con dodici attività completate su quindici pianificate. Le
tre attività rimaste aperte riguardano tutte la migrazione dell'archivio storico
e sono state spostate allo sprint 25 con la stessa priorità: nessuna di esse
blocca il rilascio previsto per il 22 settembre.

Il tema principale del periodo è stato l'incidente del 4 settembre sul servizio
di ricerca, risolto in due ore e quaranta minuti. L'analisi post-incidente è
allegata in fondo al documento sotto forma di elenco di azioni correttive; due
delle quattro azioni sono già chiuse.

- **Rilascio previsto:** 22 settembre, invariato.
- **Rischio principale:** capacità dell'archivio storico durante la migrazione.
- **Decisione richiesta:** conferma della finestra di manutenzione notturna.

## Stato dei servizi

| Servizio | Ambiente | Stato | Disponibilità 30 gg | Nota |
|---|---|---|---:|---|
| Gateway API | produzione | Operativo | 99,95% | nessun intervento nel periodo |
| Ricerca | produzione | Operativo | 99,71% | incidente del 4 settembre |
| Archivio storico | produzione | Degradato | 99,40% | migrazione in corso |
| Notifiche | produzione | Operativo | 99,99% | coda sotto soglia |
| Gateway API | collaudo | Operativo | — | allineato a produzione |
| Archivio storico | collaudo | In migrazione | — | dati sintetici |

La disponibilità è calcolata sulle sonde esterne, con finestra mobile di trenta
giorni e granularità di un minuto. Il valore dell'archivio storico riflette la
degradazione volontaria durante le finestre di migrazione notturne, non un
guasto.

## Lavori completati

| Riferimento | Attività | Esito | Rilasciato |
|---|---|---|---|
| ATL-412 | Riscrittura del client di indicizzazione | Completata | 2 settembre |
| ATL-415 | Cache di secondo livello sulle ricerche | Completata | 3 settembre |
| ATL-418 | Limitatore di frequenza per chiave API | Completata | 5 settembre |
| ATL-421 | Migrazione schema notifiche, fase 1 | Completata | 8 settembre |
| ATL-423 | Tracciamento distribuito sul gateway | Completata | 9 settembre |
| ATL-427 | Rotazione automatica dei segreti | Completata | 11 settembre |
| ATL-430 | Riduzione dell'immagine di base a 84 MB | Completata | 12 settembre |
| ATL-431 | Test di carico riproducibili | Completata | 12 settembre |

## Questioni aperte

| Riferimento | Descrizione | Gravità | Assegnataria | Scadenza |
|---|---|---|---|---|
| ATL-433 | Copia dell'archivio storico oltre la finestra | Alta | R. Bianchi | 19 settembre |
| ATL-436 | Riconciliazione dei documenti duplicati | Media | L. Ferrari | 25 settembre |
| ATL-439 | Metriche della coda notifiche incomplete | Bassa | M. Conti | sprint 26 |

!!! danger "ATL-433 — copia oltre la finestra"
    La copia completa dell'archivio storico richiede oggi circa sei ore e
    quaranta minuti contro le quattro ore della finestra concordata. Senza una
    delle due mitigazioni elencate più sotto, la migrazione non entra nella
    finestra del 19 settembre.

## Incidente del 4 settembre

Alle 09:12 il servizio di ricerca ha iniziato a restituire errori 503 su circa
il 40% delle richieste. La causa è stata un indice riaperto in sola lettura da
un processo di manutenzione che non rilasciava il lock. Il ripristino è avvenuto
alle 11:52 dopo il riavvio controllato dei tre nodi di indicizzazione.

Azioni correttive:

1. **Chiusa** — timeout esplicito sul lock di manutenzione (ATL-441).
2. **Chiusa** — allarme sul tasso di errori 503 oltre l'1% per due minuti.
3. **Aperta** — prova di ripristino programmata mensile, prevista per ottobre.
4. **Aperta** — revisione della procedura di manutenzione con il fornitore.

> Il problema non è stato l'indice riaperto, ma il fatto che nessuno se ne sia
> accorto per undici minuti. La correzione utile è l'allarme, non il lock.
>
> — verbale della revisione post-incidente, 5 settembre

## Nota tecnica: limitatore di frequenza

Il limitatore introdotto con ATL-418 usa una finestra scorrevole per chiave API,
con contatori tenuti in memoria condivisa e riversati ogni cinque secondi. Il
comportamento in caso di superamento è il rifiuto immediato con `429` e
intestazione `Retry-After`, mai l'accodamento.

```python
LIMITE_PREDEFINITO = 600      # richieste al minuto, per chiave
FINESTRA = 60.0               # secondi

def consenti(chiave: str, adesso: float, contatori: dict) -> bool:
    finestra_inizio = adesso - FINESTRA
    eventi = [t for t in contatori.get(chiave, ()) if t >= finestra_inizio]
    if len(eventi) >= LIMITE_PREDEFINITO:
        contatori[chiave] = eventi
        return False
    eventi.append(adesso)
    contatori[chiave] = eventi
    return True
```

Le chiavi di servizio interne restano escluse dal limite; l'elenco è definito
nella configurazione dell'ambiente e non nel codice, così da poterlo modificare
senza un nuovo rilascio.

## Indicatori del periodo

| Indicatore | Sprint 23 | Sprint 24 | Variazione |
|---|---:|---:|---:|
| Attività completate | 11 | 12 | +1 |
| Tempo medio di risposta ricerca | 214 ms | 168 ms | −21,5% |
| Errori 5xx per milione | 340 | 91 | −73,2% |
| Copertura dei test | 71,4% | 74,8% | +3,4 pt |
| Dimensione immagine di base | 141 MB | 84 MB | −40,4% |

!!! success "Effetto della cache di secondo livello"
    La riduzione del tempo medio di risposta è quasi interamente attribuibile ad
    ATL-415. Il valore misurato sul 95° percentile passa da 906 ms a 402 ms.

## Rischi e mitigazioni

!!! note "Capacità dell'archivio storico"
    Due mitigazioni possibili per ATL-433, da scegliere entro il 16 settembre:
    copia incrementale in tre notti consecutive, oppure estensione della finestra
    a sette ore in una sola notte con fermo del servizio di ricerca.

| Rischio | Probabilità | Impatto | Mitigazione |
|---|---|---|---|
| Migrazione fuori finestra | Media | Alto | copia incrementale, ATL-433 |
| Regressione sui duplicati | Bassa | Medio | riconciliazione, ATL-436 |
| Fornitore indisponibile | Bassa | Basso | procedura manuale documentata |

## Prossimi passi

1. Confermare la finestra di manutenzione entro il **16 settembre**.
2. Completare la copia dell'archivio storico entro il **19 settembre**.
3. Congelare il codice il **20 settembre**, rilascio il **22 settembre**.
4. Chiudere le due azioni correttive aperte entro fine ottobre.

## Riferimenti

- Registro delle decisioni architetturali, voce 2026-09-05, sezione «lock di
  manutenzione»: <https://esempio.test/atlante/decisioni/2026-09-05-lock-di-manutenzione-del-servizio-di-ricerca>
- Cruscotto delle sonde esterne, vista «trenta giorni».
- Verbale della revisione post-incidente del 5 settembre.

Termini usati in questo documento:

Finestra di manutenzione
:   Intervallo concordato in cui è ammessa una degradazione del servizio.

Copia incrementale
:   Trasferimento dei soli blocchi modificati rispetto alla copia precedente.
