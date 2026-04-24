#!/bin/bash


ollama serve &


echo "Attendendo l'avvio di Ollama..."
sleep 5


echo "Controllo modello llama3.1..."
ollama pull llama3.1


wait