# LLM-CAN-Interface

This project implements an **Intelligent Safety Controller** for automotive applications. It monitors real-time vehicle telemetry and uses a local Large Language Model (Llama 3.1) to make autonomous decisions, intervening on the CAN-BUS to protect the engine or ensure vehicle stability.

---

##  Hardware Stack
- **USB-CAN Interface:** [WeAct Studio USB to CAN/CANFD Module](https://github.com/WeActStudio/WeActStudio.USB-CANFD-Module)
- **Chipset:** STM32G4 (MCP2515 emulation via SLCAN)
- **AI Acceleration:** NVIDIA GeForce RTX 3060 Laptop GPU (6GB VRAM)
- **Protocol:** SLCAN (Lawicel) @ 500kbps

---

##  AI Engine
The system uses **Ollama** running in a Docker container with GPU pass-through.
- **Model:** `llama3.1:latest` (8B parameters)
- **Inference Latency:** ~200-500ms (on RTX 3060)
- **Logic:** The AI evaluates RPM, Speed, Temperature, and 4-wheel tire pressures to determine if the vehicle is within safe operating boundaries.

---

##  CAN-BUS Protocol Details
The system emulates an ECU bridge, sending specific commands based on AI reasoning:

| CAN ID | Data Format (HEX) | Description | Trigger |
| :--- | :--- | :--- | :--- |
| **0x316** | `[HighByte][LowByte][0...0]` | **RPM Limiter** | Engine Overheat (>100°C) |
| **0x320** | `[SpeedLimit][0...0]` | **Speed Limiter** | Low Tire Pressure (<1.5 bar) |

###  SLCAN Command Examples:
- `t31680BB8000000000000`: Sets RPM limit to **3000** (Hex `0BB8`).
- `t32083400000000000000`: Sets Speed limit to **52 km/h** (Hex `34`).

---

##  Project Structure
- `main.py`: Handles serial communication with the WeAct module and data buffering.
- `ai_engine.py`: Manages the prompt engineering and Ollama API communication.
- `message_send.py`: Formats and sends Lawicel/SLCAN commands to the hardware.
- `docker-compose.yml`: Orchestrates the AI environment with GPU support.

---

##  Getting Started

### 1. Requirements
- Docker Desktop with NVIDIA Container Toolkit.
- Python 3.10+
- WeAct USB-CAN Module connected to `COM5` (or update in `main.py`).

### 2. Launch the AI Engine

Command: docker-compose up -d



---

### Launch the ECU Application
pip install -r requirements.txt
python main.py

---

### Real-Time Intervention Examples


#### Example A: Engine Protection (Overheat)
* **Input Data:** `3500RPM | 150km/h | 115.0C | 2.0bar | 2.0bar | 2.0bar | 2.0bar`
* **AI Reasoning:** > "Temp is 115.0C (OVERHEAT). Mild RPM limit required."
* **Action:** `LIMITA:4000`
* **CAN-BUS Command:** `t31680BB8000000000000` (Sent via ID `0x316`)

#### Example B: Tire Emergency (Low Pressure)
* **Input Data:** `3419RPM | 212km/h | 95.0C | 1.7bar | 1.5bar | 1.4bar | 1.5bar`
* **AI Reasoning:** > "Lowest tire is 1.4 (DANGEROUS). Severe speed reduction needed."
* **Action:** `L_VEL:52`
* **CAN-BUS Command:** `t32083400000000000000` (Sent via ID `0x320`)

--- 
## Intellectual Property & Rights
**© 2026. All Rights Reserved.**

This software, the integration logic between LLM and CAN-BUS, and the contained prompt engines are the intellectual property of the author.

* **Permitted Use:** This code is provided solely for educational, study, or testing purposes in Hardware-in-the-Loop (HIL) simulation environments.
* **Restrictions:** Unauthorized reproduction, distribution, or commercial use of this software without explicit written consent is strictly prohibited.
* **Usage:** Do not use this software for purposes other than those illustrated. Do not use on public roads or real vehicles without necessary safety certifications.