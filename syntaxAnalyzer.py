# Parser Avance 2 con PLY.yacc (subconjunto estilo Rust)
# println, entrada por teclado tipo io::stdin().read_line(...),
# expresiones aritméticas y lógicas, let/let mut (con o sin tipo e init),
# arrays, vec![], indexación, slices, cast, referencias (& y &mut),
# funciones (con/sin retorno), return y CLOSURES/LAMBDAS.

import argparse
import datetime
from pathlib import Path
import ply.yacc as yacc
import os

# Traigo el lexer del Avance 1
import lexicalAnalyzer
tokens = lexicalAnalyzer.tokens
lexer  = lexicalAnalyzer.lexer

# Precedencias básicas para quitar ambigüedades
precedence = (
    ('left', 'DISJUNCTION'),                         # ||
    ('left', 'CONJUNCTION'),                         # &&
    ('right', 'NOT'),                                # !
    ('nonassoc', 'EQUAL_TO', 'NOT_EQUAL',
                 'LESS_THAN', 'LESS_THAN_OR_EQUAL_TO',
                 'GREATER_THAN', 'GREATER_THAN_OR_EQUAL_TO'),
    ('nonassoc', 'RANGE', 'RANGE_INCLUSIVE'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE', 'MOD'),
    ('right', 'AS'),                                 # cast: expr as TYPE
    ('right', 'UMINUS'),                             # unary minus
)

ERRORS = []  # acumulo errores de parseo

# ---------------- Programa ----------------

def p_program(p):
    '''program : program statement
               | statement'''
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
    'statement : PRINTLN NOT LPAREN STRING RPAREN SEMICOLON'
    p[0] = ("println", p[4])

# println!(expr);
def p_println_expr(p):
    'statement : PRINTLN NOT LPAREN expression RPAREN SEMICOLON'
    p[0] = ("println_expr", p[4])

def p_println_format(p):
    '''statement : PRINTLN NOT LPAREN STRING COMMA argument_list RPAREN SEMICOLON'''    
    p[0] = ("println_format", p[4], p[6])

# ---------------- HashMap ----------------
#Avance de hashmaps por Nicolás Sierra
def p_hashmap_insert(p):
    'expression : expression DOT IDENTIFIER LPAREN expression COMMA expression RPAREN'

    if p[3] == 'insert':
        p[0] = ("hashmap_insert", p[1], p[5], p[7])
    else:
        p[0] = ("call", p[1], p[3], [p[5], p[7]])

def p_hashmap_get(p):
    'expression : expression DOT IDENTIFIER LPAREN expression RPAREN'
    if p[3] == 'get':
        p[0] = ("hashmap_get", p[1], p[5])
    else:
        p[0] = ("call", p[1], p[3], [p[5]])

# ---------------- Entrada por teclado ----------------
# Acepto algo tipo: io::stdin().read_line(&mut nombre);
# Primero la llamada de path con ::
def p_path_call_noargs(p):
    'expression : IDENTIFIER DOUBLE_COLON IDENTIFIER LPAREN RPAREN'
    if p[1] == 'HashMap' and p[3] == 'new':
        #HashMap::new() 
        p[0] = ("hashmap_new", [])
    else:
        # ej: io::stdin()
        p[0] = ("path_call", p[1], p[3], [])

def p_expr_stmt(p):
    'statement : expression SEMICOLON'
    p[0] = ("expr_stmt", p[1])

# Luego método encadenado con o sin argumentos: expr.metodo(args)
def p_call_method(p):
    'expression : expression DOT IDENTIFIER LPAREN arguments_opt RPAREN'
    p[0] = ("call", p[1], p[3], p[5])

def p_arguments_opt(p):
    '''arguments_opt : argument_list
                      | empty'''
    p[0] = p[1] if p[1] is not None else []

def p_argument_list(p):
    '''argument_list : argument_list COMMA expression
                        | expression'''
    p[0] = p[1] + [p[3]] if len(p) == 4 else [p[1]]

# ---------------- CLOSURES/LAMBDAS ----------------

# Parámetros del closure
def p_closure_params_empty(p):
    'closure_params : '
    p[0] = []

def p_closure_params_single(p):
    'closure_params : IDENTIFIER'
    p[0] = [("param", p[1], None)]

def p_closure_params_single_typed(p):
    'closure_params : IDENTIFIER COLON type'
    p[0] = [("param", p[1], p[3])]

def p_closure_params_multiple(p):
    'closure_params : IDENTIFIER COMMA closure_params'
    p[0] = [("param", p[1], None)] + p[3]

def p_closure_params_multiple_typed(p):
    'closure_params : IDENTIFIER COLON type COMMA closure_params'
    p[0] = [("param", p[1], p[3])] + p[5]

# Cuerpo del closure: expresión simple (sin llaves)
def p_closure_body_expr(p):
    'closure_body : expression'
    p[0] = ("expr_body", p[1])

# Cuerpo del closure: bloque { expr } o { statements; expr }
def p_closure_body_block(p):
    'closure_body : LBRACE closure_block_content RBRACE'
    p[0] = p[2]

# Contenido del bloque: puede ser solo expresión o statements + expresión
def p_closure_block_content_expr(p):
    'closure_block_content : expression'
    p[0] = ("block_body", [], p[1])  # sin statements previos

def p_closure_block_content_stmts_expr(p):
    'closure_block_content : program expression'
    p[0] = ("block_body", p[1], p[2])  # con statements previos

def p_closure_block_content_stmts(p):
    'closure_block_content : program_opt'
    p[0] = ("block_body", p[1], None)  # solo statements, sin expresión final

# Closure SIN tipo de retorno
def p_expression_closure(p):
    'expression : CLOSURE_PIPE closure_params CLOSURE_PIPE closure_body'
    p[0] = ("closure", p[2], None, p[4])

# Closure CON tipo de retorno
def p_expression_closure_ret(p):
    'expression : CLOSURE_PIPE closure_params CLOSURE_PIPE ARROW type closure_body'
    p[0] = ("closure", p[2], p[5], p[6])

# ---------------- Expresiones ----------------
def p_exp_paren(p):
    'expression : LPAREN expression RPAREN'
    p[0] = p[2]

def p_exp_binary(p):
    '''expression : expression PLUS expression
                 | expression MINUS expression
                 | expression TIMES expression
                 | expression DIVIDE expression
                 | expression MOD expression'''
    p[0] = ("op", p[2], p[1], p[3])

def p_exp_range(p):
    '''expression : expression RANGE expression
                  | expression RANGE_INCLUSIVE expression'''
    inclusive = (p[2] == '..=')
    p[0] = ("range", p[1], p[3], inclusive)

def p_exp_relational(p):
    '''expression : expression EQUAL_TO expression
                  | expression NOT_EQUAL expression
                  | expression LESS_THAN expression
                  | expression GREATER_THAN expression
                  | expression LESS_THAN_OR_EQUAL_TO expression
                  | expression GREATER_THAN_OR_EQUAL_TO expression'''
    p[0] = ("rel", p[2], p[1], p[3])

def p_exp_logic(p):
    '''expression : expression CONJUNCTION expression
                  | expression DISJUNCTION expression'''
    p[0] = ("logic", p[2], p[1], p[3])

def p_exp_unary_not(p):
    'expression : NOT expression'
    p[0] = ("not", p[2])

def p_exp_unary_minus(p):
    'expression : MINUS expression %prec UMINUS'
    p[0] = ("uminus", p[2])

def p_exp_literal_num(p):
    '''expression : INTEGER
                 | FLOAT'''
    p[0] = ("num", p[1])

def p_exp_literal_str_char_bool(p):
    '''expression : STRING
                 | CHAR
                 | BOOLEAN'''
    p[0] = ("lit", p[1])

def p_exp_ident(p):
    'expression : IDENTIFIER'
    p[0] = ("id", p[1])

# &expr
def p_ref_unary(p):
    'expression : BIT_AND expression'
    p[0] = ("ref", p[2])

# &mut nombre
def p_ref_mut_ident(p):
    'expression : BIT_AND MUT IDENTIFIER'
    p[0] = ("ref_mut", ("id", p[3]))

# cast: expr as TYPE
def p_cast_as(p):
    'expression : expression AS type'
    p[0] = ("cast", p[1], p[3])

# ---------------- Condiciones ----------------
def p_cond_rel(p):
    '''condition : expression EQUAL_TO expression
                 | expression NOT_EQUAL expression
                 | expression LESS_THAN expression
                 | expression GREATER_THAN expression
                 | expression LESS_THAN_OR_EQUAL_TO expression
                 | expression GREATER_THAN_OR_EQUAL_TO expression'''
    p[0] = ("rel", p[2], p[1], p[3])

def p_cond_logic_bin(p):
    '''condition : condition CONJUNCTION condition
                 | condition DISJUNCTION condition'''
    p[0] = ("logic", p[2], p[1], p[3])

def p_cond_logic_not(p):
    'condition : NOT condition'
    p[0] = ("not", p[2])

def p_cond_parenthesis(p):
    'condition : LPAREN condition RPAREN'
    p[0] = p[2]

def p_cond_expression(p):
    'condition : expression'
    p[0] = p[1]

def p_cond_boolean(p):
    'condition : BOOLEAN'
    p[0] = ("bool", p[1])

# if simple para pruebas (usa expression en vez de condition)
def p_if_simple(p):
    'statement : IF expression LBRACE program_opt RBRACE'
    p[0] = ("if", p[2], p[4])

def p_if_else(p):
    'statement : IF expression LBRACE program_opt RBRACE ELSE LBRACE program_opt RBRACE'
    p[0] = ("if_else", p[2], p[4], p[8])

# ---------------- Asignación simple: identificador = expresión; ----------------
def p_assignment(p):
    'statement : IDENTIFIER ASIGNED_TO expression SEMICOLON'
    p[0] = ("assignment", p[1], p[3])

# ---------------- Bucle while (usa expression) ----------------
def p_while(p):
    'statement : WHILE expression LBRACE program_opt RBRACE'
    p[0] = ("while", p[2], p[4])

# ---------------- Funciones async ----------------
def p_function_with_return_async(p):
    'statement : ASYNC FN function_name LPAREN param_list_opt RPAREN ARROW type LBRACE function_body RBRACE'
    p[0] = ("async_fn_ret", p[3], p[5], p[8], p[10])

def p_function_without_return_async(p):
    'statement : ASYNC FN function_name LPAREN param_list_opt RPAREN LBRACE program_opt RBRACE'
    p[0] = ("async_fn", p[3], p[5], p[8])

# ---------------- Tipos (anotaciones) ----------------
def p_type_base(p):
    '''type : TYPE_I32
            | TYPE_U8
            | TYPE_U16
            | TYPE_U32
            | TYPE_U64
            | TYPE_F64
            | TYPE_CHAR
            | TYPE_STRING
            | TYPE_STR
            | TYPE_BOOL
            | TYPE_TUPLE'''
    p[0] = ("type", p[1])

# Arreglo/slice anidado: [T]
def p_type_array_rec(p):
    'type : LBRACKET type RBRACKET'
    p[0] = ("type_array", p[2])

# Arreglo con longitud anotada: [T, N]
def p_type_array_len(p):
    'type : LBRACKET type COMMA INTEGER RBRACKET'
    p[0] = ("type_array_len", p[2], p[4])

# Referencia: &T
def p_type_ref_rec(p):
    'type : BIT_AND type'
    p[0] = ("type_ref", p[2])

# Referencia mutable: &mut T
def p_type_ref_mut_rec(p):
    'type : BIT_AND MUT type'
    p[0] = ("type_ref_mut", p[3])

# ---------------- Declaraciones let ----------------
def p_statement_let(p):
    'statement : let_decl'
    p[0] = p[1]

def p_let_decl(p):
    'let_decl : LET maybe_mut IDENTIFIER maybe_type maybe_init SEMICOLON'
    ident = p[3]
    is_mut = p[2] is not None
    tipe   = p[4]
    init   = p[5]

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
    '''maybe_type : COLON type
                  | empty'''
    p[0] = p[2] if len(p) == 3 else None

def p_maybe_init(p):
    '''maybe_init : ASIGNED_TO expression
                  | empty'''
    p[0] = ("init", p[2]) if len(p) == 3 else None

# ---------------- Arrays / vectores / slices ----------------
def p_element_list(p):
    '''element_list : element_list COMMA expression
                       | expression'''
    p[0] = p[1] + [p[3]] if len(p) == 4 else [p[1]]

def p_array_literal(p):
    'expression : LBRACKET element_list RBRACKET'
    p[0] = ("array", p[2])

def p_array_repeat(p):
    'expression : LBRACKET expression SEMICOLON INTEGER RBRACKET'
    p[0] = ("array_repeat", p[2], p[4])

def p_index(p):
    'expression : IDENTIFIER LBRACKET expression RBRACKET'
    p[0] = ("index", ("id", p[1]), p[3])

def p_slice_open(p):
    'expression : IDENTIFIER LBRACKET INTEGER RANGE INTEGER RBRACKET'
    p[0] = ("slice", ("id", p[1]), p[3], p[5], False)

def p_slice_inclusive(p):
    'expression : IDENTIFIER LBRACKET INTEGER RANGE_INCLUSIVE INTEGER RBRACKET'
    p[0] = ("slice", ("id", p[1]), p[3], p[5], True)

def p_vec_macro(p):
    'expression : IDENTIFIER NOT LBRACKET element_list RBRACKET'
    p[0] = ("vec_macro", p[1], p[4])

# ---------------- Declaraciones const ----------------
def p_statement_const(p):
    'statement : const_decl'
    p[0] = p[1]

def p_const_decl(p):
    '''const_decl : CONST IDENTIFIER COLON type ASIGNED_TO expression SEMICOLON'''
    p[0] = ("const_decl", p[2], p[4], p[6])

# ---------------- Tuplas ----------------
def p_type_tuple(p):
    '''type : LPAREN tuple_type_list RPAREN'''
    p[0] = ("type_tuple", p[2])

def p_tuple_type_list(p):
    '''tuple_type_list : type
                         | type COMMA tuple_type_list'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [p[1]] + p[3]

def p_exp_tuple_literal(p):
    '''expression : LPAREN tuple_value_list RPAREN'''
    p[0] = ("tuple_literal", p[2])

def p_tuple_value_list(p):
    '''tuple_value_list : expression
                           | expression COMMA tuple_value_list'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [p[1]] + p[3]

def p_exp_tuple_access(p):
    '''expression : expression DOT INTEGER'''
    p[0] = ("tuple_access", p[1], p[3])

# ---------------- Bucle for ----------------
def p_for_loop(p):
    'statement : FOR IDENTIFIER IN expression LBRACE program_opt RBRACE'
    p[0] = ("for", p[2], p[4], p[6])

# ---------------- Parámetros de funciones ----------------
def p_param_list_opt(p):
    '''param_list_opt : param_list
                      | empty'''
    p[0] = p[1] if p[1] is not None else []

def p_param_list(p):
    '''param_list : param_list COMMA param
                  | param'''
    p[0] = p[1] + [p[3]] if len(p) == 4 else [p[1]]

def p_param(p):
    '''param : IDENTIFIER COLON type'''
    p[0] = ("param", p[1], p[3])

# ---------------- Funciones y return ----------------
def p_function_body_with_return(p):
    '''function_body : program expression
                     | expression'''
    # Con statements previos + expresión final (retorno implícito)
    if len(p) == 3:
        p[0] = ("body", p[1], p[2])  # statements + expr final
    # Solo expresión final (retorno implícito)
    else:
        p[0] = ("body", [], p[1])    # expr final directamente

def p_function_body_statements(p):
    'function_body : program_opt'
    # Solo statements (sin retorno implícito)
    p[0] = ("body", p[1], None)
    
def p_maybe_pub(p):
    '''maybe_pub : IDENTIFIER
                 | empty'''
    p[0] = p[1] if p[1] is not None else None

def p_function_name_ident(p):
    'function_name : IDENTIFIER'
    p[0] = p[1]

def p_function_name_main(p):
    'function_name : MAIN'
    p[0] = p[1]

def p_function_with_return(p):
    'statement : maybe_pub FN function_name LPAREN param_list_opt RPAREN ARROW type LBRACE function_body RBRACE'
    p[0] = ("fn_ret", p[3], p[5], p[8], p[10])

def p_function_without_return(p):
    'statement : maybe_pub FN function_name LPAREN param_list_opt RPAREN LBRACE program_opt RBRACE'
    p[0] = ("fn", p[3], p[5], p[7])

def p_return(p):
    'statement : RETURN expression SEMICOLON'
    p[0] = ("return", p[2])

def p_function_call(p):
    'expression : IDENTIFIER LPAREN arguments_opt RPAREN'
    p[0] = ("fn_call", p[1], p[3])

# ---------------- Errores ----------------
def p_error(tok):
    if tok:
        msg = f"[ERROR] Invalid syntax at '{tok.value}' (line {tok.lineno})"
    else:
        msg = "[ERROR] Unexpected end of file"
    print(msg)
    ERRORS.append(msg)

# Construyo el parser
parser = yacc.yacc(start='program')

# --------- Función para usar desde la interfaz gráfica ---------
def analizar_sintactico(codigo: str) -> str:
    """
    Ejecuta el analizador sintáctico sobre el código recibido
    y devuelve un texto con el resultado o los errores encontrados.
    Esta función la llama main.py.
    """
    ERRORS.clear()
    lexer.lineno = 1

    try:
        parser.parse(codigo, lexer=lexer)
    except Exception as e:
        ERRORS.append(f"[ERROR] Excepción del parser: {e}")

    if ERRORS:
        salida = ["Se encontraron errores sintácticos:"]
        salida.extend(ERRORS)
        return "\n".join(salida)
    else:
        return "Análisis sintáctico completado. No se encontraron errores."


# ---------------- Runner + logs ----------------
files = {
    "Nicolas Sierra": ["./algoritmos_prueba/avance2NicolasSierra.rs"],
    "Carlos Flores": ["./algoritmos_prueba/avance2CarlosFlores.rs"],
    "Carlos Tingo":["./algoritmos_prueba/avance2CarlosTingo.rs"]
}

def analyze():
    now = datetime.datetime.now()
    date = now.strftime("%d-%m-%Y")
    time = now.strftime("%Hh%M")

    for name, file_list in files.items():
        folder = f"./logs/{name.replace(' ', '_')}"
        os.makedirs(folder, exist_ok=True)

        log_name = f"{folder}/sintactico-{name.replace(' ', '')}-{date}-{time}.txt"
        with open(log_name, "w", encoding="utf-8") as log:
            log.write(f"===== Syntactic Analysis ({date} - {time}) =====\n\n")

            for file in file_list:
                if not os.path.exists(file):
                    alert = f"⚠️ ALERT: The file '{file}' does not exist.\n"
                    print(alert.strip())
                    log.write(alert + "\n")
                    continue

                with open(file, "r", encoding="utf-8") as f:
                    data = f.read()

                print(f"\n📂 Analyzing file: {file}")
                log.write(f"=== File: {file} ===\n")

                ERRORS.clear()
                lexer.lineno = 1

                try:
                    result = parser.parse(data, lexer=lexer)
                    if ERRORS:
                        log.write("❌ Syntax errors found:\n")
                        for e in ERRORS:
                            log.write(f"   - {e}\n")
                        print(f"❌ Syntax errors in {file}")
                    else:
                        log.write("✅ No syntax errors.\n")
                        print(f"✅ {file} analyzed successfully.")
                        # Opcional: imprimir el AST
                        # log.write(f"\nAST: {result}\n")
                except Exception as e:
                    error_msg = f"🔥 Critical error analyzing {file}: {e}\n"
                    print(error_msg.strip())
                    log.write(error_msg)

                log.write("\n")

        print(f"📄 Log generated at: {log_name}\n")


if __name__ == "__main__":
    analyze()
