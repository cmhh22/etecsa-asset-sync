import pandas as pd
import mysql.connector  # type: ignore
import sys
import logging
from pathlib import Path
from decouple import config
from openpyxl import load_workbook

# ---------------------------------------------------------------------------
# Configuration from .env
# ---------------------------------------------------------------------------
db_name = config('DB_NAME', default='ocsweb')
db_user = config('DB_USER', default='root')
db_password = config('DB_PASSWORD', default='')
db_host = config('DB_HOST', default='localhost')
db_port_str = config('DB_PORT', default='3306')
db_port = int(db_port_str) if db_port_str else 3306

table_name = config('TABLA_ACCOUNTINFO', default='accountinfo')
inventory_column = config('COLUMNA_INVENTARIO', default='fields_3')

log_file = config('ARCHIVO_REGISTRO', default='Registros.txt')

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='w', encoding='utf-8'),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Load Excel data sources
# ---------------------------------------------------------------------------
finance_file = config('EXCEL_ECONOMIA', default='AR01-1.xlsx')
skip_rows_finance = 8
finance_columns = [5, 8]  # Column 6 (Inventory No.), Column 9 (Location)
df_finance = pd.read_excel(finance_file, skiprows=skip_rows_finance, usecols=finance_columns)

classifier_file = config('EXCEL_CLASIFICADOR', default='CLASIFICADOR DE LOCALES -KARINA-1.xlsx')
classifier_columns = [4, 5, 6]  # Column 5 (LOCATION_ID), Column 6 (LOCATION_DESC), Column 7 (BUILDING)
df_location_classifier = pd.read_excel(classifier_file, usecols=classifier_columns)

# Optimized function to look up inventory number and return the location value
def find_inventory_location(inventory_number):
    inventory_number = inventory_number.strip()  # Clean the inventory number

    # Clean whitespace from the inventory number column
    clean_inventory_col = df_finance.iloc[:, 0].astype(str).str.strip()

    # Check if the inventory number exists in the cleaned column
    if inventory_number in clean_inventory_col.values:
        # Get the index of the matching row
        row_index = clean_inventory_col[clean_inventory_col == inventory_number].index[0]
        location = df_finance.iloc[row_index, 1]  # Get the location column value
        return location.strip() if isinstance(location, str) else location  # Clean if string
    return None


# Look up location in the classifier and return LOCATION_DESC and BUILDING values
def find_classifier_values(location):
    location = location.strip()
    row = df_location_classifier[df_location_classifier.iloc[:, 0].astype(str).str.strip() == location]
    if not row.empty:
        location_desc = str(row.iloc[0, 1]).strip().replace(" ", "_")
        building = str(row.iloc[0, 2]).strip().replace(" ", "_")
        return location_desc, building  # Return values
    return None

