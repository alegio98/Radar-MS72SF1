import csv
import struct
import sys

def split_into_chunks(hex_string, chunk_size=4):
    """Splits a space-separated hex string into chunks of given size."""
    bytes_list = hex_string.strip().split()
    return [' '.join(bytes_list[i:i+chunk_size]) for i in range(0, len(bytes_list), chunk_size)]

def process_line(line):
    """Processes a single line to extract time and hex data chunks."""
    # Estrazione tempo
    time = line[1:13]
    
    # Estrazione hex data
    hex_data = line.split(']')[1].strip()
    
    # Split dati in 4 bytes
    chunks = split_into_chunks(hex_data)
    
    return time, chunks

def function1(value):
    """Funzione applicata alle colonne 'ID' per calcolare il numero di persone."""
    try:
        value = str(value).strip()
        value = value.replace(' ', '')
        value = value[:2]
        int_value = int(value, 16)
        length_of_personnel_data = int_value
        num_people = length_of_personnel_data // 32
        return str(num_people)
    except (ValueError, TypeError):
        return value

def function2(value):
    """Funzione applicata alle colonne 'Xn', 'Yn', 'Zn', 'Vxn', 'Vyn', 'Vzn'."""
    try:
        float_value = struct.unpack('<f', bytes.fromhex(value))[0]
        return f"{float_value:.2f}"
    except (ValueError, TypeError):
        return value

def function3(binary_str):
    """Converte una stringa binaria in un numero decimale."""
    try:
        binary_str = str(binary_str).strip()
        binary_str = binary_str.replace(' ', '')
        decimal_value = int(binary_str, 2)
        return decimal_value
    except ValueError:
        return binary_str

def process_txt_to_csv(input_file, intermediate_file):
    with open(input_file, 'r') as infile, open(intermediate_file, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile, delimiter=';')
        
        header = [
            'Time', 'FrameHeader1', 'FrameHeader2', 'LenFrame', 'CurrentFrame', 
            'TLV1', 'AlwaysZero', 'TLV2', 'NumPeople'
        ]
        for i in range(1, 6):  # Assumo di base al massimo 6 persone
            header.extend([f'ID{i}', f'Q{i}', f'X{i}', f'Y{i}', f'Z{i}', f'Vx{i}', f'Vy{i}', f'Vz{i}'])
        csv_writer.writerow(header)
        
        for line in infile:
            time, chunks = process_line(line)
            row = [time] + chunks
            csv_writer.writerow(row)

def apply_functions_to_csv(input_file, output_file):
    with open(input_file, 'r') as infile:
        reader = csv.DictReader(infile, delimiter=';')
        rows = list(reader)
        fieldnames = reader.fieldnames

    non_empty_fieldnames = [field for field in fieldnames if any(row[field] for row in rows)]
    columns_to_remove = {'FrameHeader1', 'FrameHeader2', 'LenFrame', 'CurrentFrame', 
                         'TLV1', 'AlwaysZero', 'Q'}
    final_fieldnames = [field for field in non_empty_fieldnames if field not in columns_to_remove]

    filtered_rows = [row for row in rows if row.get('ID1')]

    for row in filtered_rows:
        for field in final_fieldnames:
            if field.startswith('NumPeople'):
                row[field] = function1(row[field])
            elif field.startswith('ID'):
                row[field] = function3(row[field])
            elif field == 'TLV2':
                row[field] = row[field][:2]
            else:
                row[field] = function2(row[field])

    with open(output_file, 'w', newline='') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=final_fieldnames, delimiter=';')
        writer.writeheader()
        for row in filtered_rows:
            filtered_row = {field: row.get(field, '') for field in final_fieldnames}
            writer.writerow(filtered_row)

if __name__ == "__main__":
    input_txt_file = sys.argv[1]
    intermediate_csv_file = 'output_chunks.csv'
    output_csv_file = 'output_processed.csv'
    
    process_txt_to_csv(input_txt_file, intermediate_csv_file)
    apply_functions_to_csv(intermediate_csv_file, output_csv_file)
