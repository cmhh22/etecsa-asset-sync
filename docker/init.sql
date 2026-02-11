-- ETECSA Asset Sync - Demo Database Schema
-- This creates the OCS Inventory accountinfo table structure

CREATE DATABASE IF NOT EXISTS ocsweb;
USE ocsweb;

CREATE TABLE IF NOT EXISTS accountinfo (
    HARDWARE_ID INT NOT NULL AUTO_INCREMENT,
    TAG VARCHAR(255) DEFAULT NULL,
    fields_3 VARCHAR(255) DEFAULT NULL COMMENT 'Numero de Inventario',
    fields_4 VARCHAR(255) DEFAULT NULL,
    fields_5 VARCHAR(255) DEFAULT NULL,
    fields_6 VARCHAR(255) DEFAULT NULL,
    fields_7 VARCHAR(255) DEFAULT NULL,
    fields_8 VARCHAR(255) DEFAULT NULL,
    fields_9 VARCHAR(255) DEFAULT NULL,
    fields_10 VARCHAR(255) DEFAULT NULL,
    fields_11 VARCHAR(255) DEFAULT NULL,
    PRIMARY KEY (HARDWARE_ID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Insert demo data (fictional inventory numbers and data)
INSERT INTO accountinfo (HARDWARE_ID, TAG, fields_3) VALUES
(1, NULL, 'INV-CFG-001'),
(2, NULL, 'INV-CFG-002'),
(3, NULL, 'INV-CFG-003'),
(4, NULL, 'INV-CFG-004'),
(5, NULL, 'INV-CFG-005'),
(6, NULL, 'INV-CFG-006'),
(7, NULL, 'INV-CFG-007'),
(8, NULL, 'INV-CFG-008'),
(9, NULL, 'INV-CFG-009'),
(10, NULL, 'INV-CFG-010'),
(11, NULL, 'INV-CFG-011'),
(12, NULL, 'INV-CFG-012'),
(13, NULL, 'INV-CFG-003'),   -- Duplicate of INV-CFG-003
(14, NULL, 'MV'),             -- Virtual Machine
(15, NULL, 'MV'),             -- Virtual Machine
(16, NULL, NULL),             -- Empty inventory
(17, NULL, NULL),             -- Empty inventory
(18, NULL, 'INV-CFG-013'),
(19, NULL, 'INV-CFG-014'),
(20, NULL, 'INV-CFG-015'),
(21, NULL, 'INV-CFG-099'),   -- Not in AR01 (anomaly)
(22, NULL, 'INV-CFG-098'),   -- Not in AR01 (anomaly)
(23, NULL, 'INV-CFG-016'),
(24, NULL, 'INV-CFG-017'),
(25, NULL, 'INV-CFG-018');
