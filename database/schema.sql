CREATE DATABASE IF NOT EXISTS ms_track_db;
USE ms_track_db;


-- 1. Tabella universale per l'accesso (Login & Ruolo)
CREATE TABLE IF NOT EXISTS utenti (
    username VARCHAR(50) PRIMARY KEY,
    password_hash VARCHAR(255) NOT NULL,
    ruolo ENUM('medico', 'paziente') NOT NULL
);

-- 2. Tabella Medici (operatore clinico)
CREATE TABLE IF NOT EXISTS medici (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    nome VARCHAR(100) NOT NULL,
    FOREIGN KEY (username) REFERENCES utenti(username) ON DELETE CASCADE
);

-- 3. Tabella Pazienti (mantiene il tuo ID PT-xxx, legato al login e al medico curante)
CREATE TABLE IF NOT EXISTS pazienti (
    id VARCHAR(20) PRIMARY KEY,
    medico_id INT NULL,
    eta INT NOT NULL,
    diagnosi_anno INT NOT NULL,
    farmaco VARCHAR(100) NOT NULL,
    FOREIGN KEY (id) REFERENCES utenti(username) ON DELETE CASCADE,
    FOREIGN KEY (medico_id) REFERENCES medici(id) ON DELETE SET NULL
);

-- 4. Tabella Visite (invariata rispetto al tuo schema originale)
CREATE TABLE IF NOT EXISTS visite (
    id INT AUTO_INCREMENT PRIMARY KEY,
    paziente_id VARCHAR(20) NOT NULL,
    data_visita DATE NOT NULL,
    edss DECIMAL(3, 1) NOT NULL,
    volume_lesioni DECIMAL(5, 2) NOT NULL,
    note TEXT,
    FOREIGN KEY (paziente_id) REFERENCES pazienti(id) ON DELETE CASCADE
);

-- Account Login
INSERT INTO utenti (username, password_hash, ruolo) VALUES
('dott.rossi', 'password123', 'medico'),
('PT-101', 'password123', 'paziente'),
('PT-102', 'password123', 'paziente'),
('PT-103', 'password123', 'paziente');

-- Profilo Medico (id generato: 1)
INSERT INTO medici (username, nome) VALUES
('dott.rossi', 'Dott. Mario Rossi');

-- Pazienti associati al Dott. Rossi (medico_id = 1)
INSERT INTO pazienti (id, medico_id, eta, diagnosi_anno, farmaco) VALUES
('PT-101', 1, 34, 2021, 'Ocrelizumab'),
('PT-102', 1, 42, 2019, 'Fingolimod'),
('PT-103', 1, 29, 2023, 'Natalizumab');

-- Visite cliniche
INSERT INTO visite (paziente_id, data_visita, edss, volume_lesioni, note) VALUES
('PT-101', '2025-05-10', 2.0, 12.40, 'Quadro clinico iniziale stabile.'),
('PT-101', '2026-02-15', 2.5, 13.10, 'Lieve progressione volumetrica.'),
('PT-102', '2026-01-20', 3.0, 18.00, 'Tolleranza al farmaco regolare.');