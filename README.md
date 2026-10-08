# NeuraLink - Clinical Management System

Applicazione web per il monitoraggio e la gestione clinica dei pazienti affetti da Sclerosi Multipla (SM), con possibilità di ampliamento
a tutte le malattie neurodegenerative con iter clinici e pattern di controllo simili alla SM.


## 1. Analisi del Progetto

### Problema e Obiettivo
Il monitoraggio della sclerosi multipla richiede di seguire nel tempo parametri clinici specifici (come il punteggio EDSS e il volume delle lesioni rilevato da risonanza magnetica).  
**NeuraLink** fornisce una piattaforma centralizzata per associare a ciascun paziente il proprio storico clinico di controlli, garantendo persistenza dei dati, integrità referenziale e visualizzazione cronologica ordinata.

### Utenti e Dati Trattati
- **Utenti target**: Medici neurologi e personale clinico/di ricerca.
- **Paziente**: Codice identificativo univoco (`id`), età, anno di diagnosi, linea terapeutica farmacologica.
- **Visita**: Identificativo visita, data del controllo, scala di disabilità (`edss`), carico lesionale volumetrico (`volume_lesioni`), note cliniche e riferimento al paziente (`paziente_id`).

### Architettura del Database
Il database relazionale (`ms_track_db`) adotta una relazione **1 a Molti (1:N)** tra le tabelle `pazienti` e `visite`:
- Chiave primaria `pazienti(id)` per prevenire duplicazioni anagrafiche.
- Chiave esterna `visite(paziente_id)` con vincolo `ON DELETE CASCADE`: la cancellazione di una scheda paziente rimuove automaticamente tutto lo storico visite associato, garantendo la consistenza dei dati.

---

## 2. Tecnologie Utilizzate
- **Linguaggio**: Python 3.10+
- **Framework Web**: Flask
- **Database**: MySQL Server
- **Driver DB**: `mysql-connector-python`
- **Configurazione**: `python-dotenv`
- **Interfaccia Grafica**: HTML5, Jinja2, Bootstrap 5

---

## 3. Prerequisiti di Sistema
Prima di avviare il progetto, assicurarsi di avere a disposizione sulla propria macchina locale:
1. **Python 3.10 o superiore** installato e aggiunto al PATH di sistema.
2. **MySQL Server** installato, avviato e funzionante (servizio locale attivo sulla porta standard `3306`).
3. Credenziali di un utente MySQL locale con permessi di creazione database e tabelle (es. utente `root`).

---

## 4. Installazione e Avvio

### Passo 1: Clonare il repository
```bash
git clone <URL_DEL_REPOSITORY>
cd Final_Project
```

### Passo 2: Creare e attivare l'ambiente virtuale (consigliato)
```bash
python -m venv venv

# Su Windows (Git Bash):
source venv/Scripts/activate

# Su Windows (Prompt dei comandi / PowerShell):
.\venv\Scripts\activate
```

### Passo 3: Installare le dipendenze
Installare tutti i pacchetti necessari tramite `requirements.txt`:
```bash
pip install -r requirements.txt
```

### Passo 4: Configurare il file `.env` locale
Il progetto necessita delle credenziali del **proprio** database MySQL locale.
1. Creare una copia del file template di esempio:
   ```bash
   cp .env.example .env
   ```
2. Aprire il file `.env` appena generato e impostare la propria password locale:
   ```env
   DB_HOST=127.0.0.1
   DB_PORT=3306
   DB_USER=root
   DB_PASSWORD=la_tua_password_mysql_locale
   DB_NAME=ms_track_db
   ```

### Passo 5: Inizializzazione Database e Test
**Non è necessario creare manualmente il database o le tabelle in MySQL Workbench.**  
Eseguire lo script di verifica:
```bash
python database/test_db.py
```
Questo comando:
- Crea automaticamente il database `ms_track_db` se non esiste.
- Esegue `schema.sql` creando le tabelle e i vincoli relazionali.
- Verifica le operazioni CRUD (inserimento, associazione visite, lettura e cancellazione a cascata).

### Passo 6: Avvio dell'Applicazione Web Flask
```bash
python app.py
```
L'interfaccia web sarà accessibile dal browser all'indirizzo:  
`http://127.0.0.1:5000/`