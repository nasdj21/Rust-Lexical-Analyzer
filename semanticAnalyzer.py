# Analizador Semántico Simple para Rust
# Sin clases, solo funciones para validar reglas semánticas

import datetime
import os
from syntaxAnalyzer import parser, lexer, ERRORS as PARSER_ERRORS

# Variables globales para el análisis
errors = []
symbol_table = {}  # {nombre: {'mutable': bool, 'initialized': bool, 'type': 'num', 'bool', 'String (por incluir)','unknown'}}
function_stack = [] # {'name' : str, 'ret_type' _ str[None, 'found_return': bool]}
type_map = {"i32":"num","u64":"num","f64":"num","bool":"bool","String":"string","char":"char","tuple":"tuple"}
type_map["str"] = "string"


def add_error(msg):
    """Agrega un error semántico"""
    error_msg = f"[SEMANTIC ERROR] {msg}"
    errors.append(error_msg) 

def reset_analyzer():
    """Reinicia el estado del analizador"""
    global errors, symbol_table
    errors = []
    symbol_table = {}


# ============== REGLA 1: Variables deben estar inicializadas antes de usarse ==============

def check_variable_initialized(var_name):
    """Verifica si una variable está inicializada antes de usarse"""
    if var_name not in symbol_table:
        add_error(f"Variable '{var_name}' is not declared")
        return False
    if not symbol_table[var_name]['initialized']:
        add_error(f"Variable '{var_name}' used before initialization")
        return False   
    return True


# ============== REGLA 2: No se puede asignar a variables inmutables ==============

def check_variable_mutable(var_name):
    """Verifica si se puede asignar a una variable (debe ser mutable)"""
    if var_name not in symbol_table:
        add_error(f"Variable '{var_name}' is not declared")
        return False
    if not symbol_table[var_name]['mutable']:
        add_error(f"Cannot assign to immutable variable '{var_name}'")
        return False
    return True

# ============== HELPERS ==============

def type_name_from_ast(t):
    """
    Convierte el nodo de tipo del AST en un nombre sencillo: 'num', 'bool' o 'unknown'.
    Ajusta esto a cómo tu parser represente los tipos.
    """
    if isinstance(t, str): 
        return type_map.get(t, t)
    if isinstance(t, tuple) and len(t) > 1:
        tag = t[0]
        if tag in ("type_ref", "type_ref_mut", "type_array"):
            return type_name_from_ast(t[1])
        if isinstance(t[1], str):
            return type_map.get(t[1], "unknown")
    return "unknown"

def combine_arimethic_types(op, left_t, right_t):
    """
    Combina operaciones ariméticas en los casos de booleanos
    """
    if left_t == "bool" or right_t == "bool":
        add_error(f"Invalid operands for arithmetic operator '{op}' (SEM-TYPE-MISMATCH: bool is not allowed here)")
        return "unknown"
    if left_t == "num" and right_t == "num":
        return "num"
    return "unknown"

def combine_logic_types(left_t, right_t, op):
    """
    Reglas para && y ||. Ambos deberían ser bool si se conocen.
    """
    if left_t not in ("bool", "unknown"):
        add_error(
            f"Left operand of '{op}' should be boolean, got {left_t} (SEM-TYPE-MISMATCH)"
        )
    if right_t not in ("bool", "unknown"):
        add_error(
            f"Right operand of '{op}' should be boolean, got {right_t} (SEM-TYPE-MISMATCH)"
        )
    return "bool"

def combine_rel_types(left_t, right_t, op):
    """
    Reglas para ==, !=, <, >, <=, >=.
    Si ambos tipos son conocidos y distintos, marcamos error.
    """
    if left_t != "unknown" and right_t != "unknown" and left_t != right_t:
        add_error(
            f"Incompatible types for comparison '{op}': {left_t} and {right_t} "
            f"(SEM-TYPE-MISMATCH)"
        )
    # Comparaciones devuelven bool
    return "bool"

# ============== ANÁLISIS DE EXPRESIONES ==============

