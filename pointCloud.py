import struct
import json
import argparse
import csv
import os

#How to use the script : python pointCloud.py input.txt output.csv

# Funzioni di manipolazione del file TXT
def split_into_chunks(hex_string, chunk_size=1):
    bytes_list = hex_string.strip().split()
    return [' '.join(bytes_list[i:i+chunk_size]) for i in range(0, len(bytes_list), chunk_size)]

def process_line(line):
    try:
        time = line[1:13]
        hex_data = line.split(']')[1].strip()
        chunks = split_into_chunks(hex_data, 1)

        if len(chunks) < 24:
            print(f"Linea troppo corta, viene skippata: {time}, Chunks: {chunks}")
            return None

        return time, chunks
    except Exception as e:
        print(f"Errore durante l'elaborazione della linea: {line}. Errore: {e}")
        return None

def mappare(line):
    result = {}
    processed = process_line(line)
    if processed:
        time, chunks = processed
        result['time'] = time
        headers = chunks[:8]
        result['headers'] = headers
        frame = chunks[8:12]
        result['frame'] = frame
        tlv1 = ''.join(chunks[16:20])
        result['TLV1'] = tlv1
        point_length = int(''.join(chunks[20:24]), 16)
        result['PointL'] = f'{point_length:08X}'
        points = []
        index = 24
        point_counter = 1
        while index < len(chunks):
            if ''.join(chunks[index:index + 4]) == '02 00 00 00':
                break
            if index + 25 > len(chunks):
                break
            x = ''.join(chunks[index:index + 4])
            y = ''.join(chunks[index + 4:index + 8])
            z = ''.join(chunks[index + 8:index + 12])
            v = chunks[index + 12]
            snr = ''.join(chunks[index + 13:index + 17])
            po = ''.join(chunks[index + 17:index + 21])
            dpk = ''.join(chunks[index + 21:index + 25])
            points.append({
                f'x{point_counter}': x,
                f'y{point_counter}': y,
                f'z{point_counter}': z,
                f'v{point_counter}': v,
                f'SNR{point_counter}': snr,
                f'POW{point_counter}': po,
                f'DPK{point_counter}': dpk
            })
            point_counter += 1
            index += 25
        result['points'] = points
    return result if result else None

def process_file(file_path):
    results = []
    with open(file_path, 'r') as file:
        for line in file:
            if line.strip():
                mapped_data = mappare(line)
                if mapped_data:
                    results.append(mapped_data)
    return results

# Funzioni di manipolazione del JSON
def function2(value):
    try:
        float_value = struct.unpack('<f', bytes.fromhex(value))[0]
        return f"{float_value:.2f}"
    except (ValueError, TypeError):
        return value

def transform_values(data):
    if not isinstance(data, list):
        raise ValueError("Il file JSON deve essere un array di oggetti.")
    for entry in data:
        if 'points' in entry:
            for point in entry['points']:
                for key in list(point.keys()):
                    if key.startswith(('x', 'y', 'z', 'v')):
                        point[key] = function2(point[key])
    return data

def remove_fields(data):
    if not isinstance(data, list):
        raise ValueError("Il file JSON deve essere un array di oggetti.")
    for entry in data:
        entry.pop('headers', None)
        entry.pop('frame', None)
        entry.pop('TLV1', None)
        entry.pop('PointL', None)
        if 'points' in entry:
            for point in entry['points']:
                keys_to_remove = [key for key in point if key.startswith(('v', 'SNR', 'POW', 'DPK'))]
                for key in keys_to_remove:
                    del point[key]
    return data

def check_if_json_is_empty(json_file):
    return os.stat(json_file).st_size == 0

def calculate_averages(data):
    results = []
    for entry in data:
        if entry is None or 'points' not in entry or not isinstance(entry['points'], list):
            continue
        total_x, total_y, total_z = 0.0, 0.0, 0.0
        count = 0
        for point in entry['points']:
            try:
                x_values = [float(point[key]) for key in point if key.startswith('x')]
                y_values = [float(point[key]) for key in point if key.startswith('y')]
                z_values = [float(point[key]) for key in point if key.startswith('z')]
                if all(-10 <= x <= 10 for x in x_values) and \
                   all(-10 <= y <= 10 for y in y_values) and \
                   all(-10 <= z <= 10 for z in z_values):
                    total_x += sum(x_values)
                    total_y += sum(y_values)
                    total_z += sum(z_values)
                    count += 1
            except (ValueError, TypeError):
                continue
        average_x = round(total_x / count, 2) if count > 0 else None
        average_y = round(total_y / count, 2) if count > 0 else None
        average_z = round(total_z / count, 2) if count > 0 else None
        results.append({
            'time': entry['time'],
            'average_x': average_x,
            'average_y': average_y,
            'average_z': average_z
        })
    return results

def save_to_json(data, output_file):
    try:
        with open(output_file, 'w') as file:
            json.dump(data, file, indent=4)
        print(f'Dati salvati in {output_file}')
    except Exception as e:
        print(f"Errore nella scrittura del file JSON: {e}")

def save_averages_to_csv(averaged_data, output_file):
    try:
        with open(output_file, 'w', newline='') as csvfile:
            fieldnames = ['time', 'average_x', 'average_y', 'average_z']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
            writer.writeheader()
            for row in averaged_data:
                writer.writerow(row)
        print(f'Dati medi salvati in {output_file}')
    except Exception as e:
        print(f"Si è verificato un errore durante la scrittura del CSV: {e}")

def process_json_file(input_file, output_file):
    """Legge il file JSON, rimuove i campi e trasforma i valori, quindi salva il risultato."""
    try:
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        # Verifica che i dati non siano None
        if data is None:
            raise ValueError("Il file JSON è vuoto o non è stato letto correttamente.")
        
        # Rimuovi i campi indesiderati
        updated_data = remove_fields(data)
        
        # Trasforma i valori x, y, z, v
        transformed_data = transform_values(updated_data)
        
        # Salva il file JSON aggiornato
        with open(output_file, 'w') as f:
            json.dump(transformed_data, f, indent=4)
        
        print(f'Dati aggiornati salvati in {output_file}')
    
    except json.JSONDecodeError as e:
        print(f"Errore nella lettura del file JSON: {e}")
    except FileNotFoundError as e:
        print(f"File non trovato: {e}")
    except ValueError as e:
        print(f"Errore nel formato dei dati: {e}")
    except Exception as e:
        print(f"Si è verificato un errore: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Processa un file TXT, manipola i dati e salva in un file CSV con medie delle coordinate.")
    parser.add_argument('input_txt', type=str, help='Il file TXT di input da elaborare')
    parser.add_argument('output_csv', type=str, help='Il file CSV di output per salvare i risultati finali')

    args = parser.parse_args()

    json_intermediate_file = "intermediate.json"
    processed_data = process_file(args.input_txt)
    save_to_json(processed_data, json_intermediate_file)

    if not check_if_json_is_empty(json_intermediate_file):
        process_json_file(json_intermediate_file, json_intermediate_file)
        with open(json_intermediate_file, 'r') as f:
            transformed_data = json.load(f)
        averaged_data = calculate_averages(transformed_data)
        save_averages_to_csv(averaged_data, args.output_csv)
