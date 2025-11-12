from ply import lex
import datetime
import os

reserved = {
    # AVANCE DE PALABRAS RESERVADAS: Nicolas Sierra - INICIO
    'as': 'AS',
    'break': 'BREAK',
    'const': 'CONST',
    'continue': 'CONTINUE',
    'enum': 'ENUM',
    'loop': 'LOOP',
    'where': 'WHERE',
    'let': 'LET',
    'mut': 'MUT',
    'if': 'IF',
    'else': 'ELSE',
    'while': 'WHILE',
    'return': 'RETURN',
    'match': 'MATCH',
    'then': 'THEN',
    'main': 'MAIN',
    'println': 'PRINTLN',
    'fn':'FN',        
    'for':'FOR',
    'in':'IN',
    'async':'ASYNC'

    # AVANCE DE PALABRAS RESERVADAS: Nicolas Sierra - FIN
}

tokens = (
    # AVANCE DE OPERADORES: Nicolás Sierra - INICIO

    # Aritméticos
    'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MOD',

    # Comparación
    'EQUAL_TO', 'NOT_EQUAL', 'LESS_THAN', 'GREATER_THAN',
    'LESS_THAN_OR_EQUAL_TO', 'GREATER_THAN_OR_EQUAL_TO',

    # Lógicos
    'CONJUNCTION', 'DISJUNCTION', 'NOT',

    # Asignación
    'ASIGNED_TO', 'PLUS_EQUAL', 'MINUS_EQUAL', 'TIMES_EQUAL', 'DIVIDE_EQUAL', 'MOD_EQUAL',

    # Bit a bit
    'BIT_AND', 'BIT_OR', 'BIT_XOR', 'BIT_NOT', 'SHIFT_LEFT', 'SHIFT_RIGHT',

    # AVANCE DE TOKENS PARA VARIABLES: Carlos Flores - INICIO
    'IDENTIFIER',    
    'TYPE_I32',
    'TYPE_U64',
    'TYPE_F64',
    'TYPE_CHAR',
    'TYPE_STRING',
    'TYPE_BOOL',
    'TYPE_TUPLE',
    'SEMICOLON',
    'COLON',
    'STRING',
    'COMMA',
    'CHAR',
    'LPAREN',
    'RPAREN',
    'BOOLEAN',
    'INTEGER',
    'FLOAT',    
    'PIPE',
    'ARROW',
    # AVANCE DE TOKENS PARA VARIABLES: Carlos Flores - FIN

    # AVANCE DELIMITADORES ARRAYS: Carlos TIngo - inicio
    'LBRACE', 'RBRACE',
    'LBRACKET', 'RBRACKET',
    'DOT',
    # Para arreglos/slices/paths:
    'RANGE', 'RANGE_INCLUSIVE', 'DOUBLE_COLON',
    # AVANCE DELIMITADORES ARRAYS: Carlos TIngo - fin

)+tuple(reserved.values())

# OPERADORES ARITMÉTICOS
t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIVIDE = r'/'
t_MOD = r'%'

# OPERADORES DE COMPARACIÓN
t_EQUAL_TO = r'=='
t_NOT_EQUAL = r'!='
t_LESS_THAN_OR_EQUAL_TO = r'<='
t_GREATER_THAN_OR_EQUAL_TO = r'>='
t_LESS_THAN = r'<'
t_GREATER_THAN = r'>'

# OPERADORES LÓGICOS
t_CONJUNCTION = r'&&'
t_DISJUNCTION = r'\|\|'
t_NOT = r'!'

# OPERADORES DE ASIGNACIÓN
t_ASIGNED_TO = r'='
t_PLUS_EQUAL = r'\+='
t_MINUS_EQUAL = r'-='
t_TIMES_EQUAL = r'\*='
t_DIVIDE_EQUAL = r'/='
t_MOD_EQUAL = r'%='

# OPERADORES BIT A BIT
t_BIT_AND = r'&'
t_BIT_OR = r'\|'
t_BIT_XOR = r'\^'
t_BIT_NOT = r'~'
t_SHIFT_LEFT = r'<<'
t_SHIFT_RIGHT = r'>>'



# Rangos y ::  (el ORDEN importa: primero ..=, luego .., luego ::, luego . y :)
t_RANGE_INCLUSIVE = r'\.\.='   # ..=
t_RANGE           = r'\.\.'    # ..
t_DOT             = r'\.'      #.
t_DOUBLE_COLON    = r'::'      # ::




