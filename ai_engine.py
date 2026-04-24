import ollama
from message_send import send_can_message 
import time
import re
from ollama import Client
client = Client(host='http://localhost:11434')

def send_message_ai(dato_attuale, porta):
    
    # PROMPT IA
    
    storia_messaggi = [
        {
            'role': 'system',
            'content': '''YOU ARE AN ADVANCED AI ECU CONTROLLER. You evaluate telemetry and make dynamic safety decisions.

            CRITICAL MATHEMATICAL ANCHORS:
            - SAFE TIRE VALUES: 1.5, 1.6, 1.7, 1.8, 1.9, 2.0, 2.1, 2.2+
            - DANGEROUS TIRE VALUES: 1.4, 1.3, 1.2, 1.1, 1.0, 0.9, 0.8, 0.7...

            BOUNDARIES & RULES (EVALUATE IN ORDER):
            1. TIRE EMERGENCY: 
               Condition: IF ANY tire is < 1.5 bar.
               Action: Calculate a dynamic speed reduction between 40% (mild risk) and 60% (extreme risk).
               Output: L_VEL:[percentage]
               
            2. ENGINE OVERHEAT: 
               Condition: IF ALL tires are SAFE (>= 1.5) BUT TEMP > 100.
               Action: Calculate dynamic RPM limit.
               Output: LIMITA:[rpm]
               
            3. ALL CLEAR: 
               Condition: IF ALL tires >= 1.5 AND TEMP <= 100.
               Output: OK

            STRICT OUTPUT FORMAT (2 LINES ONLY):
            Line 1: State the lowest tire pressure, confirm if it is (SAFE) or (DANGEROUS), and state the TEMP.
            Line 2: CRITICAL RULE -> If Line 1 says "(SAFE)" for both, YOU MUST OUTPUT EXACTLY "OK". DO NOT output L_VEL or LIMITA. If DANGEROUS, output L_VEL:XX. If OVERHEAT, output LIMITA:XXXX.
            
            EXAMPLES OF CORRECT REASONING:
            
            Input: 5006RPM|216km/h|83.0C|1.7bar|1.7bar|1.6bar|1.6bar
            Lowest tire is 1.6 (SAFE), Temp is 83.0C (SAFE). All clear.
            OK
            
            Input: 3888RPM|171km/h|84.0C|1.6bar|1.6bar|1.5bar|1.5bar
            Lowest tire is 1.5 (SAFE), Temp is 84.0C (SAFE). All clear.
            OK
            
            Input: 6922RPM|120km/h|84.0C|1.5bar|1.5bar|1.4bar|1.4bar
            Lowest tire is 1.4 (DANGEROUS). Severe reduction needed.
            L_VEL:58
            
            Input: 6000RPM|150km/h|105.0C|2.0bar|2.0bar|2.0bar|2.0bar
            Lowest tire is 2.0 (SAFE), Temp is 105.0C (OVERHEAT). Mild RPM limit.
            LIMITA:4000'''
        },
        {
            'role': 'user', 
            'content': f"Input: {dato_attuale}\nOutput:" 
        }
    ]

    try:
        porta.reset_input_buffer()
        
        # Invio Comandi
        risposta=client.chat(
            model='llama3.1',
            messages=storia_messaggi,
            options={
                'temperature':0.1, 
                'num_predict':60   
            }
        )
        
        testo_risposta=risposta['message']['content'].strip().upper()
        
        # Dividiamo la risposta in righe/ Let's divide the answer into lines
        righe=testo_risposta.strip().split('\n')
        
        if len(righe)>0:
            print(f"Decisione IA: {righe[0]}") 
            
        ultima_riga=righe[-1] # Prendiamo l ultima riga/select last row

        
        if "L_VEL:" in ultima_riga:
            try:
                #divido la stringa in 2/split the string in 2 and select the last string 
                parte_destra=ultima_riga.split("L_VEL:")[-1]
                
                
                solo_numero=''.join(filter(str.isdigit, parte_destra))
                
                target_vel=int(solo_numero)
                
                    
                print(f" EMERGENZA GOMME: {target_vel} Km/h")
                send_can_message(porta, 0x320, [target_vel, 0, 0, 0, 0, 0, 0, 0])
            except Exception as e:
                print(f" Errore conversione L_VEL: {e}")

        elif "LIMITA:" in ultima_riga:
            try:
                
                parte_destra=ultima_riga.split("LIMITA:")[-1]
                
               
                solo_numero=''.join(filter(str.isdigit, parte_destra))
                
                target_rpm=int(solo_numero)
                
               
                
                print(f"PROTEZIONE MOTORE: {target_rpm} RPM")
                # divisione in byte e invio/division into bytes and send
                byte_alto=(target_rpm>>8) & 0xFF
                byte_basso=target_rpm & 0xFF
                send_can_message(porta, 0x316, [byte_alto, byte_basso, 0, 0, 0, 0, 0, 0])
            except Exception as e:
                print(f" Errore conversione LIMITA: {e}")
                
        else:
            if "OK" in ultima_riga:
                print("IA: OK (Parametri nei limiti)")
            else:
                print(f"Comando non riconosciuto: {ultima_riga}")

        porta.reset_input_buffer()
        time.sleep(0.1)
        print("*"*50+"\n")
        
    except Exception as e:
        print(f"Errore IA: {e}")