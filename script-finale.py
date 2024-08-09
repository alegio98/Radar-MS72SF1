import csv
import struct
import sys
import re

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

def remove_empty_lines(input_file, cleaned_file):
    """Rimuove linee vuote dal file > per evitare errori quando processiamo i file txt."""
    with open(input_file, 'r') as infile, open(cleaned_file, 'w') as outfile:
        for line in infile:
            if line.strip():
                outfile.write(line)

def process_txt_to_csv(input_file, intermediate_file, mode):
    with open(input_file, 'r') as infile, open(intermediate_file, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile, delimiter=';')
        
        if mode == 'd2':
            header = ['Time', 'TLV2', 'NumPeople']
            for i in range(1, 6):  # Assumo di base al massimo 6 persone
                header.extend([f'ID{i}', f'Q{i}', f'X{i}', f'Y{i}', f'Z{i}', f'Vx{i}', f'Vy{i}', f'Vz{i}'])
        else:  # mode == 'd3'
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

def preprocess_file(input_file, output_file):
    """Processa il file in modo tale da prendere solo nel caso in cui abbiamo debug 2 i valori successvi a i byes 02 00 00 00."""
    time_pattern = r'^\[(\d{2}:\d{2}:\d{2}\.\d{3})\]'
    data_pattern = r'02 00 00 00'
    
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        for line in infile:
            time_match = re.match(time_pattern, line)
            if not time_match:
                continue
            
            time_str = time_match.group(1)
            data_start = line.find(data_pattern)
            
            if data_start == -1:
                continue
            
            data_str = line[data_start:].strip()
            outfile.write(f'[{time_str}] {data_str}\n')

if __name__ == "__main__":
    input_txt_file = sys.argv[1]
    mode = sys.argv[2]
    intermediate_csv_file = 'output_chunks.csv'
    output_csv_file = 'output_processed.csv'
    cleaned_txt_file = 'cleaned_input.txt'

    # Remove empty lines from the input file
    remove_empty_lines(input_txt_file, cleaned_txt_file)

    if mode == 'd2':
        preprocessed_txt_file = 'preprocessed_input.txt'
        preprocess_file(cleaned_txt_file, preprocessed_txt_file)
        process_txt_to_csv(preprocessed_txt_file, intermediate_csv_file, mode)
    else:  # mode == 'd3'
        process_txt_to_csv(cleaned_txt_file, intermediate_csv_file, mode)

    apply_functions_to_csv(intermediate_csv_file, output_csv_file)
