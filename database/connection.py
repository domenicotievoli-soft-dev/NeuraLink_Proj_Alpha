import os
import mysql.connector
from mysql.connector import Error
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

def get_connection(db_name=DEFAULT_DB, host=DEFAULT_HOST, port=DEFAULT_PORT, user=DEFAULT_USER, pw=DEFAULT_PW):
    """
    Crea e restituisce un oggetto connessione.
    Se db_name è impostato, si connette al database indicato.
    """
    try:
        connection_params = {
            "host": host,
            "port": port,
            "user": user,
            "password": pw
        }
        
        if db_name:
            connection_params["database"] = db_name

        connection = mysql.connector.connect(**connection_params)

        if connection.is_connected():
            return connection

    except Error as e:
        print(f"Errore durante la connessione a MySQL: {e}")
        return None

def check_db_ready():
    """Controlla velocemente se la tabella principale esiste già."""
    conn = get_connection(db_name=DEFAULT_DB)
    if not conn:
        return False
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES LIKE 'pazienti'")
    exists = cursor.fetchone() is not None
    cursor.close()
    conn.close()
    return exists


def init_db(schema_file="schema.sql"):
    """
    Crea il database se non esiste ed esegue lo script SQL di inizializzazione.
    """
    if check_db_ready():
        return True
    
    try:
        #Connessione generica al server MySQL (senza DB)
        conn = get_connection(db_name=None)
        if not conn:
            print("Impossibile connettersi al server per l'inizializzazione.")
            return False

        cursor = conn.cursor()
        
        #Crea il DB se assente
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DEFAULT_DB}")
        print(f"Database '{DEFAULT_DB}' verificato o creato con successo.")
        cursor.close()
        conn.close()

        #Ora che il DB esiste, ci connettiamo direttamente ad esso
        conn = get_connection(db_name=DEFAULT_DB)
        cursor = conn.cursor()

        #Leggiamo ed eseguiamo le query di schema.sql
        with open(schema_file, "r", encoding="utf-8") as f:
            sql_commands = f.read()

        # Separiamo per ';' ed eseguiamo comando per comando (ignora USE e vuoti)
        statements = sql_commands.split(";")
        
        for stmt in statements:
            stmt = stmt.strip()
            # Saltiamo statement vuoti o comandi USE (siamo già collegati al DB)
            if stmt and not stmt.upper().startswith("USE"):
                cursor.execute(stmt)

        conn.commit()
        cursor.close()
        conn.close()
        print("Schema e tabelle configurati con successo!")
        return True

    except Error as e:
        print(f"Errore durante l'inizializzazione del DB: {e}")
        return False
    except FileNotFoundError:
        print(f"File {schema_file} non trovato.")
        return False