# Main function to iterate and process the inventory column
def sync_and_process_data(db_name, db_user, db_password, db_host, db_port, table_name, inventory_column):
    try:
        logger.info('Starting TAG synchronization...')

        # Connect to MySQL database
        connection = mysql.connector.connect(
            database=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port
        )
        cursor = connection.cursor()

        # Execute query
        query = f'SELECT * FROM {table_name}'
        cursor.execute(query)
        db_rows = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]

        # Initialize lists for different conditions
        vm_inventories = []
        empty_inventories = []
        duplicate_inventories = []
        db_not_in_ar01 = []
        locations_not_in_classifier = []
        seen_inventories = {}  # Dict storing already-processed inventories, used to detect duplicates
        db_inventory_list = []  # Stores all DB inventories, used to detect AR01 items missing from DB

        # Cleaned inventory numbers from AR01 (whitespace-stripped)
        ar01_clean_inventories = df_finance.iloc[:, 0].astype(str).str.strip().values

        for index, row in enumerate(db_rows, start=1):
            inventory_number = row[column_names.index(inventory_column)]
            hardware_id_value = row[column_names.index('HARDWARE_ID')]

            logger.info(f"{index}. {inventory_number}")

            if inventory_number is None:
                empty_inventories.append(row)
            elif inventory_number == 'MV':
                vm_inventories.append(row)
            else:
                # Clean the inventory number
                inventory_number = str(inventory_number).strip()

                # Add to DB inventory list and seen dict
                db_inventory_list.append(inventory_number)
                seen_inventories.setdefault(inventory_number, []).append((row, hardware_id_value))
                
                # Check if inventory is not in AR01
                if inventory_number not in ar01_clean_inventories:
                    db_not_in_ar01.append(row)

                found_location = find_inventory_location(inventory_number)
                if found_location:
                    values = find_classifier_values(found_location)
                    if values:
                        location_desc, building = values
                        tag_display = f"[ {building}-{location_desc} ]"
                        tag_db_value = f"{building}-{location_desc}"

                        update_query = f'''
                            UPDATE {table_name} 
                            SET `TAG` = %s 
                            WHERE TRIM(`{inventory_column}`) = %s
                        '''
                        cursor.execute(update_query, (tag_db_value, inventory_number))
                        connection.commit()
                        logger.info(f"TAG updated for inventory {inventory_number} with value {tag_display}")
                    else:
                        logger.warning(f"Location {found_location} not found in classifier for inventory {inventory_number}")
                        locations_not_in_classifier.append((inventory_number, found_location))
                else:
                    logger.warning(f"Inventory {inventory_number} not found in AR01")


        # Process duplicates
        for _, values in seen_inventories.items():
            # Identify duplicates
            if len(values) > 1:
                # Sort by HARDWARE_ID (highest to lowest)
                sorted_values = sorted(values, key=lambda x: x[column_names.index('HARDWARE_ID')], reverse=True)

                for row, _ in sorted_values:
                    # Update TAG before adding to duplicates list
                    inventory_number = row[column_names.index(inventory_column)]
                    found_location = find_inventory_location(str(inventory_number).strip())
                    if found_location:
                        classifier_result = find_classifier_values(found_location)
                        if classifier_result:
                            row_as_dict = dict(zip(column_names, row))  # Convert row to dictionary
                            row_as_dict['TAG'] = f" {classifier_result[1]}-{classifier_result[0]} "  # Keep brackets for duplicates
                            # Add duplicate inventories with updated TAG
                            duplicate_inventories.append(row_as_dict)

        # Compare AR01 inventories with those in the database
        ar01_not_in_db = [inv for inv in ar01_clean_inventories if inv not in db_inventory_list]

        # Corresponding locations for inventories not found in DB
        corresponding_locations = [find_inventory_location(inv) for inv in ar01_not_in_db]

        # Generate DataFrames
        def generate_dataframe_with_message(data, columns, found_message, not_found_message):
            """
            Generates a DataFrame if 'data' is not empty.
            Prints the corresponding message for found/not-found results.
            """
            if data:
                df = pd.DataFrame(data, columns=columns)
                logger.info(f"\n{found_message}")
                logger.info(f"\n{df}")
            else:
                df = pd.DataFrame(columns=columns)
                logger.info(f"\n{not_found_message}")
            return df

        # Generate DataFrames for each category
        df_duplicates = generate_dataframe_with_message(
            duplicate_inventories, 
            column_names, 
            "Rows with duplicate inventories:", 
            "No duplicate inventories found."
        )

        df_empty = generate_dataframe_with_message(
            empty_inventories, 
            column_names, 
            "Rows with 'None':", 
            "No rows with 'None' found."
        )

        df_vm = generate_dataframe_with_message(
            vm_inventories, 
            column_names, 
            "Rows with 'MV' (Virtual Machines):", 
            "No rows with 'MV' found."
        )

        df_db_not_in_ar01 = generate_dataframe_with_message(
            db_not_in_ar01, 
            column_names, 
            "OCS inventories not found in AR01:", 
            "All inventories are in AR01."
        )

        # DataFrame with inventories in AR01 but not in database
        df_ar01_not_in_db = pd.DataFrame({
            'AR01 Inventory not in DB': ar01_not_in_db,
            'Corresponding Location': corresponding_locations
        })

        # DataFrame for locations not found in classifier
        df_locations_not_in_classifier = generate_dataframe_with_message(
            locations_not_in_classifier, 
            ['Inventory', 'Location'], 
            "Locations not found in classifier:", 
            "All locations are in the classifier."
        )

        # Function to auto-fit column widths
        def auto_fit_columns(writer):
            for sheet in writer.sheets.values():
                for column in sheet.columns:
                    # Get maximum length of non-empty cells in the column
                    max_length = max(
                        (len(str(cell.value)) for cell in column if cell.value), 
                        default=0
                    )
                    # Adjust column width
                    adjusted_width = (max_length + 2) * 1.2
                    sheet.column_dimensions[column[0].column_letter].width = adjusted_width  
                      
        # Save results to an Excel file
        sheets_and_dataframes = [
            ('Empty_Inventories', df_empty),
            ('VM_Inventories', df_vm),
            ('Locations_Not_In_Classifier', df_locations_not_in_classifier),
            ('Duplicate_Inventories', df_duplicates),
            ('DB_Not_In_AR01', df_db_not_in_ar01),
            ('AR01_Not_In_DB', df_ar01_not_in_db)
        ]

        with pd.ExcelWriter('Reportes.xlsx', engine='openpyxl') as writer:
            for sheet_name, df in sheets_and_dataframes:
                df.to_excel(writer, sheet_name=sheet_name, index=False)

             # Auto-fit column widths
            auto_fit_columns(writer)

        logger.info("\nReport generated successfully: Reportes.xlsx")

    except mysql.connector.Error as err:
        logger.error(f"Database error: {err}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals() and connection.is_connected():
            connection.close()
        logger.info('Synchronization completed.')

# Call the main function
sync_and_process_data(db_name, db_user, db_password, db_host, db_port, table_name, inventory_column)