def analyze_expression(expr):
    """Analiza una expresión y verifica uso de variables"""
    if not isinstance(expr, tuple):
        return
    
    expr_type = expr[0]
    
    # ===== VARIABLE (id) =====
    if expr_type == "id":
        var_name = expr[1]
        if not check_variable_initialized(var_name): #Si es que la variable no ha sido inizializada
            return "unknown"
        return symbol_table.get(var_name, {}).get("type", "unknown")
    
    # ===== OPERACIÓN BINARIA (op): Analizar ambos lados =====
    # Estructura esperada: ("op", operador, left, right). Left y right deberian ser "lit" y "BOOLEAN" para esto
    elif expr_type == "op":
        op, left, right = expr[1], expr[2], expr[3]
        left_t = analyze_expression(left) or "unknown"
        right_t = analyze_expression(right) or "unknown"
        if op in ("+", "-", "*", "/", "%"):
            return combine_arimethic_types(op, left_t, right_t)
        return "unknown"

    elif expr_type == "lit":
        value = expr[1]
        if isinstance(value, bool) or value in ("true", "false"):
            return "bool"
        if isinstance(value, (int, float)):
            return "num"
        if isinstance(value,str):
            if len(value)==1: 
                return "char"
            return "string"
        return "unknown"
    #Revisar bien estos 2 elifs de abajo
    elif expr_type == "rel":
        analyze_expression(expr[2]); analyze_expression(expr[3]); return "bool"
    
    elif expr_type == "logic":
        analyze_expression(expr[2]); analyze_expression(expr[3]); return "bool"
        

    # ===== LLAMADA A FUNCIÓN: Analizar argumentos =====
    elif expr_type == "fn_call":
        args = expr[2]
        for arg in args:
            analyze_expression(arg)
    
    # Array: analizar elementos
    elif expr_type == "array":
        elements = expr[1]
        for elem in elements:
            analyze_expression(elem)
    
    # Indexación: analizar array e índice
    elif expr_type == "index":
        array_expr = expr[1]
        index_expr = expr[2]
        analyze_expression(array_expr)
        analyze_expression(index_expr)
    
    # Referencia: analizar la expresión referenciada
    elif expr_type in ("ref", "ref_mut"):
        analyze_expression(expr[1])
    
    # Cast: analizar expresión a castear
    elif expr_type == "cast":
        analyze_expression(expr[1])
    
    # Closure/Lambda: analizar cuerpo
    elif expr_type == "closure":
        params = expr[1]
        body = expr[3]
        
        # Guardar tabla de símbolos actual
        old_table = symbol_table.copy()
        
        # Registrar parámetros como variables inicializadas
        for param in params:
            if param[0] == "param":
                param_name = param[1]
                symbol_table[param_name] = {
                    'mutable': False,
                    'initialized': True
                }
        
        # Analizar cuerpo del closure
        if body[0] == "expr_body":
            analyze_expression(body[1])
        elif body[0] == "block_body":
            statements = body[1]
            if isinstance(statements, list):
                for stmt in statements:
                    analyze_statement(stmt)
            # Si hay expresión final
            if len(body) > 2 and body[2]:
                analyze_expression(body[2])
        
        # Restaurar tabla de símbolos
        symbol_table.clear()
        symbol_table.update(old_table)
    
    # Tupla: analizar elementos
    elif expr_type == "tuple_literal":
        elements = expr[1]
        for elem in elements:
            analyze_expression(elem)

    # ===== LITERALES NUMÉRICOS =====
    elif expr_type == "num":
        return "num"
    


# ============== ANÁLISIS DE STATEMENTS ==============

