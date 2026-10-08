from connection import get_connection, init_db
 

#READ
def get_pazienti(search_query=None):
    """Tabella generale e la barra di ricerca:
        Restituisce tutti i pazienti oppure mi restituisce i pazienti associati ad un farmaco
    """
    connection = get_connection()
    if not connection:
        return[]
    cursor = connection.cursor(dictionary=True)

    #Verifico che ci sia un parametro di ricerca ed effettuo una ricerca parziale basata su pattern
    if search_query:
        query = "SELECT * FROM pazienti WHERE farmaco LIKE %s"
        param = f"%{search_query}%"
        cursor.execute(query, (param,))
    else:
        query = "SELECT * FROM pazienti"
        cursor.execute(query)

    risultati = cursor.fetchall()
    cursor.close()
    connection.close()
    return risultati

def get_paziente_by_id(paziente_id):
    """Scheda clinica dettagliata: restituisce l'anagrafica del paziente e l'elenco cronologico delle visite."""
    connection = get_connection()
    if not connection:
        return None
    pass

    cursor = connection.cursor(dictionary = True)
    # Lettura anagrafica
    cursor.execute("SELECT * FROM pazienti WHERE id = %s", (paziente_id,))
    paziente = cursor.fetchone()

    # Se il paziente esiste, alleghiamo lo storico visite
    if paziente:
        cursor.execute (
            """
        SELECT * FROM visite
        WHERE paziente_id = %s
        ORDER BY data_visita DESC
            """,
            (paziente_id,)
        )
        paziente["visite"] = cursor.fetchall()
    
    cursor.close()
    connection.close()
    return paziente
#CREATE
def crea_paziente(paziente_id, eta, diagnosi_anno, farmaco):
    """Registra un nuovo paziente"""
    connection = get_connection()
    if not connection:
        return False

    try:
        cursor = connection.cursor()
        query = """
                INSERT INTO pazienti (id, eta, diagnosi_anno, farmaco)
                VALUES (%s, %s, %s, %s)
                """
        cursor.execute (query, (paziente_id, eta, diagnosi_anno, farmaco))
        connection.commit()
        cursor.close()
        return True
    except Exception as e:
        connection.rollback()
        print(f"Errore durante l'inserimento del paziente: {e}")
        return False
    finally:
        connection.close()

def crea_report_visita(paziente_id, data_visita, edss, volume_lesioni, note):
    """Registra il report di una visita effettuata"""
    connection = get_connection()
    if not connection:
        return False

    try:
        cursor = connection.cursor()
        query = """
            INSERT INTO visite (paziente_id, data_visita, edss, volume_lesioni, note)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(
            query, (paziente_id, data_visita, edss, volume_lesioni, note)
        )
        connection.commit()
        cursor.close()
        return True
    except Exception as e:
        connection.rollback()
        print(f"Errore durante l'inserimento della visita: {e}")
        return False
    finally:
        connection.close()


def elimina_paziente(paziente_id):
    """Elimina un paziente"""
    connection = get_connection()
    if not connection:
        return None
    try:
        cursor = connection.cursor()
        query = "DELETE FROM pazienti WHERE id=%s"
        cursor.execute(query, (paziente_id,))
        connection.commit()
        cursor.close()
        return True
    except Exception as e:
        connection.rollback()
        print(f"Errore durante l'eliminazione: {e}")
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
        query = "DELETE FROM pazienti WHERE id LIKE %s"
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