import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from dotenv import load_dotenv
import math

# Import delle funzioni CRUD dal modulo database
from database.db import (
    verifica_utente,
    get_pazienti_by_medico,
    get_paziente_by_id,
    crea_paziente,
    crea_report_visita,
    elimina_paziente,
    elimina_visita_db
)

load_dotenv()

app = Flask(__name__)
# Chiave segreta per la firma sicura dei cookie di sessione
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'chiave_secret_local_12345!')

# FUNZIONI HELPER PER I CONTROLLI DI ACCESSO
def utente_loggato():
    """Verifica se l'utente ha sessioni attive"""
    return 'username' in session

def role_medico():
    """Verifica se l'utente in sessione ha il ruolo di medico"""
    return utente_loggato() and session.get('ruolo') == 'medico'

def role_paziente():
    """Verifica se l'utente in sessione ha il ruolo di paziente"""
    return utente_loggato() and session.get('ruolo') == 'paziente'

# AUTENTICAZIONE & SMISTAMENTO

@app.route('/login', methods=['GET','POST'])
def login():
# Se è già loggato, reindirizza subito alla home di smistamento
    if utente_loggato():
        return redirect(url_for('index'))

    if request.method == 'POST' :
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            #flash invia messaggi di alert in Flask
            flash("Inserisci sia username che password", "warning")
            return render_template('login.html')

        utente = verifica_utente(username, password)

        if utente:
            # Salvataggio sicuro nella sessione
            session['username'] = utente['username']
            session['ruolo'] = utente['ruolo']
            
            # Se è medico salva medico_id, altrimenti se è paziente salva paziente_id (o ID utente)
            session['medico_id'] = utente.get('medico_id')
            session['paziente_id'] = utente.get('paziente_id')  # o utente['username'] se l'ID è PT-101

            flash(f"Accesso effettuato. Benvenuto/a {utente['username']}")
            return redirect(url_for('index'))
        else:
            flash("Credenziali non corrette o utente non trovato", "warning")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Disconnessione effettuata con successo", "info")
    return redirect(url_for('login'))

@app.route('/')
def index():
    """Smista l'utente alla dashboard corretta in base al ruolo"""
    if not utente_loggato():
        return redirect(url_for('login'))

    if session.get('ruolo') == 'medico':
        return redirect(url_for('dashboard_medico'))
    elif session.get('ruolo') == 'paziente':
        return redirect(url_for('dashboard_paziente'))
    else:
        session.clear() 
        return redirect(url_for('login'))

@app.after_request
def add_header(response):
    """
    Impedisce al browser di salvare le pagine in cache (bfcache).
    Se l'utente fa Logout e preme 'Indietro', il browser è costretto
    a richiedere la pagina al server, che lo reindirizzerà al Login.
    """
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

# AREA MEDICO
@app.route('/medico/dashboard')
def dashboard_medico():
    if not utente_loggato():
        flash("Accedi prima di continuare.", "warning")
        return redirect(url_for('login'))

    if not role_medico():
        flash("Accesso non autorizzato all'area medica." , "danger")
        return redirect(url_for('index'))

    query_ricerca = request.args.get('q', '').strip()
    medico_id = session.get('medico_id')
    ordina_per = request.args.get('sort', 'edss_desc')
    
    # Gestione Numero Pagina
    try:
        page = int(request.args.get('page', 1))
        if page < 1: page = 1
    except ValueError:
        page = 1

    per_page = 20
    offset = (page - 1) * per_page


    # Recupera i pazienti (con eventuale filtro di ricerca per ID o farmaco)
    pazienti, totale_pazienti = get_pazienti_by_medico(
        medico_id=medico_id,
        search_query=query_ricerca or None,
        sort_by=ordina_per,
        limit=per_page,
        offset=offset
    )

    total_pages = math.ceil(totale_pazienti / per_page) if totale_pazienti > 0 else 1
    start_item = offset + 1 if totale_pazienti > 0 else 0
    end_item = min(offset + per_page, totale_pazienti)

    # Se la lista è vuota, passa valori di default ed evita calcoli Pandas
    if not pazienti:
        return render_template(
            'area_medico.html', 
            pazienti=[], 
            totale_pazienti=0,
            dates=[], 
            edss_scores=[], 
            volume_lesioni=[]
        )
    
    
    # Sovrascrive dinamicamente farmaco ed EDSS di ciascun paziente
    for paziente in pazienti:
        _, visite = get_paziente_by_id(paziente['id'])
        if visite and len(visite) > 0:
            paziente['farmaco'] = visite[-1]['farmaco']
            
            # Conversione sicura dell'EDSS in float
            valore_edss = visite[-1].get('edss')
            try:
                paziente['edss'] = float(valore_edss) if valore_edss is not None else None
            except (ValueError, TypeError):
                paziente['edss'] = None
        else:
            paziente['edss'] = None
    
    return render_template(
        'area_medico.html',
        pazienti=pazienti,
        totale_pazienti=totale_pazienti,
        page=page,
        total_pages=total_pages,
        start_item=start_item,
        end_item=end_item,
        query=query_ricerca,
        sort_current=ordina_per
    )

