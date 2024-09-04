import struct
import json
import argparse



# Il codice sottostante manipola il file TXT generato dall'interfaccia SSCOM5 per la configurazione DEBUG 2 ed estrare nel giusto modo i
# bytes relativi alla nuvola di punti. 

"""HOW TO USE THIS SCRIPT: > python manipolazione.py <percorso_del_file_input.txt> <percorso_del_file_output.json> """

def split_into_chunks(hex_string, chunk_size=1):
    """Splits a space-separated hex string into chunks of given size."""
    bytes_list = hex_string.strip().split()
    return [' '.join(bytes_list[i:i+chunk_size]) for i in range(0, len(bytes_list), chunk_size)]


def process_line(line):
    """Processes a single line to extract time and hex data chunks."""
    # Estrazione tempo
    time = line[1:13]
    
    # Estrazione hex data
    hex_data = line.split(']')[1].strip()
    
    # Split dati in 1 byte per elemento
    chunks = split_into_chunks(hex_data, 1)
    
    return time, chunks


def mappare(line):
    # Processa la linea per ottenere il timestamp e i dati in chunks
    time, chunks = process_line(line)
    
    if len(chunks) < 24:
        print(f"Linea troppo corta, viene skippata: {time}")
        return None  # Salta la linea restituendo None
    
    # Mappa per immagazzinare i risultati
    result = {'time': time}
    
    # Header (primi 8 bytes)
    headers = chunks[:8]
    result['headers'] = headers
    
    # Frame (dal 9° al 16° byte)
    frame = chunks[8:12]
    result['frame'] = frame
    
    # TLV1 (dal 17° al 20° byte)
    tlv1 = ''.join(chunks[16:20])
    result['TLV1'] = tlv1
    
    # PointLength (dal 21° al 24° byte)
    point_length = int(''.join(chunks[20:24]), 16)
    result['PointL'] = f'{point_length:08X}'
    
    point_counter = 1
    
    # Iniziamo l'indice per i punti
    index = 24
    
    points = []
    
    while index < len(chunks):
        # Controlla se l'attuale chunk è 02 00 00 00
        if ''.join(chunks[index:index + 4]) == '02 00 00 00':
            # Trovato il segnale di fine punti (TLV2)
            break
        
        # Se non ci sono abbastanza bytes rimanenti, interrompiamo
        if index + 25 > len(chunks):
            break
        
        # Aggiungi i dati dei punti
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
        
        # Incrementa il contatore dei punti
        point_counter += 1
        
        # Incremento indice per i prossimi 25 bytes
        index += 25
    
    result['points'] = points
    
    return result


# Esempio di uso della funzione con la linea fornita
#line = "[11:27:18.234]IN¡û¡ô01 02 03 04 05 06 07 08 5F 02 00 00 38 00 00 00 01 00 00 00 3F 02 00 00 01 44 C1 3E 01 8F AC BF 8C 21 81 3F FA 3B 44 01 41 00 00 7F 43 98 55 0A 41 01 E0 DC 3E 01 5D BA BF 29 D0 51 3F FB 8F 5B A9 40 00 00 7F 43 29 01 CB 40 01 80 C7 3E 01 90 AE BF D6 ED 89 3F F9 F4 A0 07 41 00 00 7F 43 A1 56 E0 40 01 80 C7 3E 01 B0 B5 BF FB 65 80 3F FA B0 5C DD 41 00 00 7F 43 E7 E1 02 41 01 C0 D5 3E 01 B0 B5 BF 01 EA 7D 3F FB A6 25 97 41 00 00 7F 43 0A 5B 06 41 01 BC CD 3E 81 04 B4 BF 44 3D 8E 3F F9 AE 86 5A 41 00 00 7F 43 48 AC FA 40 01 6E DC 3E 01 58 B0 BF 06 6E 91 3F FA F2 BA 2B 42 00 00 7F 43 72 C6 FA 40 01 6E DC 3E 01 B1 B7 BF E9 07 88 3F FB 90 68 EF 41 00 00 7F 43 21 AE F4 40 01 40 F2 3E 01 E7 B1 BF B0 DD 98 3F F9 FB C8 51 41 00 00 7F 43 EC 13 F0 40 01 1C E3 3E 01 B0 B5 BF 35 D6 95 3F FA D4 9C 17 42 00 00 7F 43 04 7A F6 40 01 F8 D3 3E 01 B0 B5 BF 86 37 97 3F FB 6A 65 CC 41 00 00 7F 43 E0 B0 E9 40 01 60 F9 3E 01 08 BB BF DC B5 98 3F F9 88 C5 DC 40 00 00 7F 43 E3 7E E7 40 01 CA E9 3E 81 22 B7 BF B8 D9 9E 3F FA 45 AD 94 41 00 00 7F 43 B9 75 E4 40 01 CA E9 3E 81 22 B7 BF B8 D9 9E 3F FB 66 A7 41 41 00 00 7F 43 C7 78 CE 40 01 48 10 3F 01 5E BC BF B5 72 9E 3F FB 6A 99 B4 40 00 00 7F 43 35 0F C3 40 01 48 10 3F 02 60 C0 BF AB 8E 99 3F FC 1E F0 00 41 00 00 7F 43 A8 1E D5 40 01 4A 14 3F 01 3E B5 BF D3 7F B0 3F FB 4A B1 DB 40 00 00 7F 43 CF E7 EF 40 01 87 1C 3F 01 7B BD BF B6 BD A5 3F FC B1 A2 28 41 00 00 7F 43 B1 0F E6 40 01 C2 20 3F 02 4B CF BF 74 83 9A 3F FB 92 69 A1 40 00 00 00 00 24 9A E1 40 01 4C 18 3F 01 24 BA BF 02 45 B5 3F FC 24 76 0B 41 00 00 7F 43 2B 8A D8 40 01 A0 15 BE 02 70 E0 BF B6 0C C5 3F 03 DE 6A 58 40 00 00 7F 43 C6 50 EB 40 01 30 99 BD 81 FE E0 BF CC BA CF 3F 03 44 4E 76 40 00 00 7F 43 51 A2 FC 40 02 6C D8 3F 01 46 0C C0 14 7D 39 40 00 B4 08 5E 40 00 00 00 00 51 EF 32 41 02 00 00 00 00 00 00 00"
#mapped_data = mappare(line)
#print(mapped_data)

def process_file(file_path):
    """Processa un intero file e restituisce una lista di dizionari."""
    results = []
    
    with open(file_path, 'r') as file:
        for line in file:
            if line.strip():  # Ignora le righe vuote
                mapped_data = mappare(line)
                results.append(mapped_data)
    
    return results


def save_to_json(data, output_file):
    """Salva i dati in formato JSON in un file."""
    with open(output_file, 'w') as file:
        json.dump(data, file, indent=4)


# Esempio di utilizzo
#input_file = 'C:/Users/Ale/Downloads/Minew/Minew/SaveWindows02_09_2024_11-28-35.TXT'
#output_file = 'output.json'

# Processa il file e salva il risultato in JSON
#processed_data = process_file(input_file)
#save_to_json(processed_data, output_file)

#print(f'Dati salvati in {output_file}')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a hex data file and convert it to JSON.")
    parser.add_argument('input_file', type=str, help='The input TXT file to process')
    parser.add_argument('output_file', type=str, help='The output JSON file to save the results')

    args = parser.parse_args()

    # Processa il file e salva il risultato in JSON
    processed_data = process_file(args.input_file)
    save_to_json(processed_data, args.output_file)

    print(f'Dati salvati in {args.output_file}')