def analyze_statement(stmt):
    """Analiza un statement y aplica las reglas semánticas"""
    if not isinstance(stmt, tuple):
        return
    
    stmt_type = stmt[0]
    
    # ===== DECLARACIONES LET =====
    
    if stmt_type == "let_decl":
        # let x;
        var_name = stmt[1]
        symbol_table[var_name] = {
            'mutable': False,
            'initialized': False,
            'type': "unknown"
        }
    
    elif stmt_type == "let_assign":
        # let x = expr;
        var_name = stmt[1]
        expr = stmt[2]
        expr_t = analyze_expression(expr)
        symbol_table[var_name] = {
            'mutable': False,
            'initialized': True,
            'type': expr_t
        }
    
    elif stmt_type == "let_mut_assign":
        # let mut x = expr;
        var_name = stmt[1]
        expr = stmt[2]
        expr_t = analyze_expression(expr)
        symbol_table[var_name] = {
            'mutable': True,
            'initialized': True,
            'type': expr_t
        }
    
    elif stmt_type == "let_typed_decl":
        # let x: T;
        var_name = stmt[1]
        tipo_ast = stmt[2]      # normalmente el parser pone aquí el tipo
        tipo = type_name_from_ast(tipo_ast)
        symbol_table[var_name] = {
            'mutable': False,
            'initialized': False,
            'type': tipo
        }
    
    elif stmt_type == "let_typed_assign":
        # let x: T = expr;
        var_name = stmt[1]
        tipo_ast = stmt[2]
        expr = stmt[3]

        tipo = type_name_from_ast(tipo_ast)
        expr_t = analyze_expression(expr) 

        symbol_table[var_name] = {
            'mutable': False,
            'initialized': True,
            'type': tipo or expr_t
        }
    
    elif stmt_type == "let_mut_typed_assign":
        # let mut x: T = expr;
        var_name = stmt[1]
        tipo_ast = stmt[2]
        expr = stmt[3]

        tipo = type_name_from_ast(tipo_ast)
        expr_t = analyze_expression(expr)

        symbol_table[var_name] = {
            'mutable': True,
            'initialized': True,
            'type': tipo or expr_t
        }
    
    elif stmt_type == "let_mut_typed_decl":
        # let mut x: T;
        var_name = stmt[1]
        tipo_ast = stmt[2]
        tipo = type_name_from_ast(tipo_ast)

        symbol_table[var_name] = {
            'mutable': True,
            'initialized': False,
            'type': tipo
        }

    
    # ===== ASIGNACIÓN =====
    
    elif stmt_type == "assignment":
        # x = expr;
        var_name = stmt[1]
        expr = stmt[2]
        
        # REGLA 2: Verificar que sea mutable
        if check_variable_mutable(var_name):
            # Marcar como inicializada
            symbol_table[var_name]['initialized'] = True
        
        analyze_expression(expr)
    
    # ===== CONSTANTES =====
    
    elif stmt_type == "const_decl":
        # const X: T = expr;
        const_name = stmt[1]
        tipo_ast = stmt[2]
        const_value = stmt[3]

        tipo = type_name_from_ast(tipo_ast)
        expr_t = analyze_expression(const_value)
        
        # Registrar constante (siempre inicializada e inmutable)
        symbol_table[const_name] = {
            'mutable': False,
            'initialized': True,
            'type': tipo or expr_t
        }
    
    # ===== ESTRUCTURAS DE CONTROL =====
    
    elif stmt_type == "if":
        # if condition { body }
        condition = stmt[1]
        body = stmt[2]
        analyze_expression(condition)
        if isinstance(body, list):
            for s in body:
                analyze_statement(s)
    
    elif stmt_type == "while":
        # while condition { body }
        condition = stmt[1]
        body = stmt[2]
        analyze_expression(condition)
        if isinstance(body, list):
            for s in body:
                analyze_statement(s)
    
    elif stmt_type == "for":
        # for var in iterable { body }
        var_name = stmt[1]
        iterable = stmt[2]
        body = stmt[3]
        
        # Variable del for está inicializada
        symbol_table[var_name] = {
            'mutable': False,
            'initialized': True
        }
        
        analyze_expression(iterable)
        if isinstance(body, list):
            for s in body:
                analyze_statement(s)
    
    # ===== FUNCIONES =====
    
    elif stmt_type in ("fn", "fn_ret", "async_fn", "async_fn_ret"):
        # fn nombre() { body }
        if stmt_type in ("fn_ret", "async_fn_ret"):
            body = stmt[3]
        else:
            body = stmt[2]
        
        # Analizar cuerpo (simplificado, sin scope separado)
        if isinstance(body, list):
            for s in body:
                analyze_statement(s)
    
    elif stmt_type == "return":
        # return expr;
        expr = stmt[1]
        analyze_expression(expr)
    
    # ===== OTROS =====
    
    elif stmt_type == "expr_stmt":
        analyze_expression(stmt[1])
    
    elif stmt_type == "println_expr":
        if len(stmt) > 1:
            analyze_expression(stmt[1])

