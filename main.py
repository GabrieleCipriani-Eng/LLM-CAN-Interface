import serial
import time
import numpy as np
from ai_engine import send_message_ai

# Inizializzazione variabili / Variable initialization
pressione_ant_dx=0
pressione_ant_sx=0
pressione_post_dx=0
pressione_post_sx=0

ultimo_rpm=0
ultima_vel=0
ultima_temp=0

# Buffer per medie mobili / Buffers for moving averages
lista_ultime_letture_rpm=[]
lista_ultime_letture_vel=[]
lista_ultime_letture_temp=[]
lista_ultime_letture_ant_dx=[]
lista_ultime_letture_ant_sx=[]
lista_ultime_letture_post_dx=[]
lista_ultime_letture_post_sx=[]
tempo_ultima_domanda=time.time()

print("Mi connetto all'Arduino... / Connecting to Arduino...")
porta=serial.Serial('COM5',115200,timeout=1)
time.sleep(2)

# Configurazione Lawicel / Lawicel configuration
porta.write(b'C\r') # Chiude il canale / Close channel
time.sleep(0.1)
porta.write(b'S6\r') # Imposta velocità 500kbps / Set speed to 500kbps
time.sleep(0.1)
porta.write(b'O\r') # Apre il canale / Open channel
print("Configurazione completata. Inizio lettura... / Setup complete. Starting read...\n")

try:
    while True:
        # Lettura linea grezza / Read raw line
        linea_grezza=porta.read_until(b'\r').decode('ascii',errors='ignore').strip()
        
        # Parsing dati Lawicel  / Lawicel data parsing 
        if linea_grezza.startswith('t316'): # RPM
            pezzo_alto=int(linea_grezza[5:7],16)
            pezzo_basso=int(linea_grezza[7:9],16)
            ultimo_rpm=(pezzo_alto*256)+pezzo_basso
            
        elif linea_grezza.startswith('t320'): # VEL
            ultima_vel=int(linea_grezza[5:7],16)
            
        elif linea_grezza.startswith('t324'): # TEMP
            ultima_temp=int(linea_grezza[5:7],16)
            
        elif linea_grezza.startswith('t421'): # PRESSIONI / PRESSURES
            # Conversione in float / Convert to float 
            pressione_ant_sx=int(linea_grezza[7:9],16)/10.0
            pressione_ant_dx=int(linea_grezza[9:11],16)/10.0
            pressione_post_sx=int(linea_grezza[11:13],16)/10.0
            pressione_post_dx=int(linea_grezza[13:15],16)/10.0
            
        # Aggiornamento buffer (max 30 campioni) / Buffer update (max 30 samples)
        lista_ultime_letture_rpm.append(ultimo_rpm)
        lista_ultime_letture_temp.append(ultima_temp)
        lista_ultime_letture_vel.append(ultima_vel)
        lista_ultime_letture_ant_sx.append(pressione_ant_sx)
        lista_ultime_letture_ant_dx.append(pressione_ant_dx)
        lista_ultime_letture_post_dx.append(pressione_post_dx)
        lista_ultime_letture_post_sx.append(pressione_post_sx)
        
        if len(lista_ultime_letture_rpm)>30:
            lista_ultime_letture_rpm.pop(0)
            lista_ultime_letture_temp.pop(0)
            lista_ultime_letture_vel.pop(0)
            lista_ultime_letture_ant_dx.pop(0)
            lista_ultime_letture_ant_sx.pop(0)
            lista_ultime_letture_post_dx.pop(0)
            lista_ultime_letture_post_sx.pop(0)

        tempo_attuale=time.time()
        
        # Intervallo IA (10 secondi) / AI interval (10 seconds)
        if (tempo_attuale-tempo_ultima_domanda)>10:
            print("\n"+"*"*50)
            
            # Calcolo medie / Calculate averages
            media_rpm=np.mean(lista_ultime_letture_rpm)
            media_temp=np.mean(lista_ultime_letture_temp)
            media_vel=np.mean(lista_ultime_letture_vel)
            media_ant_sx=np.mean(lista_ultime_letture_ant_sx)
            media_ant_dx=np.mean(lista_ultime_letture_ant_dx)
            media_post_sx=np.mean(lista_ultime_letture_post_sx)
            media_post_dx=np.mean(lista_ultime_letture_post_dx)
            
            # Log terminale / Terminal log
            print(f"Dati:{media_rpm:.0f}RPM|{media_vel:.0f}km/h|{media_temp:.1f}C|{media_ant_sx:.1f}bar|{media_ant_dx:.1f}bar|{media_post_sx:.1f}bar|{media_post_dx:.1f}bar")

            # Formattazione compatta per l'IA / Compact formatting for AI
            
            dato_attuale=f"RPM={media_rpm:.0f},TEMP={media_temp:.1f},VEL={media_vel:.0f},FL={media_ant_sx:.1f},FR={media_ant_dx:.1f},RL={media_post_sx:.1f},RR={media_post_dx:.1f}"
            
            # Invio all'IA / Sending to AI
            send_message_ai(dato_attuale,porta)
            
            tempo_ultima_domanda=time.time()

except KeyboardInterrupt:
    print("\nChiusura script... / Closing script...")
    porta.write(b'C\r') # Chiude CAN prima di uscire / Close CAN before exit
    porta.close()