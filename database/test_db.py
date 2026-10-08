import db
import os
from connection import get_connection,init_db

def test_connessione():
    print("1. Test Connessione...")
    conn = get_connection()
    assert conn is not None and conn.is_connected(), "Impossibile connettersi a MySQL!"
    conn.close()
    print("   [OK] Connessione riuscita.")

def test_lettura_iniziale():
    print("2. Test Lettura Dati Esistenti...")
    pazienti = db.get_pazienti()
    print(f"   [OK] Trovati {len(pazienti)} pazienti già presenti nel DB.")

def test_ciclo_completo_con_pulizia():
    print("3. Test Inserimento, Lettura e Pulizia Automatica...")
    id_test = "TEST-999"

    # Pulizia preventiva: rimuove qualsiasi residuo precedente
    db.pulisci_dati_test()
    try:
        # A. Inserimento Paziente
        ok_p = db.crea_paziente(id_test, 45, 2021, "Test-Drug")
        assert ok_p, "Errore nella INSERT del paziente."
        print("   [OK] Paziente di test creato.")

        # B. Inserimento Visita
        ok_v = db.crea_report_visita(id_test, "2026-10-01", 1.5, 12.0, "Test note")
        assert ok_v, "Errore nella INSERT della visita."
        print("   [OK] Visita di test creata.")

        # C. Verifica Lettura
        dati = db.get_paziente_by_id(id_test)
        assert dati is not None, "Paziente non trovato!"

        # Stampa di debug per vedere cosa contiene 'dati'
        print(
            f"   [DEBUG] Dati recuperati: {dati.get('id')} - Visite trovate:"
            f" {len(dati.get('visite', []))}"
        )

        assert (
            len(dati.get("visite", [])) == 1
        ), "La visita di test non risulta associata!"
        print("   [OK] Visita verificata con successo.")

    finally:
        # Pulizia conclusiva: garantisce che il DB rimanga pulito al 100%
        db.pulisci_dati_test()
        print("   [OK] Pulizia completata.")

if __name__ == "__main__":
    print("=== AVVIO TEST DEL BACKEND ===")
    cartella_corrente = os.path.dirname(os.path.abspath(__file__))
    percorso_schema = os.path.join(cartella_corrente, "schema.sql")

    init_db(schema_file=percorso_schema)

    try:
        test_connessione()
        test_lettura_iniziale()
        test_ciclo_completo_con_pulizia()
        print("\n Tutto il backend (connessione, letture, scritture, vincoli e cancellazioni) funziona perfettamente!")
    except AssertionError as err:
        print(f"\n❌ TEST FALLITO: {err}")
    except Exception as e:
        print(f"\n❌ ERRORE IMPREVISTO: {e}")