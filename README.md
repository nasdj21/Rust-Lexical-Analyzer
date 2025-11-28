# Rust-Lexical-Analyzer
Lexical, syntactic, and semantic analyzer for the Rust language using the PLY tool.

# 📘 Rust Analyzer – Dependencias e Instalación

Este proyecto incluye un **analizador léxico, sintáctico, semántico y una interfaz gráfica** para interpretar un subconjunto del lenguaje **Rust**.

## 📦 Librerías necesarias

Instala las dependencias ejecutando:

```bash
pip install ply
```

Tkinter viene incluido en Python para Windows y la mayoría de distribuciones.
Si no lo tienes en Linux, instala:

```bash
sudo apt-get install python3-tk
```

## ▶️ Ejecutar el proyecto

Desde la carpeta raíz:

```bash
python main.py
```

Esto abrirá la interfaz gráfica, donde podrás realizar:

* Análisis léxico
* Análisis sintáctico
* Análisis semántico
* Abrir y guardar archivos `.rs`

## 📁 Estructura básica

```
lexicalAnalyzer.py      # Analizador léxico
syntaxAnalyzer.py       # Analizador sintáctico
semanticAnalyzer.py     # Analizador semántico
main.py                 # Interfaz gráfica
logs/                   # Logs generados por usuario
ply/                    # Algoritmos de prueba
```


