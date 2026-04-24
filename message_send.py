# Funzione per l'invio del messaggio sul CAN
def send_can_message(porta,id, data):
    id_str = f"{id:03X}"
    dlc = len(data)
    data_str = "".join(f"{b:02X}" for b in data) # Dati in HEX con padding automatico
    command = f"t{id_str}{dlc}{data_str}\r" 
    porta.write(command.encode())
    print(f"Comando fisico inviato al CAN-BUS: {command.strip()}")
