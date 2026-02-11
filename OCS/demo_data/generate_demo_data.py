"""
Generate demo Excel files for testing the ETECSA Asset Sync workflow.
These files contain fictional data that mimics the real structure.

Run: python generate_demo_data.py
"""

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

# ============================================================================
# 1. AR01 Demo (Finance Department Report)
# ============================================================================
# The real AR01 starts data at row 9 (8 header rows), uses columns 6 and 9

wb_ar01 = Workbook()
ws = wb_ar01.active
ws.title = "AR01"

# Header rows (rows 1-8) — mimicking the real format
header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
header_font = Font(color="FFFFFF", bold=True, size=11)

ws.merge_cells('A1:I1')
ws['A1'] = 'ETECSA - Empresa de Telecomunicaciones de Cuba S.A.'
ws['A1'].font = Font(bold=True, size=14)

ws.merge_cells('A2:I2')
ws['A2'] = 'Dirección Territorial Cienfuegos'
ws['A2'].font = Font(bold=True, size=12)

ws.merge_cells('A3:I3')
ws['A3'] = 'Reporte AR01-1 — Activos Fijos Tangibles'

ws.merge_cells('A4:I4')
ws['A4'] = 'Departamento de Economía y Finanzas'

ws.merge_cells('A5:I5')
ws['A5'] = f'Fecha de emisión: 2024-01-15'

# Row 6-7 blank
# Row 8 = column headers
headers_ar01 = ['Consecutivo', 'Cuenta', 'SubCuenta', 'Descripción', 'Área',
                'No_Inventario', 'Valor', 'Depreciación', 'Local']

for col_idx, header in enumerate(headers_ar01, 1):
    cell = ws.cell(row=8, column=col_idx, value=header)
    cell.font = header_font
    cell.fill = header_fill
    cell.alignment = Alignment(horizontal='center')

# Data rows (starting at row 9) — fictional inventory data
# Municipios de Cienfuegos: Cienfuegos, Rodas, Palmira, Lajas, Cruces,
# Cumanayagua, Abreus, Aguada de Pasajeros

demo_assets = [
    [1, '240', '01', 'PC Desktop HP ProDesk', 'Informática', 'INV-CFG-001', 1500.00, 300.00, 'L-001'],
    [2, '240', '01', 'PC Desktop Dell OptiPlex', 'Informática', 'INV-CFG-002', 1600.00, 320.00, 'L-001'],
    [3, '240', '01', 'Laptop Lenovo ThinkPad', 'RRHH', 'INV-CFG-003', 2100.00, 420.00, 'L-002'],
    [4, '240', '01', 'PC Desktop HP ProDesk', 'Economía', 'INV-CFG-004', 1500.00, 300.00, 'L-003'],
    [5, '240', '01', 'Monitor Samsung 24"', 'Informática', 'INV-CFG-005', 450.00, 90.00, 'L-001'],
    [6, '240', '01', 'Impresora HP LaserJet', 'Dirección', 'INV-CFG-006', 800.00, 160.00, 'L-004'],
    [7, '240', '01', 'PC Desktop Dell', 'Comercial', 'INV-CFG-007', 1500.00, 300.00, 'L-005'],
    [8, '240', '01', 'Laptop HP EliteBook', 'Informática', 'INV-CFG-008', 2200.00, 440.00, 'L-006'],
    [9, '240', '01', 'PC Desktop Lenovo', 'RRHH', 'INV-CFG-009', 1400.00, 280.00, 'L-007'],
    [10, '240', '01', 'Switch Cisco 24p', 'Red', 'INV-CFG-010', 3500.00, 700.00, 'L-008'],
    [11, '240', '01', 'PC Desktop HP', 'Operaciones', 'INV-CFG-011', 1500.00, 300.00, 'L-009'],
    [12, '240', '01', 'Laptop Dell Latitude', 'Comercial', 'INV-CFG-012', 1900.00, 380.00, 'L-010'],
    [13, '240', '01', 'PC Desktop HP ProDesk', 'Planificación', 'INV-CFG-013', 1500.00, 300.00, 'L-011'],
    [14, '240', '01', 'UPS APC 1500VA', 'Informática', 'INV-CFG-014', 600.00, 120.00, 'L-001'],
    [15, '240', '01', 'PC Desktop Dell', 'Logística', 'INV-CFG-015', 1500.00, 300.00, 'L-012'],
    [16, '240', '01', 'Laptop Lenovo L15', 'Dirección', 'INV-CFG-016', 1800.00, 360.00, 'L-004'],
    [17, '240', '01', 'PC Desktop HP', 'Técnico', 'INV-CFG-017', 1500.00, 300.00, 'L-013'],
    [18, '240', '01', 'Servidor Dell R740', 'Informática', 'INV-CFG-018', 8500.00, 1700.00, 'L-014'],
    # Assets in AR01 but NOT in database (for anomaly testing)
    [19, '240', '01', 'PC Desktop Lenovo', 'RRHH', 'INV-CFG-050', 1500.00, 300.00, 'L-002'],
    [20, '240', '01', 'Laptop HP ProBook', 'Comercial', 'INV-CFG-051', 1700.00, 340.00, 'L-005'],
]

