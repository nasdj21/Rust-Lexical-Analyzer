# Analizador Semántico Simple para Rust
# Sin clases, solo funciones para validar reglas semánticas

import datetime
import os
from syntaxAnalyzer import parser, lexer, ERRORS as PARSER_ERRORS

# Variables globales para el análisis
errors = []
symbol_table = {}  # {nombre: {'mutable': bool, 'initialized': bool, 'type': 'num', 'bool', 'String (por incluir)','unknown'}}
function_stack = [] # {'name' : str, 'ret_type' _ str[None, 'found_return': bool]}
type_map = {
    "i32":"num","u64":"num","f64":"num",
    "u8":"num","u16":"num","u32":"num",
    "bool":"bool","String":"string","str":"string",
    "char":"char","tuple":"tuple","HashMap":"hashmap"
}
unsigned_tokens = {"u8","u16","u32","u64","u128","usize"}


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

# Tipos y literales auxiliares
def is_unsigned_type(t):
    """Verifica si un tipo AST corresponde a un entero sin signo."""
    if isinstance(t, str):
        return t in unsigned_tokens
    if isinstance(t, tuple) and len(t) > 1:
        tag = t[0]
        if tag in ("type_ref", "type_ref_mut"):
            return is_unsigned_type(t[1])
        if tag in ("type_array", "type_array_len"):
            return is_unsigned_type(t[1])
        if tag == "type_tuple":
            return False
        if isinstance(t[1], str):
            return t[1] in unsigned_tokens
    return False

def is_negative_literal(expr):
    """Detecta si la expresión es un literal numérico negativo simple."""
    if not isinstance(expr, tuple):
        return False
    if expr[0] == "uminus" and isinstance(expr[1], tuple) and expr[1][0] == "num":
        return True
    if expr[0] == "num" and isinstance(expr[1], (int, float)) and expr[1] < 0:
        return True
    return False

