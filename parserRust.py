# Parser Avance 2 con PLY.yacc (subconjunto estilo Rust)
# println, entrada por teclado tipo io::stdin().read_line(...),
# expresiones aritméticas y lógicas, let/let mut (con o sin tipo e init),
# arrays, vec![], indexación, slices, cast, referencias (& y &mut),
# funciones (con/sin retorno) y return.

import argparse
import datetime
from pathlib import Path
import ply.yacc as yacc

# Traigo el lexer del Avance 1
import rustAnalizer
tokens = rustAnalizer.tokens
lexer  = rustAnalizer.lexer

# Precedencias básicas para quitar ambigüedades
precedence = (
    ('left', 'DISJUNCTION'),                         # ||
    ('left', 'CONJUNCTION'),                         # &&
    ('right', 'NOT'),                                # !
    ('nonassoc', 'EQUAL_TO', 'NOT_EQUAL',
                 'LESS_THAN', 'LESS_THAN_OR_EQUAL_TO',
                 'GREATER_THAN', 'GREATER_THAN_OR_EQUAL_TO'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE', 'MOD'),
    ('right', 'AS'),                                 # cast: expr as TYPE
)

ERRORES = []  # acumulo errores de parseo

# ---------------- Programa ----------------

def p_program(p):
    '''program : program sentencia
               | sentencia'''
    p[0] = p[1] + [p[2]] if len(p) == 3 else [p[1]]

def p_program_opt(p):
    '''program_opt : program
                   | empty'''
    p[0] = p[1] if p[1] is not None else []

def p_empty(p):
    'empty :'
    p[0] = None

# ---------------- Impresión ----------------
# println!("texto");
def p_println_string(p):
    'sentencia : PRINTLN NOT LPAREN STRING RPAREN SEMICOLON'
    p[0] = ("println", p[4])

# println!(expr);
def p_println_expr(p):
    'sentencia : PRINTLN NOT LPAREN expresion RPAREN SEMICOLON'
    p[0] = ("println_expr", p[4])

# ---------------- Entrada por teclado ----------------
# Acepto algo tipo: io::stdin().read_line(&mut nombre);
# Primero la llamada de path con ::
def p_path_call_noargs(p):
    'expresion : IDENTIFIER DOUBLE_COLON IDENTIFIER LPAREN RPAREN'
    # ej: io::stdin()
    p[0] = ("path_call", p[1], p[3], [])

# Luego método encadenado con o sin argumentos: expr.metodo(args)
def p_call_method(p):
    'expresion : expresion DOT IDENTIFIER LPAREN argumentos_opt RPAREN'
    p[0] = ("call", p[1], p[3], p[5])

def p_argumentos_opt(p):
    '''argumentos_opt : lista_argumentos
                      | empty'''
    p[0] = p[1] if p[1] is not None else []

def p_lista_argumentos(p):
    '''lista_argumentos : lista_argumentos COMMA expresion
                        | expresion'''
    p[0] = p[1] + [p[3]] if len(p) == 4 else [p[1]]

# ---------------- Expresiones ----------------

def p_exp_paren(p):
    'expresion : LPAREN expresion RPAREN'
    p[0] = p[2]

def p_exp_binaria(p):
    '''expresion : expresion PLUS expresion
                 | expresion MINUS expresion
                 | expresion TIMES expresion
                 | expresion DIVIDE expresion
                 | expresion MOD expresion'''
    p[0] = ("op", p[2], p[1], p[3])

def p_exp_unaria_not(p):
    'expresion : NOT expresion'
    p[0] = ("not", p[2])

def p_exp_literal_num(p):
    '''expresion : INTEGER
                 | FLOAT'''
    p[0] = ("num", p[1])

def p_exp_literal_str_char_bool(p):
    '''expresion : STRING
                 | CHAR
                 | BOOLEAN'''
    p[0] = ("lit", p[1])

def p_exp_ident(p):
    'expresion : IDENTIFIER'
    p[0] = ("id", p[1])

# &expr
def p_ref_unario(p):
    'expresion : BIT_AND expresion'
    p[0] = ("ref", p[2])

# &mut nombre
def p_ref_mut_ident(p):
    'expresion : BIT_AND MUT IDENTIFIER'
    p[0] = ("ref_mut", ("id", p[3]))

# cast: expr as TYPE
def p_cast_as(p):
    'expresion : expresion AS tipo'
    p[0] = ("cast", p[1], p[3])

# ---------------- Condiciones ----------------
def p_cond_rel(p):
    '''condicion : expresion EQUAL_TO expresion
                 | expresion NOT_EQUAL expresion
                 | expresion LESS_THAN expresion
                 | expresion GREATER_THAN expresion
                 | expresion LESS_THAN_OR_EQUAL_TO expresion
                 | expresion GREATER_THAN_OR_EQUAL_TO expresion'''
    p[0] = ("rel", p[2], p[1], p[3])

def p_cond_logica_bin(p):
    '''condicion : condicion CONJUNCTION condicion
                 | condicion DISJUNCTION condicion'''
    p[0] = ("logic", p[2], p[1], p[3])

def p_cond_logica_not(p):
    'condicion : NOT condicion'
    p[0] = ("not", p[2])

def p_cond_parentesis(p):
    'condicion : LPAREN condicion RPAREN'
    p[0] = p[2]

# if simple para pruebas
def p_if_simple(p):
    'sentencia : IF condicion LBRACE program_opt RBRACE'
    p[0] = ("if", p[2], p[4])

# ---------------- Tipos (anotaciones) ----------------
# Regla base: acepta cualquiera de los tipos definidos en el lexer
def p_tipo_base(p):
    '''tipo : TYPE_I32
            | TYPE_U64
            | TYPE_F64
            | TYPE_CHAR
            | TYPE_STRING
            | TYPE_BOOL
            | TYPE_TUPLE'''
    p[0] = ("type", p[1])

# Arreglo/slice anidado: [T]  (permite [i32], [[i32]], etc.)
def p_tipo_array_rec(p):
    'tipo : LBRACKET tipo RBRACKET'
    p[0] = ("type_array", p[2])

# Referencia: &T
def p_tipo_ref_rec(p):
    'tipo : BIT_AND tipo'
    p[0] = ("type_ref", p[2])

# Referencia mutable: &mut T
def p_tipo_ref_mut_rec(p):
    'tipo : BIT_AND MUT tipo'
    p[0] = ("type_ref_mut", p[3])

# ---------------- Declaraciones let ----------------
# Lo manejo con una regla general para soportar:
# let x;
# let x = expr;
# let x: T;
# let x: T = expr;
# let mut x = expr;
# let mut x: T = expr;

def p_sentencia_let(p):
    'sentencia : let_decl'
    p[0] = p[1]

def p_let_decl(p):
    'let_decl : LET maybe_mut IDENTIFIER maybe_type maybe_init SEMICOLON'
    ident = p[3]
    is_mut = p[2] is not None
    tipe   = p[4]           # None o ("type", ...)
    init   = p[5]           # None o ("init", expr)

    if tipe and init:
        p[0] = ("let_mut_typed_assign", ident, tipe, init[1]) if is_mut else ("let_typed_assign", ident, tipe, init[1])
    elif tipe and not init:
        p[0] = ("let_mut_typed_decl", ident, tipe) if is_mut else ("let_typed_decl", ident, tipe)
    elif init and not tipe:
        p[0] = ("let_mut_assign", ident, init[1]) if is_mut else ("let_assign", ident, init[1])
    else:
        p[0] = ("let_decl", ident)

def p_maybe_mut(p):
    '''maybe_mut : MUT
                 | empty'''
    p[0] = p[1] if p[1] is not None else None

def p_maybe_type(p):
    '''maybe_type : COLON tipo
                  | empty'''
    p[0] = p[2] if len(p) == 3 else None

def p_maybe_init(p):
    '''maybe_init : ASIGNED_TO expresion
                  | empty'''
    p[0] = ("init", p[2]) if len(p) == 3 else None

# ---------------- Arrays / vectores / slices ----------------

def p_lista_elementos(p):
    '''lista_elementos : lista_elementos COMMA expresion
                       | expresion'''
    p[0] = p[1] + [p[3]] if len(p) == 4 else [p[1]]

def p_array_literal(p):
    'expresion : LBRACKET lista_elementos RBRACKET'
    p[0] = ("array", p[2])

def p_array_repeat(p):
    'expresion : LBRACKET expresion SEMICOLON INTEGER RBRACKET'
    p[0] = ("array_repeat", p[2], p[4])

def p_index(p):
    'expresion : IDENTIFIER LBRACKET expresion RBRACKET'
    p[0] = ("index", ("id", p[1]), p[3])

def p_slice_open(p):
    'expresion : IDENTIFIER LBRACKET INTEGER RANGE INTEGER RBRACKET'
    p[0] = ("slice", ("id", p[1]), p[3], p[5], False)

def p_slice_inclusive(p):
    'expresion : IDENTIFIER LBRACKET INTEGER RANGE_INCLUSIVE INTEGER RBRACKET'
    p[0] = ("slice", ("id", p[1]), p[3], p[5], True)

def p_vec_macro(p):
    'expresion : IDENTIFIER NOT LBRACKET lista_elementos RBRACKET'
    # ej: vec![1,2,3]
    p[0] = ("vec_macro", p[1], p[4])

# 2do Avance Carlos Flores
# ---------------- Declaraciones const ----------------
# const NOMBRE: TIPO = expresion;

def p_sentencia_const(p):
    'sentencia : const_decl'
    p[0] = p[1]

def p_const_decl(p):
    '''const_decl : CONST IDENTIFIER COLON tipo ASIGNED_TO expresion SEMICOLON'''
    p[0] = ("const_decl", p[2], p[4], p[6])

# ---------------- Tuplas ----------------
# Tipo de tupla: (i32, f64, bool)
def p_tipo_tupla(p):
    '''tipo : LPAREN lista_tipos_tupla RPAREN'''
    p[0] = ("type_tuple", p[2])

def p_lista_tipos_tupla(p):
    '''lista_tipos_tupla : tipo
                         | tipo COMMA lista_tipos_tupla'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [p[1]] + p[3]


# Valor literal de tupla: (5, 3.14, true)
def p_exp_tupla_literal(p):
    '''expresion : LPAREN lista_valores_tupla RPAREN'''
    p[0] = ("tuple_literal", p[2])

def p_lista_valores_tupla(p):
    '''lista_valores_tupla : expresion
                           | expresion COMMA lista_valores_tupla'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [p[1]] + p[3]


# Acceso a elemento de tupla: mi_tupla.0
def p_exp_acceso_tupla(p):
    '''expresion : IDENTIFIER DOT INTEGER'''
    p[0] = ("tuple_access", ("id", p[1]), p[3])

# Fin 2do Avance Carlos Flores

# ---------------- Funciones y return ----------------

# opcional "pub" antes de fn: lo dejo genérico como IDENTIFIER para no complicar
def p_maybe_pub(p):
    '''maybe_pub : IDENTIFIER
                 | empty'''
    p[0] = p[1] if p[1] is not None else None

# nombre de función: main o IDENTIFIER cualquiera
def p_nombre_fn_ident(p):
    'nombre_fn : IDENTIFIER'
    p[0] = p[1]

def p_nombre_fn_main(p):
    'nombre_fn : MAIN'
    p[0] = p[1]

# fn con retorno: fn nombre() -> T { ... }
def p_funcion_con_retorno(p):
    'sentencia : maybe_pub FN nombre_fn LPAREN RPAREN MINUS GREATER_THAN tipo LBRACE program_opt RBRACE'
    p[0] = ("fn_ret", p[3], p[8], p[11])

# fn sin retorno: fn nombre() { ... }
def p_funcion_sin_retorno(p):
    'sentencia : maybe_pub FN nombre_fn LPAREN RPAREN LBRACE program_opt RBRACE'
    p[0] = ("fn", p[3], p[7])

def p_return(p):
    'sentencia : RETURN expresion SEMICOLON'
    p[0] = ("return", p[2])
    

# ---------------- Errores ----------------

def p_error(tok):
    if tok:
        msg = f"[ERROR] Sintaxis inválida en '{tok.value}' (línea {tok.lineno})"
    else:
        msg = "[ERROR] Fin de archivo inesperado"
    print(msg)
    ERRORES.append(msg)

# Construyo el parser
parser = yacc.yacc(start='program')

# ---------------- Runner + logs ----------------
import os

# Diccionario de archivos por usuario
archivos = {
    "Carlos Flores": ["algoritmoVariables.rs"],
    "Nicolas Sierra": ["algoritmoOperadores.rs"],
    "Carlos Tingo": ["algoritmoVectoresArreglos.rs"]
}

def analizar():
    ahora = datetime.datetime.now()
    fecha = ahora.strftime("%d-%m-%Y")
    hora = ahora.strftime("%Hh%M")

    # Recorre los archivos de cada persona
    for name, lista_archivos in archivos.items():
        carpeta = f"./logs/{name.replace(' ', '_')}"
        os.makedirs(carpeta, exist_ok=True)

        nombre_log = f"{carpeta}/sintactico-{name.replace(' ', '')}-{fecha}-{hora}.txt"
        with open(nombre_log, "w", encoding="utf-8") as log:
            log.write(f"===== Análisis Sintáctico ({fecha} - {hora}) =====\n\n")

            for archivo in lista_archivos:
                if not os.path.exists(archivo):
                    alerta = f"⚠️ ALERTA: El archivo '{archivo}' no existe.\n"
                    print(alerta.strip())
                    log.write(alerta + "\n")
                    continue

                with open(archivo, "r", encoding="utf-8") as file:
                    data = file.read()

                print(f"\n📂 Analizando archivo: {archivo}")
                log.write(f"=== Archivo: {archivo} ===\n")

                # Reinicia errores por archivo
                ERRORES.clear()
                lexer.lineno = 1

                try:
                    result = parser.parse(data, lexer=lexer)
                    if ERRORES:
                        log.write("❌ Errores sintácticos encontrados:\n")
                        for e in ERRORES:
                            log.write(f"   - {e}\n")
                        print(f"❌ Errores sintácticos en {archivo}")
                    else:
                        log.write("✅ Sin errores sintácticos.\n")
                        print(f"✅ {archivo} analizado correctamente.")
                except Exception as e:
                    error_msg = f"🔥 Error crítico al analizar {archivo}: {e}\n"
                    print(error_msg.strip())
                    log.write(error_msg)

                log.write("\n")

        print(f"📝 Log generado en: {nombre_log}\n")


if __name__ == "__main__":
    analizar()
