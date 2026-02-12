-- ETECSA Asset Sync — Demo Database Schema
-- Creates the OCS Inventory accountinfo table matching the Django model

CREATE DATABASE IF NOT EXISTS ocsweb;
USE ocsweb;

CREATE TABLE IF NOT EXISTS accountinfo (
    hardware_id VARCHAR(100) NOT NULL,
    tag VARCHAR(100) DEFAULT '',
    edificio VARCHAR(100) DEFAULT '',
    noinventario VARCHAR(100) DEFAULT '',
    usuario VARCHAR(100) DEFAULT '',
    observaciones TEXT DEFAULT NULL,
    fields_3 VARCHAR(100) DEFAULT NULL COMMENT 'Inventory Number',
    fields_4 VARCHAR(100) DEFAULT NULL,
    fields_5 VARCHAR(100) DEFAULT NULL,
    fields_6 VARCHAR(100) DEFAULT NULL,
    fields_7 VARCHAR(100) DEFAULT NULL,
    fields_8 VARCHAR(100) DEFAULT NULL,
    fields_9 VARCHAR(100) DEFAULT NULL,
    fields_10 VARCHAR(100) DEFAULT NULL,
    fields_11 VARCHAR(100) DEFAULT NULL,
    PRIMARY KEY (hardware_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Insert demo data (fictional — does not contain real ETECSA information)
INSERT INTO accountinfo (hardware_id, tag, edificio, noinventario, usuario, fields_3) VALUES
('1001', 'DTCFG-Despacho Dir', 'DTCFG', '180045', 'Juan Perez', '180045'),
('1002', 'DTCFG-Contabilidad', 'DTCFG', '180046', 'Maria Garcia', '180046'),
('1003', 'CCFG_CENTRO-RRHH', 'CCFG_CENTRO', '180047', 'Carlos Lopez', '180047'),
('1004', 'CCFG_PRADO-Comercial', 'CCFG_PRADO', '180048', 'Ana Rodriguez', '180048'),
('1005', 'DTCFG-Area Tecnica', 'DTCFG', '180049', 'Pedro Sanchez', '180049'),
('1006', 'DTCFG-Direccion', 'DTCFG', '180050', 'Director Provincial', '180050'),
('1007', 'MUN_RODAS-Oficina', 'MUN_RODAS', '180051', 'Luis Hernandez', '180051'),
('1008', 'MUN_CRUCES-Oficina', 'MUN_CRUCES', '180052', 'Sofia Martinez', '180052'),
('1009', 'DTCFG-Datacenter', 'DTCFG', '180054', 'Admin Sistemas', '180054'),
('1010', 'CCFG_CENTRO-Almacen', 'CCFG_CENTRO', '180055', 'Teresa Gomez', '180055'),
('1011', 'DTCFG-Juridico', 'DTCFG', '180056', 'Fernando Ruiz', '180056'),
('1012', '', '', '180057', 'Test VM', 'MV'),
('1013', 'CCFG_PRADO-Recepcion', 'CCFG_PRADO', '180058', 'Marta Suarez', '180058'),
('1014', 'DTCFG-Taller', 'DTCFG', '180059', 'Miguel Torres', '180059'),
('1015', 'DTCFG-Despacho Dir', 'DTCFG', '180045', 'Juan Perez', '180045'),
('1016', 'DTCFG-SinDoc', 'DTCFG', '', 'No Inventory', ''),
('1017', '', '', '180060', 'New Equipment', '180060'),
('1018', 'CCFG_CENTRO-Planificacion', 'CCFG_CENTRO', '180061', 'Laura Vega', '180061'),
('1019', 'MUN_CRUCES-Comercial', 'MUN_CRUCES', '180062', 'Diego Mora', '180062'),
('1020', '', '', '180063', 'Roberto Diaz', '180063');