# AVANCE SIGNOS: Carlos Flores - INICIO
# SIGNOS
t_SEMICOLON = r'\;'
t_COLON = r'\:'
t_COMMA = r','
t_LPAREN  = r'\('
t_RPAREN  = r'\)'
t_PIPE = r'\|'
t_ARROW = r'->'
# AVANCE SIGNOS: Carlos Flores - FIN

#AVANCE ARRAY CARLOS TINGO - Inicio
t_LBRACE   = r'\{'
t_RBRACE   = r'\}'
t_LBRACKET = r'\['
t_RBRACKET = r'\]'




#AVANCE ARRAY CARLOS TINGO - Fin


# Ignorar espacios y tabulaciones
t_ignore = ' \t'

# Define los booleanos true y false
def t_BOOLEAN(t):
    r'true|false'
    return t

# Regla de manejo de errores
def t_error(t):
    print("Componente lexico '%s' no existe en el lenguaje Rust" % t.value[0])
    t.lexer.skip(1)

# AVANCE DE OPERADORES: Nicolás Sierra - FIN

# AVANCE PARA DEFINIR VARIABLES: Carlos Flores - INICIO
# Regla para cadenas de texto (entre comillas)
def t_CHAR(t):
    r"'(\\.|[^\\'])'"
    t.value = t.value[1:-1]  # elimina las comillas simples
    return t

#Regla para String
def t_STRING(t):
    r'\"([^\\\n]|(\\.))*?\"'
    t.value = t.value.strip('"')
    return t

# Regla para tipo de datos i32
def t_TYPE_I32(t):
    r'i32'
    return t

# Regla para tipo de datos u64
def t_TYPE_U64(t):
    r'u64'
    return t

# Regla para tipo de datos f64
def t_TYPE_F64(t):
    r'f64'
    return t

# Regla para tipo de datos char
def t_TYPE_CHAR(t):
    r'char'
    return t

# Regla para tipo de datos String
def t_TYPE_STRING(t):
    r'String'
    return t

# Regla para tipo de datos bool
def t_TYPE_BOOL(t):
    r'bool'
    return t

# Regla para tipo de datos tupla
def t_TYPE_TUPLE(t):
    r'tuple'
    return t

# Regla para identificar variables en Rust
def t_IDENTIFIER(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = reserved.get(t.value, 'IDENTIFIER')
    return t

# Regla para identificar números decimales
def t_FLOAT(t):
    r'\d+\.\d+'
    t.value = float(t.value)
    return t

# Regla para identificar números enteros
def t_INTEGER(t):
    r'\d+'
    t.value = int(t.value)
    return t

# Regla para identificar saltos de línea
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)
# AVANCE PARA DEFINIR VARIABLES: Carlos Flores - FIN


# Give the lexer some input
archivos = {"Carlos Flores":["algoritmoVariables.rs"], 
            "Nicolas Sierra":["algoritmoOperadores.rs"],    
            "Carlos Tingo":["algoritmoVectoresArreglos.rs"]}

# Build the lexer
lexer = lex.lex()

if __name__ == "__main__":
    ahora = datetime.datetime.now()
    fecha = ahora.strftime("%d-%m-%Y")
    hora = ahora.strftime("%Hh%M")

    for name, lista_archivos in archivos.items():
        carpeta = f"./logs/{name.replace(' ', '_')}"
        os.makedirs(carpeta, exist_ok=True)

        nombre_log = f"{carpeta}/lexico-{name.replace(' ', '')}-{fecha}-{hora}.txt"
        with open(nombre_log, "w", encoding="utf-8") as log:
            for archivo in lista_archivos:
                if not os.path.exists(archivo):
                    print(f"ALERTA: El archivo '{archivo}' no existe.")
                else:
                    with open(archivo, "r", encoding="utf-8") as file:
                        for num_linea, linea in enumerate(file, start=1):
                            print(f"\nLínea {num_linea}: {linea.strip()}")
                            log.write(f"\nLínea {num_linea}: {linea.strip()}\n")
                            lexer.input(linea)
                            while True:
                                tok = lexer.token()
                                if not tok:
                                    break
                                linea_log = (
                                    f"[TOKEN] Tipo: {tok.type:<15} | "
                                    f"Valor: {str(tok.value):<15} | "
                                    f"Línea: {num_linea:<3} | Posición: {tok.lexpos}\n"
                                )
                                print(linea_log.strip())
                                log.write(linea_log)