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
    'BIT_AND', 'BIT_XOR', 'BIT_NOT', 'SHIFT_LEFT', 'SHIFT_RIGHT',

    # AVANCE DE TOKENS PARA VARIABLES: Carlos Flores - INICIO
    'IDENTIFIER',    
    'TYPE_I32',
    'TYPE_U64',
    'TYPE_F64',
    'TYPE_CHAR',
    'TYPE_STRING',
    'TYPE_STR',
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
    'CLOSURE_PIPE',
    'ARROW',
    # AVANCE DE TOKENS PARA VARIABLES: Carlos Flores - FIN

    # AVANCE DELIMITADORES ARRAYS: Carlos Tingo - inicio
    'LBRACE', 'RBRACE',
    'LBRACKET', 'RBRACKET',
    'DOT',
    # Para arreglos/slices/paths:
    'RANGE', 'RANGE_INCLUSIVE', 'DOUBLE_COLON',
    # AVANCE DELIMITADORES ARRAYS: Carlos Tingo - fin

)+tuple(reserved.values())

# ============== ESTADOS PARA COMENTARIOS ==============
states = (
    ('blockcomment', 'exclusive'),
)

# Variable global para comentarios anidados
comment_depth = 0

# ============== COMENTARIOS ==============
# IMPORTANTE: El orden de estas reglas es crítico

# Comentario de documentación externa: ///
def t_DOC_COMMENT_OUTER(t):
    r'///[^\n]*'
    pass  # Ignorar (o procesar para generar docs)

# Comentario de documentación interna: //!
def t_DOC_COMMENT_INNER(t):
    r'//![^\n]*'
    pass  # Ignorar (o procesar para generar docs)

# Comentario de línea simple: //
def t_COMMENT_LINE(t):
    r'//[^\n]*'
    pass  # Ignorar completamente

# Inicio de comentario de bloque: /*
def t_BLOCKCOMMENT_start(t):
    r'/\*'
    global comment_depth
    comment_depth = 1
    t.lexer.push_state('blockcomment')

# Dentro del comentario de bloque: encontrar otro /*
def t_blockcomment_start(t):
    r'/\*'
    global comment_depth
    comment_depth += 1

# Dentro del comentario de bloque: encontrar */
def t_blockcomment_end(t):
    r'\*/'
    global comment_depth
    comment_depth -= 1
    if comment_depth == 0:
        t.lexer.pop_state()

# Dentro del comentario de bloque: contar saltos de línea
def t_blockcomment_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# Dentro del comentario de bloque: ignorar contenido
def t_blockcomment_content(t):
    r'[^/*\n]+'
    pass

# Dentro del comentario de bloque: ignorar / o * solos
def t_blockcomment_single(t):
    r'[/*]'
    pass

# Error en estado de comentario de bloque
def t_blockcomment_error(t):
    t.lexer.skip(1)

# ============== OPERADORES ARITMÉTICOS ==============
t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIVIDE = r'/'
t_MOD = r'%'

# ============== OPERADORES DE COMPARACIÓN ==============
t_EQUAL_TO = r'=='
t_NOT_EQUAL = r'!='
t_LESS_THAN_OR_EQUAL_TO = r'<='
t_GREATER_THAN_OR_EQUAL_TO = r'>='
t_LESS_THAN = r'<'
t_GREATER_THAN = r'>'

# ============== OPERADORES LÓGICOS ==============
t_CONJUNCTION = r'&&'
t_DISJUNCTION = r'\|\|'
t_NOT = r'!'

# ============== OPERADORES DE ASIGNACIÓN ==============
t_ASIGNED_TO = r'='
t_PLUS_EQUAL = r'\+='
t_MINUS_EQUAL = r'-='
t_TIMES_EQUAL = r'\*='
t_DIVIDE_EQUAL = r'/='
t_MOD_EQUAL = r'%='

# ============== OPERADORES BIT A BIT ==============
t_BIT_AND = r'&'
t_BIT_XOR = r'\^'
t_BIT_NOT = r'~'
t_SHIFT_LEFT = r'<<'
t_SHIFT_RIGHT = r'>>'

