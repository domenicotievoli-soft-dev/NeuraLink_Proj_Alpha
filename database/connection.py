import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

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
    """Controlla se il DB e la tabella utenti esistono, senza generare eccezioni se il DB è assente."""
    try:
        # Tenta la connessione diretta al DB
        conn = get_connection(db_name=DEFAULT_DB)
        if not conn:
            return False
        
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES LIKE 'utenti'")
        exists = cursor.fetchone() is not None
        cursor.close()
        conn.close()
        return exists
    except Exception:
        # Se il database non esiste (errore 1049), restituisce False silenziosamente
        return False


def init_db(schema_file="schema.sql"):
    """
    Crea il database, esegue schema.sql ed effettua l'hashing automatico
    delle password inserite in testo chiaro.
    """
    if check_db_ready():
        return True
    
    try:
        # 1. Connessione al server MySQL per creare il database
        conn = get_connection(db_name=None)
        if not conn:
            print("Impossibile connettersi al server per l'inizializzazione.")
            return False

        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DEFAULT_DB}")
        print(f"Database '{DEFAULT_DB}' verificato o creato con successo.")
        cursor.close()
        conn.close()

        # 2. Connessione al DB appena creato ed esecuzione dello schema.sql
        conn = get_connection(db_name=DEFAULT_DB)
        cursor = conn.cursor(dictionary=True) # dictionary=True per accedere ai campi per nome

        with open(schema_file, "r", encoding="utf-8") as f:
            sql_commands = f.read()

        statements = sql_commands.split(";")
        for stmt in statements:
            stmt = stmt.strip()
            if stmt and not stmt.upper().startswith("USE"):
                cursor.execute(stmt)

        conn.commit()

        # 3. CONVERSIONE AUTOMATICA DELLE PASSWORD IN TEXT IN HASH
        cursor.execute("SELECT username, password_hash FROM utenti")
        utenti = cursor.fetchall()

        for utente in utenti:
            pwd_raw = utente['password_hash']
            # Convertiamo solo se la password non è già un hash di Werkzeug
            if not pwd_raw.startswith(('pbkdf2:', 'scrypt:', 'argon2:')):
                hashed_pwd = generate_password_hash(pwd_raw)
                cursor.execute(
                    "UPDATE utenti SET password_hash = %s WHERE username = %s",
                    (hashed_pwd, utente['username'])
                )

        conn.commit()
        cursor.close()
        conn.close()
        print("Schema configurato e password cifrate correttamente!")
        return True

    except Error as e:
        print(f"Errore durante l'inizializzazione del DB: {e}")
        return False
    except FileNotFoundError:
        print(f"File {schema_file} non trovato.")
        return False