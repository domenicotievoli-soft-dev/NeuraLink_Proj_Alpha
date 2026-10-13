# NeuraLink - Clinical Management System

Applicazione web per il monitoraggio e la gestione clinica dei pazienti affetti da Sclerosi Multipla (SM), con possibilità di ampliamento a tutte le malattie neurodegenerative caratterizzate da iter clinici e pattern di controllo simili alla SM. 

Il sistema si proietta verso implementazioni future quali l'integrazione di strumenti di AI comparativa per risonanze magnetiche (MRI) e diagnostica avanzata, con l'obiettivo di ottimizzare lo screening, la raccolta dati e supportare attivamente la ricerca e la prevenzione della malattia stessa.

---

## 1. Contesto Clinico e Parametri Diagnostici

### La Sclerosi Multipla (SM)
La Sclerosi Multipla è una malattia neurodegenerativa ed autoimmune del sistema nervoso centrale. Si caratterizza per la demielinizzazione e la formazione di lesioni (o placche) nella sostanza bianca encefalica e midollare, che interrompono la corretta conduzione degli impulsi nervosi. Il decorso è imprevedibile e variabile da paziente a paziente, rendendo fondamentale un tracciamento quantitativo continuativo nel tempo.

### Parametri Monitorati in NeuraLink
Per valutare la progressione della patologia e l'efficacia delle terapie farmacologiche, la piattaforma traccia ad ogni visita due indicatori fondamentali:

1. **Punteggio EDSS (Expanded Disability Status Scale)**:
   * **Cos'è**: È la scala standard internazionale usata dai neurologi per valutare il livello di disabilità neurologica globale causato dalla SM.
   * **Range**: Va da **0.0** (esame neurologico perfettamente normale) a **10.0** (morte dovuta alla malattia), con incrementi di 0.5 punti.
   * **Significato**: Valori inferiori a 4.0 indicano una disabilità lieve che non compromette la deambulazione, mentre punteggi superiori a 4.0 evidenziano una progressiva limitazione dell'autonomia e della mobilità.

2. **Volume delle Lesioni ($mm^3$)**:
   * **Cos'è**: Il carico lesionale volumetrico cumulativo misurato tramite Risonanza Magnetica Encefalica/Midollare (MRI).
   * **Significato**: Un aumento del volume lesionale nel tempo indica la comparsa di nuove placche o l'espansione di quelle preesistenti, costituendo un biomarker diretto dell'attività infiammatoria e neurodegenerativa della patologia.

---

## 2. Analisi del Progetto e Architettura

### Architettura del Database
Il database relazionale (`ms_track_db`) adotta una relazione **1 a Molti (1:N)** tra le tabelle `pazienti` e `visite`:
- **Paziente**: Codice identificativo univoco (`id`), età, anno di diagnosi, linea terapeutica farmacologica.
- **Visita**: Identificativo visita, data del controllo, punteggio `edss`, carico lesionale volumetrico (`volume_lesioni`), note cliniche e riferimento al paziente (`paziente_id`).
- **Integrità Relazionale**: La chiave esterna `visite(paziente_id)` è configurata con `ON DELETE CASCADE`: la cancellazione di un paziente rimuove automaticamente tutto il suo storico visite associato, evitando dati orfani.

### Gestione dei Ruoli e Sicurezza
- **Medici**: Hanno accesso completo alla dashboard, alla ricerca dei pazienti, alla registrazione di nuovi profili, all'inserimento delle visite e all'eliminazione delle schede cliniche.
- **Pazienti**: Accedono in sola lettura alla propria area riservata per consultare la terapia assegnata, le informazioni anagrafiche e lo storico delle visite svolte.
- **Sicurezza**: Le password sono salvate sotto forma di hash crittografico tramite `Werkzeug` (`scrypt`/`pbkdf2`) e le sessioni web sono firmate digitalmente da Flask.

---

## 3. Tecnologie Utilizzate
- **Linguaggio**: Python 3.10+
- **Framework Web**: Flask
- **Database**: MySQL Server
- **Driver DB**: `mysql-connector-python`
- **Sicurezza**: `Werkzeug` (funzioni `generate_password_hash` e `check_password_hash`)
- **Configurazione**: `python-dotenv`
- **Interfaccia Grafica**: HTML5, Jinja2, Bootstrap 5, Bootstrap Icons

---

## 4. Prerequisiti di Sistema
Prima di avviare il progetto, assicurarsi di avere a disposizione:
1. **Python 3.10 o superiore** installato e aggiunto al PATH di sistema.
2. **MySQL Server** locale attivo e in ascolto sulla porta standard `3306`.
3. Credenziali di un utente MySQL locale con permessi di amministrazione (es. utente `root`).

---

## 5. Installazione e Avvio

### Passo 1: Clonare il repository
```bash
git clone <URL_DEL_REPOSITORY>
cd Final_Project

### Passo 2: Creare e attivare l'ambiente virtuale
```bash
python -m venv venv

# Su Windows (Git Bash):
source venv/Scripts/activate

# Su Windows (Prompt dei comandi / PowerShell):
.\venv\Scripts\activate

### Passo 3: Installare le dipendenze
```bash
pip install -r requirements.txt

### Passo 4: Configurare il file `.env`
Creare una copia del file template di esempio ed inserire le credenziali del proprio database locale:

```bash
cp .env.example .env

Nel file .env impostare:
Snippet di codice

DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=la_tua_password_mysql_locale
DB_NAME=ms_track_db
SECRET_KEY=chiave_segreta_casuale_per_sessione_flask

(Nota: la SECRET_KEY è indispensabile per la cifratura dei cookie di sessione e il funzionamento dei messaggi flash).

### Passo 5: Inizializzazione Database e Test

Eseguire lo script automatico per la creazione della struttura e il popolamento con i dati di test:
Bash

python database/test_db.py

### Passo 6: Avvio dell'Applicazione Web Flask
Bash

python app.py

Accedere dal browser all'indirizzo:

http://127.0.0.1:5000/