# ============== RANGOS Y SEPARADORES ==============
t_RANGE_INCLUSIVE = r'\.\.='   # ..=
t_RANGE           = r'\.\.'    # ..
t_DOT             = r'\.'      # .
t_DOUBLE_COLON    = r'::'      # ::

# ============== SIGNOS ==============
t_SEMICOLON = r'\;'
t_COLON = r'\:'
t_COMMA = r','
t_LPAREN  = r'\('
t_RPAREN  = r'\)'
t_ARROW = r'->'

# ============== DELIMITADORES ==============
t_LBRACE   = r'\{'
t_RBRACE   = r'\}'
t_LBRACKET = r'\['
t_RBRACKET = r'\]'

# Ignorar espacios y tabulaciones
t_ignore = ' \t'

# ============== LITERALES ==============

# Booleanos: true y false
def t_BOOLEAN(t):
    r'true|false'
    return t

# Caracteres: 'a', '\n', etc.
def t_CHAR(t):
    r"'(\\.|[^\\'])'"
    t.value = t.value[1:-1]
    return t

# Cadenas de texto: "hola mundo"
def t_STRING(t):
    r'\"([^\\\n]|(\\.))*?\"'
    t.value = t.value.strip('"')
    return t

# ============== TIPOS DE DATOS ==============

def t_TYPE_I32(t):
    r'i32'
    return t

def t_TYPE_U64(t):
    r'u64'
    return t

def t_TYPE_F64(t):
    r'f64'
    return t

def t_TYPE_CHAR(t):
    r'char'
    return t

def t_TYPE_STRING(t):
    r'String'
    return t

def t_TYPE_STR(t):
    r'str'
    return t

def t_TYPE_BOOL(t):
    r'bool'
    return t

def t_TYPE_TUPLE(t):
    r'tuple'
    return t

# ============== IDENTIFICADORES Y PALABRAS RESERVADAS ==============

def t_IDENTIFIER(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = reserved.get(t.value, 'IDENTIFIER')
    return t

# ============== NÚMEROS ==============

# Números decimales (flotantes)
def t_FLOAT(t):
    r'\d+\.\d+'
    t.value = float(t.value)
    return t

# Números enteros
def t_INTEGER(t):
    r'\d+'
    t.value = int(t.value)
    return t

# ============== SALTOS DE LÍNEA ==============

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# ============== PIPE PARA CLOSURES ==============

def t_CLOSURE_PIPE(t):
    r'\|(?!\|)'
    return t

# ============== MANEJO DE ERRORES ==============

def t_error(t):
    print("Lexical component '%s' does not exist in Rust language" % t.value[0])
    t.lexer.skip(1)

# ============== ARCHIVOS DE PRUEBA ==============
files = {
    "Carlos Flores": ["algo.rs"], 
    "Nicolas Sierra": ["algoritmoOperadores.rs"],    
    "Carlos Tingo": ["algoritmoVectoresArreglos.rs"]
}

# Build the lexer
lexer = lex.lex()

# ============== EJECUCIÓN ==============
if __name__ == "__main__":
    now = datetime.datetime.now()
    date = now.strftime("%d-%m-%Y")
    time = now.strftime("%Hh%M")

    for name, file_list in files.items():
        folder = f"./logs/{name.replace(' ', '_')}"
        os.makedirs(folder, exist_ok=True)

        log_name = f"{folder}/lexico-{name.replace(' ', '')}-{date}-{time}.txt"
        with open(log_name, "w", encoding="utf-8") as log:
            for file in file_list:
                if not os.path.exists(file):
                    print(f"ALERT: The file '{file}' does not exist.")
                else:
                    with open(file, "r", encoding="utf-8") as f:
                        for line_num, line in enumerate(f, start=1):
                            print(f"\nLine {line_num}: {line.strip()}")
                            log.write(f"\nLine {line_num}: {line.strip()}\n")
                            lexer.input(line)
                            while True:
                                tok = lexer.token()
                                if not tok:
                                    break
                                log_line = (
                                    f"[TOKEN] Type: {tok.type:<15} | "
                                    f"Value: {str(tok.value):<15} | "
                                    f"Line: {line_num:<3} | Position: {tok.lexpos}\n"
                                )
                                print(log_line.strip())
                                log.write(log_line)
