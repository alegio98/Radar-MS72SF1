import json
import argparse
import csv

def calculate_averages(data):
    """Calcola la media delle coordinate x, y, z per ogni time, escludendo punti con valori fuori dal range [-10, 10]."""
    results = []
    
    for entry in data:
        if entry is None or 'points' not in entry or not isinstance(entry['points'], list):
            print(f"Elemento non è un dizionario: {entry}")
            continue
        
        total_x, total_y, total_z = 0.0, 0.0, 0.0
        count = 0
        
        for point in entry['points']:
            try:
                x_values = [float(point[key]) for key in point if key.startswith('x')]
                y_values = [float(point[key]) for key in point if key.startswith('y')]
                z_values = [float(point[key]) for key in point if key.startswith('z')]
                
                # Verifica se tutti i valori sono nel range [-10, 10]
                if all(-10 <= x <= 10 for x in x_values) and \
                   all(-10 <= y <= 10 for y in y_values) and \
                   all(-10 <= z <= 10 for z in z_values):
                    
                    total_x += sum(x_values)
                    total_y += sum(y_values)
                    total_z += sum(z_values)
                    count += 1
                
            except (ValueError, TypeError):
                print(f"Errore nel calcolo: {point}")
                continue
        
        # Calcola la media solo se ci sono valori validi
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

def process_json_file(input_file, output_file):
    """Legge il file JSON, calcola le medie e salva il risultato in un file CSV."""
    try:
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        # Calcola le medie
        averaged_data = calculate_averages(data)
        
        # Scrive i risultati in un file CSV
        with open(output_file, 'w', newline='') as csvfile:
            fieldnames = ['time', 'average_x', 'average_y', 'average_z']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
            
            writer.writeheader()
            for row in averaged_data:
                writer.writerow(row)
        
        print(f'Dati medi salvati in {output_file}')
    
    except json.JSONDecodeError as e:
        print(f"Errore nella lettura del file JSON: {e}")
    except FileNotFoundError as e:
        print(f"File non trovato: {e}")
    except Exception as e:
        print(f"Si è verificato un errore: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Processa un file JSON per calcolare la media delle coordinate x, y, z per ogni time e salva in CSV.")
    parser.add_argument('input_file', type=str, help='Il file JSON di input da elaborare')
    parser.add_argument('output_file', type=str, help='Il file CSV di output per salvare i risultati')

    args = parser.parse_args()

    # Processa il file JSON e salva il risultato in un CSV
    process_json_file(args.input_file, args.output_file)