for row_data in demo_assets:
    ws.append(row_data)

# Adjust column widths (skip merged cells)
from openpyxl.cell.cell import MergedCell
for col in ws.columns:
    non_merged = [c for c in col if not isinstance(c, MergedCell)]
    if non_merged:
        max_length = max((len(str(c.value)) for c in non_merged if c.value), default=10)
        ws.column_dimensions[non_merged[0].column_letter].width = max_length + 3

wb_ar01.save('demo_data/AR01_demo.xlsx')
print("✓ AR01_demo.xlsx generated")


# ============================================================================
# 2. Clasificador de Locales Demo (HR/Locations Classifier)
# ============================================================================

wb_clasif = Workbook()
ws2 = wb_clasif.active
ws2.title = "Clasificador"

# Headers (columns 1-7, we use columns 5, 6, 7)
headers_clasif = ['Código_Municipio', 'Municipio', 'Código_Centro', 'Centro_Costo',
                  'ID_Local', 'Descripción_Local', 'Edificio']

for col_idx, header in enumerate(headers_clasif, 1):
    cell = ws2.cell(row=1, column=col_idx, value=header)
    cell.font = header_font
    cell.fill = header_fill
    cell.alignment = Alignment(horizontal='center')

# Location data — based on real Cienfuegos municipalities
locations = [
    ['01', 'Cienfuegos', 'CC-001', 'DT Cienfuegos', 'L-001', 'Sala_Servidores', 'Edif_Central_CFG'],
    ['01', 'Cienfuegos', 'CC-001', 'DT Cienfuegos', 'L-002', 'Oficina_RRHH', 'Edif_Central_CFG'],
    ['01', 'Cienfuegos', 'CC-001', 'DT Cienfuegos', 'L-003', 'Depto_Economia', 'Edif_Central_CFG'],
    ['01', 'Cienfuegos', 'CC-001', 'DT Cienfuegos', 'L-004', 'Oficina_Direccion', 'Edif_Central_CFG'],
    ['01', 'Cienfuegos', 'CC-002', 'Centro Telefónico CFG', 'L-005', 'Sala_Comercial', 'CT_Cienfuegos'],
    ['02', 'Rodas', 'CC-003', 'CT Rodas', 'L-006', 'Oficina_Tecnica', 'CT_Rodas'],
    ['03', 'Palmira', 'CC-004', 'CT Palmira', 'L-007', 'Oficina_Admin', 'CT_Palmira'],
    ['04', 'Lajas', 'CC-005', 'CT Lajas', 'L-008', 'Sala_Equipos', 'CT_Lajas'],
    ['05', 'Cruces', 'CC-006', 'CT Cruces', 'L-009', 'Oficina_Operaciones', 'CT_Cruces'],
    ['06', 'Cumanayagua', 'CC-007', 'CT Cumanayagua', 'L-010', 'Oficina_Comercial', 'CT_Cumanayagua'],
    ['07', 'Abreus', 'CC-008', 'CT Abreus', 'L-011', 'Oficina_Planificacion', 'CT_Abreus'],
    ['08', 'Aguada de Pasajeros', 'CC-009', 'CT Aguada', 'L-012', 'Oficina_Logistica', 'CT_Aguada'],
    ['01', 'Cienfuegos', 'CC-010', 'Nodo Provincial', 'L-013', 'Sala_Tecnica', 'Nodo_Provincial'],
    ['01', 'Cienfuegos', 'CC-010', 'Nodo Provincial', 'L-014', 'DataCenter', 'Nodo_Provincial'],
]

for row_data in locations:
    ws2.append(row_data)

# Adjust column widths
for col in ws2.columns:
    max_length = max((len(str(cell.value)) for cell in col if cell.value), default=10)
    ws2.column_dimensions[col[0].column_letter].width = max_length + 3

wb_clasif.save('demo_data/clasificador_demo.xlsx')
print("✓ clasificador_demo.xlsx generated")

print("\n✅ All demo data files generated successfully in demo_data/")
