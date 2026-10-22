from database.connection import get_connection
from werkzeug.security import check_password_hash, generate_password_hash
import os
from dotenv import load_dotenv

CARTELLA_DB = os.path.dirname(os.path.abspath(__file__))
CARTELLA_HOME = os.path.dirname(CARTELLA_DB)
PERCORSO_ENV = os.path.join(CARTELLA_HOME, ".env")

load_dotenv(dotenv_path=PERCORSO_ENV)

DEFAULT_HOST = os.getenv("DB_HOST", "127.0.0.1")
DEFAULT_PORT = int(os.getenv("DB_PORT", 3306))
DEFAULT_USER = os.getenv("DB_USER", "root")
DEFAULT_PW = os.getenv("DB_PASSWORD", "")
DEFAULT_DB = os.getenv("DB_NAME", "ms_track_db")

# ==============================================================================
# AUTENTICAZIONE
# ==============================================================================
def verifica_utente(username, password_in_chiaro):
    """
    Verifica le credenziali di accesso.
    Se l'utente è un medico, recupera anche il suo medico_id interno.
    """
    conn = get_connection()
    if not conn:
        return None

    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT u.username, u.password_hash, u.ruolo, m.id AS medico_id
            FROM utenti u
            LEFT JOIN medici m ON u.username = m.username
            WHERE u.username = %s
        """
        cursor.execute(query, (username,))
        utente = cursor.fetchone()

        if utente and check_password_hash(utente["password_hash"], password_in_chiaro):
            
            return {
                "username": utente["username"],
                "ruolo": utente["ruolo"],
                "medico_id": utente["medico_id"]
            }
        return None
    except Exception as err:
        print(f"Errore verifica login: {err}")
        return None
    finally:
        cursor.close()
        conn.close()


# ==============================================================================
# READ (LETTURA)
# ==============================================================================
def get_pazienti_by_medico(medico_id, search_query=None, sort_by='edss_desc', limit=20, offset=0):
    """
    Restituisce i pazienti di un medico applicando filtri, ordinamento e paginazione in SQL.
    Ritorna una tupla: (lista_pazienti_pagina, totale_pazienti_trovati)
    """
    conn = get_connection()
    if not conn:
        return [], 0

    try:
        cursor = conn.cursor(dictionary=True)

        # 1. Whitelist sicura degli ordinamenti SQL 
        sort_options = {
            'edss_desc': 'edss DESC, p.id ASC',
            'edss_asc': 'edss ASC, p.id ASC',
            'eta_desc': 'p.eta DESC',
            'eta_asc': 'p.eta ASC',
            'id_asc': 'p.id ASC',
            'id_desc': 'p.id DESC'
        }
        order_clause = sort_options.get(sort_by, 'edss DESC, p.id ASC')

        # 2. Costruzione dinamica della clausola WHERE per la ricerca
        where_clause = "WHERE p.medico_id = %s"
        params = [medico_id]

        if search_query:
            where_clause += """ 
            AND (
                p.id LIKE %s 
                OR COALESCE(
                    (SELECT v.farmaco FROM visite v 
                     WHERE v.paziente_id = p.id 
                     ORDER BY v.data_visita DESC, v.id DESC LIMIT 1),
                    p.farmaco
                ) LIKE %s
            )
        """
            filtro = f"%{search_query}%"
            params.extend([filtro, filtro])

        # 3. CONTEGGIO TOTALE (Servirà per la barra delle pagine stile Google)
        count_query = f"SELECT COUNT(*) AS totale FROM pazienti p {where_clause}"
        cursor.execute(count_query, params)
        totale_pazienti = cursor.fetchone()['totale']

        # 4. QUERY PRINCIPALE (Con Sottoquery per Ultimo EDSS/Farmaco + ORDER BY + LIMIT/OFFSET)
        query = f"""
            SELECT 
                p.id, 
                p.eta, 
                p.diagnosi_anno,
                p.medico_id,
                COALESCE(
                    (SELECT v.farmaco 
                     FROM visite v 
                     WHERE v.paziente_id = p.id 
                     ORDER BY v.data_visita DESC, v.id DESC LIMIT 1),
                    p.farmaco
                ) AS farmaco,
                (
                    SELECT CAST(v.edss AS DECIMAL(3,1)) 
                    FROM visite v 
                    WHERE v.paziente_id = p.id 
                    ORDER BY v.data_visita DESC, v.id DESC LIMIT 1
                ) AS edss
            FROM pazienti p
            {where_clause}
            ORDER BY {order_clause}
            LIMIT %s OFFSET %s
        """

        params_paginati = params + [limit, offset]
        cursor.execute(query, params_paginati)
        pazienti = cursor.fetchall()

        # Conversione float sicura per Jinja2
        for p in pazienti:
            if p.get('edss') is not None:
                p['edss'] = float(p['edss'])

        return pazienti, totale_pazienti

    except Exception as err:
        print(f"Errore get_pazienti_by_medico: {err}")
        return [], 0
    finally:
        cursor.close()
        conn.close()


def get_paziente_by_id(paziente_id):
    """Recupera la scheda anagrafica del paziente e tutto lo storico delle sue visite."""
    conn = get_connection()
    if not conn:
        return None, []

    try:
        cursor = conn.cursor(dictionary=True)
        
        # Anagrafica
        query_paziente = "SELECT * FROM pazienti WHERE id = %s"
        cursor.execute(query_paziente, (paziente_id,))
        paziente = cursor.fetchone()

        if not paziente:
            return None, []

        # Storico Visite cronologico
        query_visite = """
            SELECT id, data_visita,farmaco, edss, volume_lesioni, note 
            FROM visite 
            WHERE paziente_id = %s 
            ORDER BY data_visita ASC
        """
        cursor.execute(query_visite, (paziente_id,))
        visite = cursor.fetchall()

        return paziente, visite
    except Exception as err:
        print(f"Errore get_paziente_by_id: {err}")
        return None, []
    finally:
        cursor.close()
        conn.close()


# ==============================================================================
# CREATE (INSERIMENTO)
# ==============================================================================
def crea_paziente(paziente_id, password_in_chiaro, medico_id, eta, diagnosi_anno, farmaco):
    """
    Inserisce l'account in 'utenti' (ruolo paziente) e la scheda in 'pazienti'.
    """
    conn = get_connection()
    if not conn:
        return False

    pw_hash = generate_password_hash(password_in_chiaro)

    try:
        cursor = conn.cursor()
        
        # 1. Account utente per il login
        cursor.execute(
            "INSERT INTO utenti (username, password_hash, ruolo) VALUES (%s, %s, 'paziente')",
            (paziente_id, pw_hash)
        )

        # 2. Scheda clinica paziente
        cursor.execute(
            """INSERT INTO pazienti (id, medico_id, eta, diagnosi_anno, farmaco)
               VALUES (%s, %s, %s, %s, %s)""",
            (paziente_id, medico_id, eta, diagnosi_anno, farmaco)
        )

        conn.commit()
        return True
    except Exception as err:
        print(f"Errore crea_paziente: {err}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def crea_report_visita(paziente_id, data_visita,farmaco, edss, volume_lesioni, note):
    """Aggiunge una visita clinica per un dato paziente."""
    conn = get_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()
        query = """
            INSERT INTO visite (paziente_id, data_visita,farmaco, edss, volume_lesioni, note)
            VALUES (%s, %s, %s, %s, %s,%s)
        """
        cursor.execute(query, (paziente_id, data_visita,farmaco, edss, volume_lesioni, note))
        conn.commit()
        return True
    except Exception as err:
        print(f"Errore crea_report_visita: {err}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


# ==============================================================================
# DELETE (CANCELLAZIONE)
# ==============================================================================
def elimina_paziente(paziente_id):
    """
    Cancella il paziente partendo dalla tabella 'utenti'.
    Grazie al vincolo ON DELETE CASCADE, MySQL rimuove automaticamente:
    - La riga in 'pazienti'
    - Tutte le righe correlate in 'visite'
    """
    conn = get_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM utenti WHERE username = %s AND ruolo = 'paziente'", (paziente_id,))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as err:
        print(f"Errore elimina_paziente: {err}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def elimina_visita_db(visita_id):
    """
    Rimuove una singola visita dal database utilizzando il suo ID unico.
    Restituisce True se l'eliminazione ha avuto successo, False altrimenti.
    """
    connection = get_connection() 
    try:
        cursor = connection.cursor()
        sql = "DELETE FROM visite WHERE id = %s"
        cursor.execute(sql, (visita_id,))
        connection.commit()
        
        # Verifichiamo che almeno una riga sia stata effettivamente cancellata
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Errore durante l'eliminazione della visita {visita_id}: {e}")
        connection.rollback()
        return False
    finally:
        connection.close()

def pulisci_dati_test(prefisso="TEST-%"):
    """Elimina tutti i pazienti di test (e per CASCADE le loro visite)

    il cui ID inizia con il prefisso indicato.
    """
    conn = get_connection()
    if not conn:
        return 0

    try:
        cursor = conn.cursor()
        query = "DELETE FROM utenti WHERE username LIKE %s AND ruolo = 'paziente'"
        cursor.execute(query, (prefisso,))
        righe_eliminate = cursor.rowcount
        conn.commit()
        cursor.close()
        print(f"[PULIZIA MACRO] Eliminati {righe_eliminate} record di test.")
        return righe_eliminate
    except Exception as e:
        conn.rollback()
        print(f"Errore durante la pulizia dei dati di test: {e}")
        return 0
    finally:
        conn.close()

def reset_db():
    """Elimina l'intero database per consentire a init_db() di ricrearlo da zero."""
    conn = get_connection(db_name=None)  # Connessione senza selezionare il DB
    if not conn:
        return False

    try:
        cursor = conn.cursor()
        # Elimina l'intero database
        cursor.execute(f"DROP DATABASE IF EXISTS {DEFAULT_DB}")
        conn.commit()
        cursor.close()
        print(f"[PULIZIA MACRO] Database '{DEFAULT_DB}' eliminato con successo.")
        return True
    except Exception as e:
        print(f"Errore durante la pulizia del database: {e}")
        return False
    finally:
        conn.close()