@app.route('/medico/paziente/nuovo', methods=['GET', 'POST'])
def nuovo_paziente():
    if not role_medico():
        flash("Operazione riservata al personale medico.", "danger")
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        paziente_id = request.form.get('paziente_id', '').strip().upper()
        password = request.form.get('password', '').strip()
        eta = request.form.get('eta', '').strip()
        diagnosi_anno = request.form.get('diagnosi_anno', '').strip()
        farmaco = request.form.get('farmaco', '').strip()
        medico_id = session.get('medico_id')

        # Validazione base campi obbligatori
        if not(paziente_id and password and eta and diagnosi_anno and farmaco):
            flash("Tutti i campi sono obbligatori.", "warning")
            return render_template('form_paziente.html')

        success = crea_paziente(
            paziente_id=paziente_id,
            password_in_chiaro=password,
            medico_id=medico_id,
            eta=int(eta),
            diagnosi_anno=int(diagnosi_anno),
            farmaco=farmaco
        )

        if success:
            flash(f"Paziente {paziente_id} registrato con successo!", "success")
            return redirect(url_for('dashboard_medico'))
        else:
            flash("Errore nella registrazione: verificare che l'ID non sia già esistente.", "danger")

    #Se arriviamo a questo punto, significa che non è stato registrato correttamente
    #un nuovo paziente, per cui facciamo il render nuovamente del form_paziente
    return render_template('form_paziente.html')

@app.route('/medico/paziente/<paziente_id>', methods=['GET','POST'])
def dettaglio_paziente_medico(paziente_id):
    if not role_medico():
        flash("Accesso non consentito.", "danger")
        return redirect(url_for('index'))

   
    # GET: lettura cartella e storico visite
    paziente, visite = get_paziente_by_id(paziente_id)
    if not paziente:
        flash("Paziente non trovato.", "warning")
        return redirect(url_for('dashboard_medico'))

    return render_template('dettaglio_paziente.html', paziente=paziente, visite=visite)  

@app.route('/medico/paziente/<paziente_id>/visita/nuova', methods=['POST'])
def nuova_visita(paziente_id):
    # Verifica di sicurezza lato server
    if not role_medico():
        flash("Operazione non autorizzata: solo il personale medico può registrare visite.", "danger")
        return redirect(url_for('login'))

    #Se viene inviato il form di una nuova visita clinica
    if request.method == 'POST':
        data_visita = request.form.get('data_visita')
        farmaco = request.form.get('farmaco')
        edss = request.form.get('edss')
        volume_lesioni = request.form.get('volume_lesioni')
        note = request.form.get('note', '').strip()

        if not (data_visita and edss and volume_lesioni):
                flash("Data visita, EDSS e Volume Lesioni sono obbligatori.", "warning")
        else:
                salvato = crea_report_visita(
                    paziente_id=paziente_id,
                    data_visita=data_visita,
                    farmaco=farmaco,
                    edss=float(edss),
                    volume_lesioni=float(volume_lesioni),
                    note=note
                )
                if salvato:
                    flash("Visita registrata correttamente.", "success")
                else:
                    flash("Errore nel salvataggio della visita.", "danger")

        return redirect(url_for('dettaglio_paziente_medico', paziente_id=paziente_id))  
    
@app.route('/medico/paziente/<paziente_id>/elimina', methods=['POST'])
def cancella_paziente(paziente_id):
    if not role_medico():
        flash("Operazione non permessa.", "danger")
        return redirect(url_for('index'))

    eliminato = elimina_paziente(paziente_id)
    if eliminato:
        flash(f"Paziente {paziente_id} e relativo storico eliminati con successo.", "info")
    else:
        flash("Errore durante l'eliminazione del paziente.", "danger")

    return redirect(url_for('dashboard_medico'))    

@app.route('/medico/visita/<int:visita_id>/cancella', methods=['POST'])
def cancella_visita(visita_id):
    if not role_medico():
        flash("Operazione riservata al personale medico.", "danger")
        return redirect(url_for('login'))

    paziente_id = request.form.get('paziente_id')

    # Esegui la cancellazione della visita dal database
    eliminato = elimina_visita_db(visita_id) # sostituisci con la tua funzione DB

    if eliminato:
        flash("Visita eliminata correttamente.", "success")
    else:
        flash("Errore durante l'eliminazione della visita.", "danger")

    return redirect(url_for('dettaglio_paziente_medico', paziente_id=paziente_id))

# AREA PAZIENTE 
@app.route('/paziente/dashboard')
def dashboard_paziente():
    if not utente_loggato():
        flash("Accedi prima di continuare.", "warning")
        return redirect(url_for('login'))

    if not role_paziente():
        flash("Accesso non autorizzato all'area paziente.", "danger")
        return redirect(url_for('index'))

    # Il paziente vede solo e soltanto la propria cartella clinica
    paziente_id = session.get('username')
    paziente, visite = get_paziente_by_id(paziente_id)

    return render_template('area_paziente.html', paziente=paziente, visite=visite)



#TEST
@app.route('/test-base')
def test_base():
  return render_template('base.html')

# AVVIO APPLICAZIONE
if __name__ == '__main__':
    app.run(debug=True)