# ============== ANÁLISIS DE RETORNO DE FUNCIONES ==============
def expression_type(expression):
    """
    Devuelve un tipo aproximado: 'num', 'bool', 'string'.
    """
    if not isinstance(expression, tuple):
        return 'unknown'
    tag = expression[0]

    if tag in ('number', 'numero', 'init_lit'):
        return 'num'

# ============== ANÁLISIS DEL AST COMPLETO ==============

def analyze_ast(ast):
    """Analiza el AST completo"""
    if ast is None:
        return
    
    if isinstance(ast, list):
        for statement in ast:
            analyze_statement(statement)
    else:
        analyze_statement(ast)


# ============== GENERACIÓN DE REPORTE ==============

def generate_report(name):
    """Genera un reporte del análisis semántico"""
    report = []
    report.append("=" * 60)
    report.append("SEMANTIC ANALYSIS REPORT")
    report.append("=" * 60)
    report.append("")
    
    # Errores
    if errors:
        report.append(f"❌ ERRORS FOUND: {len(errors)}")
        for error in errors:
            report.append(f"  {error}")
        report.append("")
    else:
        report.append("✅ NO SEMANTIC ERRORS")
        report.append("")
    
    # Tabla de símbolos
    report.append("-" * 60)
    report.append("SYMBOL TABLE")
    report.append("-" * 60)
    
    if symbol_table:
        for var_name, var_info in symbol_table.items():
            mutable = "mutable" if var_info['mutable'] else "immutable"
            initialized = "initialized" if var_info['initialized'] else "NOT initialized"
            var_type = var_info.get('type', 'unknown')
            report.append(f"  {var_name}: {mutable}, {initialized}, type={var_type}")
    else:
        report.append("  (empty)")
    
    report.append("")
    report = "\n".join(report)

    # Guardar reporte
    now = datetime.datetime.now()
    date = now.strftime("%d-%m-%Y")
    time = now.strftime("%Hh%M")
    
    log_folder = f"./logs/{name.replace(" ", "_")}"
    os.makedirs(log_folder, exist_ok=True)
    
    log_name = f"{log_folder}/semantico-{name.replace(" ", "")}-{date}-{time}.txt"
    with open(log_name, "w", encoding="utf-8") as log:
        log.write(report)
    return log_name

# ============== FUNCIÓN PRINCIPAL ==============
def analyze_file(filename, autor):    
    if not os.path.exists(filename):
        print(f"❌ ERROR: File '{filename}' does not exist")
        return False
    
    with open(filename, "r", encoding="utf-8") as f:
        code = f.read()
    
    # Reiniciar todo
    reset_analyzer()
    PARSER_ERRORS.clear()
    lexer.lineno = 1
    
    # Fase 1: Análisis sintáctico
    print("🔍 Phase 1: Syntactic Analysis...")
    try:
        ast = parser.parse(code, lexer=lexer)
        
        if PARSER_ERRORS:
            print(f"❌ Syntax errors found: {len(PARSER_ERRORS)}")
            for error in PARSER_ERRORS:
                print(f"  {error}")
            return False
        else:
            print("✅ Syntax analysis passed")
    except Exception as e:
        print(f"❌ Critical error in syntax analysis: {e}")
        return False
    
    # Fase 2: Análisis semántico
    print("🔍 Phase 2: Semantic Analysis...")
    analyze_ast(ast)
    
    # Generar reporte
    log_name = generate_report(autor)
    
    print(f"📄 Log generated at: {log_name}")
    
    return len(errors) == 0


# ============== EJECUCIÓN ==============

if __name__ == "__main__":
    # Archivos de prueba
    files = {
        #"Carlos Flores": "avance3CarlosFlores.rs",
        "Nicolas Sierra": "avance3NicolasSierra.rs", #Como solo estaba probando yo, deje mi nombre nomas. PILAS
        #"Carlos Tingo": "algoritmoVectoresArreglos.rs"
    }

    for name, filename in files.items():
        print(f"\n📂 Analyzing file: {filename}")
        if os.path.exists(filename):
            success = analyze_file(filename, name)
            print(f"{'✅ PASS' if success else '❌ FAIL'}: {filename}\n")