def check_type_compatibility(declared_type, expr_type, var_name):
    """
    Verifica que el tipo de la expresión sea compatible con el tipo declarado.
    declared_type: tipo declarado (ej: 'num', 'bool', 'string')
    expr_type: tipo inferido de la expresión (ej: 'num', 'bool', 'string')
    var_name: nombre de la variable (para el mensaje de error)
    """
    if declared_type == "unknown" or expr_type == "unknown":
        return True  # No podemos verificar si alguno es desconocido
    
    if declared_type != expr_type:
        add_error(
            f"Type mismatch in variable '{var_name}': "
            f"expected '{declared_type}', but got '{expr_type}'"
        )
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
        if tag in ("type_ref", "type_ref_mut"):
            return type_name_from_ast(t[1])
        if tag == "type_array":
            inner = type_name_from_ast(t[1])
            return f"array<{inner}>"
        if tag == "type_array_len":
            inner = type_name_from_ast(t[1])
            return f"array<{inner}>"
        if tag == "type_tuple":
            return "tuple"
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
    elif expr_type == "bool":
        return "bool"
    elif expr_type == "uminus":
        inner_t = analyze_expression(expr[1])
        # Si es número, sigue siendo num (marcará negativo en el literal mismo)
        return inner_t
    elif expr_type == "not":
        inner_t = analyze_expression(expr[1])
        if inner_t not in ("bool", "unknown"):
            add_error(f"Operand of '!' should be boolean, got {inner_t} (SEM-TYPE-MISMATCH)")
        return "bool"
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
        return "unknown"

    elif expr_type == "hashmap_new":
        return "hashmap"
    
    # Array: analizar elementos
    elif expr_type == "array":
        elements = expr[1]
        elem_types = []
        for elem in elements:
            elem_types.append(analyze_expression(elem))
        return "array"
    
    elif expr_type == "array_repeat":
        analyze_expression(expr[1])
        analyze_expression(("num", expr[2]))
        return "array"
    
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
        return "tuple"

    elif expr_type == "vec_macro":
        elements = expr[2]
        for elem in elements:
            analyze_expression(elem)
        return "vector"

    elif expr_type == "range":
        start_t = analyze_expression(expr[1])
        end_t = analyze_expression(expr[2])
        if start_t not in ("num", "unknown"):
            add_error("Range start should be numeric")
        if end_t not in ("num", "unknown"):
            add_error("Range end should be numeric")
        return "range"

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
    
    if stmt_type == "let_typed_assign":
        var_name = stmt[1]
        tipo_ast = stmt[2]
        expr = stmt[3]

        tipo = type_name_from_ast(tipo_ast)
        expr_t = analyze_expression(expr)

        # NUEVA REGLA: Verificar compatibilidad de tipos
        check_type_compatibility(tipo, expr_t, var_name)

        if is_unsigned_type(tipo_ast) and is_negative_literal(expr):
            add_error(f"Cannot assign negative literal to unsigned type in variable '{var_name}'")

        symbol_table[var_name] = {
            'mutable': False,
            'initialized': True,
            'type': tipo if tipo != "unknown" else expr_t
        }
    
    # ===== let mut x: T = expr; (CON VERIFICACIÓN DE TIPOS) =====
    elif stmt_type == "let_mut_typed_assign":
        var_name = stmt[1]
        tipo_ast = stmt[2]
        expr = stmt[3]

        tipo = type_name_from_ast(tipo_ast)
        expr_t = analyze_expression(expr)

        # NUEVA REGLA: Verificar compatibilidad de tipos
        check_type_compatibility(tipo, expr_t, var_name)

        if is_unsigned_type(tipo_ast) and is_negative_literal(expr):
            add_error(f"Cannot assign negative literal to unsigned type in variable '{var_name}'")

        symbol_table[var_name] = {
            'mutable': True,
            'initialized': True,
            'type': tipo if tipo != "unknown" else expr_t
        }
    
    # ===== CONSTANTES =====
    elif stmt_type == "const_decl":
        const_name = stmt[1]
        tipo_ast = stmt[2]
        const_value = stmt[3]

        tipo = type_name_from_ast(tipo_ast)
        expr_t = analyze_expression(const_value)

        # NUEVA REGLA: Verificar compatibilidad de tipos
        check_type_compatibility(tipo, expr_t, const_name)

        if is_unsigned_type(tipo_ast) and is_negative_literal(const_value):
            add_error(f"Cannot assign negative literal to unsigned type in const '{const_name}'")

        symbol_table[const_name] = {
            'mutable': False,
            'initialized': True,
            'type': tipo or expr_t
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
    
    # ===== ESTRUCTURAS DE CONTROL =====
    
    elif stmt_type == "if":
        # if condition { body }
        condition = stmt[1]
        body = stmt[2]
        analyze_expression(condition)
        if isinstance(body, list):
            for s in body:
                analyze_statement(s)

    elif stmt_type == "if_else":
        # if condition { body } else { body2 }
        condition = stmt[1]
        then_body = stmt[2]
        else_body = stmt[3]
        analyze_expression(condition)
        if isinstance(then_body, list):
            for s in then_body:
                analyze_statement(s)
        if isinstance(else_body, list):
            for s in else_body:
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
    
    log_folder = f"./logs/{name.replace(' ', '_')}"
    os.makedirs(log_folder, exist_ok=True)
    
    log_name = f"{log_folder}/semantico-{name.replace(' ', '')}-{date}-{time}.txt"
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

# ========= FUNCIÓN PARA USAR EN LA INTERFAZ GRÁFICA =========
def analizar_semantico(codigo: str, autor="EditorGUI"):
    reset_analyzer()
    PARSER_ERRORS.clear()
    lexer.lineno = 1

    try:
        ast = parser.parse(codigo, lexer=lexer)
    except Exception as e:
        return f"❌ Critical error in syntax analysis: {e}"

    if PARSER_ERRORS:
        texto = "❌ Syntax errors found:\n"
        texto += "\n".join(f"  {e}" for e in PARSER_ERRORS)
        return texto

    analyze_ast(ast)

    log_path = generate_report(autor)

    with open(log_path, "r", encoding="utf-8") as f:
        report = f.read()

    report += f"\n\n📄 Log generated at: {log_path}"
    return report

# ============== EJECUCIÓN ==============

if __name__ == "__main__":
    # Archivos de prueba
    files = {
        "Carlos Flores": "algoritmos_prueba/avance3CarlosFlores.rs",
        "Nicolas Sierra": "algoritmos_prueba/avance3NicolasSierra.rs", #Como solo estaba probando yo, deje mi nombre nomas. PILAS
        "Carlos Tingo": "algoritmos_prueba/algoritmoVectoresArreglos.rs"
    }

    for name, filename in files.items():
        print(f"\n📂 Analyzing file: {filename}")
        if os.path.exists(filename):
            success = analyze_file(filename, name)
            print(f"{'✅ PASS' if success else '❌ FAIL'}: {filename}\n")
