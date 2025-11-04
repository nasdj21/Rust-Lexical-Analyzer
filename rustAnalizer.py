from ply import lex

reserved = {
    #AVANCE DE PALABRAS RESERVADAS: Nicolas Sierra - INICIO
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
    #AVANCE DE PALABRAS RESERVADAS: Nicolas Sierra - FIN
}

tokens = (
    #AVANCE DE OPERADORES: Nicolás Sierra - INICIO

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

    

)+tuple(reserved.values())



# OPERADORES ARITMÉTICOS

t_PLUS   = r'\+'
t_MINUS  = r'-'
t_TIMES  = r'\*'
t_DIVIDE = r'/'
t_MOD    = r'%'

# OPERADORES DE COMPARACIÓN

t_EQUAL_TO    = r'=='
t_NOT_EQUAL       = r'!='
t_LESS_THAN_OR_EQUAL_TO      = r'<='
t_GREATER_THAN_OR_EQUAL_TO   = r'>='
t_LESS_THAN       = r'<'
t_GREATER_THAN    = r'>'


# OPERADORES LÓGICOS

t_CONJUNCTION = r'&&'
t_DISJUNCTION   = r'\|\|'
t_NOT     = r'!'


# OPERADORES DE ASIGNACIÓN

t_ASIGNED_TO    = r'='
t_PLUS_EQUAL    = r'\+='
t_MINUS_EQUAL   = r'-='
t_TIMES_EQUAL   = r'\*='
t_DIVIDE_EQUAL  = r'/='
t_MOD_EQUAL     = r'%='


# OPERADORES BIT A BIT

t_BIT_AND     = r'&'
t_BIT_OR      = r'\|'
t_BIT_XOR     = r'\^'
t_BIT_NOT     = r'~'
t_SHIFT_LEFT  = r'<<'
t_SHIFT_RIGHT = r'>>'

# Ignorar espacios y tabulaciones
t_ignore = ' \t'

#Define los booleanos true y false
def t_BOOLEAN(t):
    r'true|false'
    return t

# Regla de manejo de errores
def t_error(t):
    print("Componente lexico '%s' no existe en el lenguaje Rust" % t.value[0])
    t.lexer.skip(1)

#AVANCE DE OPERADORES: Nicolás Sierra - FIN

#Definición de variables
def t_VARIABLE(t):
    r'[a-z]\w*'
    t.type = reserved.get(t.value, "VARIABLE") #Verifico que no haga match con alguna de las funciones reservadas
    return t
