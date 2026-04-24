#include <mcp_can.h>
#include <SPI.h>

const int spiCSPin=10;
MCP_CAN CAN(spiCSPin);

// Variabili Simulazione / Simulation Variables
int rpm=850;
int velocita=0;
bool accelerando=true;
bool sensore_pressione_pneumatici=true;
int tempDinamica=85;

float pressione_ant_sx=2.1;
float pressione_ant_dx=2.1;
float pressione_post_sx=2.0;
float pressione_post_dx=2.0;

int limiteRpmIA=10000;
int limiteVelIA=250;
unsigned long ultimoUpdateGomme=0;
unsigned long ultimoUpdateTemp=0;

void setup() {
    Serial.begin(115200);
    // Init CAN 500Kbps
    while(CAN_OK!=CAN.begin(MCP_ANY,CAN_500KBPS,MCP_8MHZ)){
        delay(100);
    }
    CAN.setMode(MCP_NORMAL);
}

// Formato Lawicel per Python / Lawicel format for Python
void stampaLawicel(int id,unsigned char* msg){
    Serial.print("t");
    Serial.print(id,HEX);
    Serial.print("8");
    for(int i=0;i<8;i++){
        if(msg[i]<16)Serial.print("0");
        Serial.print(msg[i],HEX);
    }
    Serial.print("\r");
}

void loop() {
    // 0. Ascolto Comandi IA / Listen for AI Commands
    if(CAN_MSGAVAIL==CAN.checkReceive()){
        long unsigned int rxId;
        unsigned char len=0;
        unsigned char rxBuf[8];
        CAN.readMsgBuf(&rxId,&len,rxBuf);

        if(rxId==0x316){ // Limite RPM
            limiteRpmIA=(rxBuf[0]*256)+rxBuf[1];
            Serial.print("L'IA ha imposto il limite RPM a: ");
            Serial.println(limiteRpmIA);
        }
        if(rxId==0x320){ // Limite VEL
            limiteVelIA=rxBuf[0];
            Serial.print("L'IA ha imposto il limite VEL a: ");
            Serial.print(limiteVelIA);
        }
    }

    // Reset automatico / Auto reset
    if(tempDinamica<98)limiteRpmIA=10000;
    if(pressione_ant_sx>=1.8)limiteVelIA=250;

    // 1. Logica Motore / Engine Logic
    if(accelerando){
        int incremento=map(rpm,1000,7000,50,20);
        rpm+=incremento+random(0,5);
        if(rpm>3000)velocita+=(rpm/2000);
        if(rpm>=7000||rpm>=limiteRpmIA)accelerando=false;
    }else{
        rpm-=120;
        if(velocita>0)velocita-=1;
        if(rpm<1200)accelerando=true;
    }

    if(rpm>limiteRpmIA)rpm=limiteRpmIA;
    if(velocita>limiteVelIA)velocita=limiteVelIA;

    // Gestione Temperatura (Aumento Randomico & Raffreddamento)
    if(millis()-ultimoUpdateTemp>250){
        if(limiteRpmIA<10000){
            // Se IA limita RPM, raffreddamento rapido
            if(tempDinamica>85&&random(0,10)>2)tempDinamica--;
        }else if(rpm>4500){
            // Aumento randomico ad alti giri
            if(tempDinamica<125&&random(0,10)>6)tempDinamica++;
        }else if(!accelerando){
            // Raffreddamento lento naturale
            if(tempDinamica>85&&random(0,10)>7)tempDinamica--;
        }
        ultimoUpdateTemp=millis();
    }

    // 2. Simulazione Gomme / Tire Simulation
    if(sensore_pressione_pneumatici&&(millis()-ultimoUpdateGomme>1500)){
        if(limiteVelIA<250){
            // Se IA limita VEL, le gomme si riposano e recuperano pressione
            if(pressione_ant_sx<2.1&&random(0,10)>4)pressione_ant_sx+=0.01;
            if(pressione_ant_dx<2.1&&random(0,10)>4)pressione_ant_dx+=0.01;
            if(pressione_post_sx<2.0&&random(0,10)>4)pressione_post_sx+=0.01;
            if(pressione_post_dx<2.0&&random(0,10)>4)pressione_post_dx+=0.01;
        }else{
            // Corsa normale, perdita pressione randomica
            if(pressione_ant_sx>0.0&&random(0,10)>5)pressione_ant_sx-=0.01;
            if(pressione_ant_dx>0.0&&random(0,10)>5)pressione_ant_dx-=0.01;
            if(pressione_post_sx>0.0&&random(0,10)>5)pressione_post_sx-=0.01;
            if(pressione_post_dx>0.0&&random(0,10)>5)pressione_post_dx-=0.01;
        }
        ultimoUpdateGomme=millis();
    }

    // 3. Invio Dati  / Data Transmission 
    
    // Pressioni / Pressures (0x421)
    unsigned char msgTyre[8];
    msgTyre[0]=0; // Stato sensore / Sensor status
    msgTyre[1]=(unsigned char)((pressione_ant_sx*10)+0.5);
    msgTyre[2]=(unsigned char)((pressione_ant_dx*10)+0.5);
    msgTyre[3]=(unsigned char)((pressione_post_sx*10)+0.5);
    msgTyre[4]=(unsigned char)((pressione_post_dx*10)+0.5);
    msgTyre[5]=0;
    msgTyre[6]=0;
    msgTyre[7]=0;
    CAN.sendMsgBuf(0x421,0,8,msgTyre);
   

    // RPM (0x316)
    unsigned char msgRPM[8];
    msgRPM[0]=(unsigned char)(rpm/256); // Byte alto / High byte
    msgRPM[1]=(unsigned char)(rpm%256); // Byte basso / Low byte
    msgRPM[2]=0;
    msgRPM[3]=0;
    msgRPM[4]=0;
    msgRPM[5]=0;
    msgRPM[6]=0;
    msgRPM[7]=0;
    CAN.sendMsgBuf(0x316,0,8,msgRPM);
   

    // VEL (0x320)
    unsigned char msgVEL[8];
    msgVEL[0]=(unsigned char)velocita;
    msgVEL[1]=0;
    msgVEL[2]=0;
    msgVEL[3]=0;
    msgVEL[4]=0;
    msgVEL[5]=0;
    msgVEL[6]=0;
    msgVEL[7]=0;
    CAN.sendMsgBuf(0x320,0,8,msgVEL);
   

    // TEMP (0x324)
    unsigned char msgTEMP[8];
    msgTEMP[0]=(unsigned char)tempDinamica;
    msgTEMP[1]=0;
    msgTEMP[2]=0;
    msgTEMP[3]=0;
    msgTEMP[4]=0;
    msgTEMP[5]=0;
    msgTEMP[6]=0;
    msgTEMP[7]=0;
    CAN.sendMsgBuf(0x324,0,8,msgTEMP);
    

    delay(35);
}