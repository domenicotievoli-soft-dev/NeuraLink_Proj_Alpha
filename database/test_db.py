import os
import sys

# Assicura la corretta risoluzione dei moduli interni
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.connection import init_db
from database.db import (
    crea_paziente,
    crea_report_visita,
    elimina_paziente,
    get_paziente_by_id,
    get_pazienti_by_medico,
    verifica_utente,
    pulisci_dati_test,
    reset_db
)


def run_tests():
  print("\n=== AVVIO DEI TEST DI VERIFICA DATABASE E RUOLI ===")
  

  # 1. Reset e inizializzazione schema
  print("\n1. Inizializzazione schema SQL...")
  try:
    cartella_corrente = os.path.dirname(os.path.abspath(__file__))
    percorso_schema = os.path.join(cartella_corrente, "schema.sql")

    #Pulizia preventiva
    reset_db()
    init_db(schema_file=percorso_schema)
    
    
    print("-> Schema inizializzato con successo.")
  except Exception as e:
    print(f"-> ERRORE durante init_db: {e}")
    return

  # 2. Test Login Medico precaricato dallo schema
  print("\n2. Test autenticazione Medico ('dott.rossi')...")
  medico = verifica_utente("dott.rossi", "password123")
  if medico and medico["ruolo"] == "medico":
    print(
        f"-> Login Medico OK: Username={medico['username']},"
        f" Ruolo={medico['ruolo']}, Medico_ID={medico['medico_id']}"
    )
    medico_id = medico["medico_id"]
  else:
    print("-> FALLITO: Impossibile autenticare il medico.")
    return

  # 3. Test Registrazione nuovo Paziente associato al Medico
  print("\n3. Creazione nuovo Paziente ('TEST-999')...")
  nuovo_paziente = crea_paziente(
      paziente_id="TEST-999",
      password_in_chiaro="pazientePass999",
      medico_id=medico_id,
      eta=45,
      diagnosi_anno=2022,
      farmaco="Glatiramer Acetato",
  )

  if nuovo_paziente:
    print("-> Paziente PT-999 creato e collegato a tabella utenti e pazienti.")
  else:
    print("-> FALLITO: Errore creazione paziente.")
    return

  # 4. Test Login del Paziente
  print("\n4. Test autenticazione Paziente ('TEST-999')...")
  paziente_auth = verifica_utente("TEST-999", "pazientePass999")
  if (
      paziente_auth
      and paziente_auth["ruolo"] == "paziente"
      and paziente_auth["medico_id"] is None
  ):
    print(
        f"-> Login Paziente OK: Username={paziente_auth['username']},"
        f" Ruolo={paziente_auth['ruolo']} (medico_id è None come previsto)."
    )
  else:
    print("-> FALLITO: Autenticazione paziente fallita.")
    return

  # 5. Test Recupero Lista Pazienti del Medico
  print(f"\n5. Recupero pazienti seguiti dal medico ID={medico_id}...")
  pazienti_list = get_pazienti_by_medico(medico_id)
  print(
      f"-> Trovati {len(pazienti_list)} pazienti per questo medico:"
      f" {[p['id'] for p in pazienti_list]}"
  )

  # 6. Test Inserimento Visita Clinica
  print("\n6. Aggiunta visita clinica per TEST-999...")
  visita_ok = crea_report_visita(
      paziente_id="TEST-999",
      farmaco="Interferone",
      data_visita="2026-03-01",
      edss=3.5,
      volume_lesioni=15.80,
      note="Test di controllo periodico: parametri nella norma.",
  )
  if visita_ok:
    print("-> Visita registrata con successo.")
  else:
    print("-> FALLITO: Errore inserimento visita.")
    return

  # 7. Test Recupero Scheda Completa con Storico Visite
  print("\n7. Recupero scheda clinica e storico visite per TEST-999...")
  scheda, visite = get_paziente_by_id("TEST-999")
  print(f"-> Scheda estratta: Età={scheda['eta']}, Farmaco={scheda['farmaco']}")
  print(
      f"-> Visite associate trovate: {len(visite)} (EDSS ultima visita:"
      f" {visite[0]['edss']})"
  )

  # 8. Test Eliminazione a Cascata
  print("\n8. Test cancellazione paziente e verifica CASCADE...")
  eliminato = elimina_paziente("TEST-999")
  scheda_post_delete, visite_post_delete = get_paziente_by_id("TEST-999")

  if eliminato and scheda_post_delete is None and len(visite_post_delete) == 0:
    print(
        "-> Eliminazione completata con successo: rimosso utente, anagrafica e"
        " visite a cascata!"
    )
  else:
    print(
        "-> FALLITO: Il record o le visite orfane sono ancora presenti nel DB."
    )
    return

  #Pulizia finale  
  pulisci_dati_test("TEST-%")  
  print("\n=== TUTTI I TEST SONO STATI SUPERATI CON SUCCESSO! ===")


if __name__ == "__main__":
  run_tests()