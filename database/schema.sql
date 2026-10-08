CREATE DATABASE IF NOT EXISTS ms_track_db;
USE ms_track_db;

-- 1. Tabella Pazienti
CREATE TABLE IF NOT EXISTS pazienti (
    id VARCHAR(20) PRIMARY KEY,
    eta INT NOT NULL,
    diagnosi_anno INT NOT NULL,
    farmaco VARCHAR(100) NOT NULL
);

-- 2. Tabella Visite
CREATE TABLE IF NOT EXISTS visite (
    id INT AUTO_INCREMENT PRIMARY KEY,
    paziente_id VARCHAR(20) NOT NULL,
    data_visita DATE NOT NULL,
    edss DECIMAL(3, 1) NOT NULL,
    volume_lesioni DECIMAL(5, 2) NOT NULL,
    note TEXT,
    FOREIGN KEY (paziente_id) REFERENCES pazienti(id) ON DELETE CASCADE
);

-- 3. Popolamento statico iniziale
INSERT INTO pazienti (id, eta, diagnosi_anno, farmaco) VALUES
('PT-101', 34, 2021, 'Ocrelizumab'),
('PT-102', 42, 2019, 'Fingolimod'),
('PT-103', 29, 2023, 'Natalizumab');

INSERT INTO visite (paziente_id, data_visita, edss, volume_lesioni, note) VALUES
('PT-101', '2025-05-10', 2.0, 12.40, 'Quadro clinico iniziale stabile.'),
('PT-101', '2026-02-15', 2.5, 13.10, 'Lieve progressione volumetrica.'),
('PT-102', '2026-01-20', 3.0, 18.00, 'Tolleranza al farmaco regolare.');