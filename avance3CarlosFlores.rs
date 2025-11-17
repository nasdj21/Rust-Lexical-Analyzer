// Archivo con código 100% correcto (sin errores semánticos)

// ============================================
// Variables inmutables correctas
// ============================================
let x = 10;
let y = 20;
let suma = x + y;

// ============================================
// Variables mutables correctas
// ============================================
let mut contador = 0;
contador = 1;
contador = 2;
contador = contador + 1;

let mut acumulador = 0;
acumulador = acumulador + 10;
acumulador = acumulador + 20;

// ============================================
// Constantes
// ============================================
const PI: f64 = 3.14159;
const MAX: i32 = 100;

// ============================================
// Variables con tipo explícito
// ============================================
let edad: i32 = 25;
let precio: f64 = 99.99;
let activo: bool = true;
let inicial: char = "A";

// ============================================
// Operaciones aritméticas
// ============================================
let a = 5;
let b = 3;
let suma_ab = a + b;
let resta = a - b;
let mult = a * b;
let div = a / b;
let mod = a % b;

// ============================================
// Expresiones lógicas
// ============================================
let verdadero = true;
let falso = false;
let resultado_and = verdadero && falso;
let resultado_or = verdadero || falso;
let negacion = !verdadero;

let mayor = a > b;
let igual = a == b;
let diferente = a != b;

// ============================================
// Arrays
// ============================================
let numeros = [1, 2, 3, 4, 5];
let letras = ["a", "b", "c"];
let ceros = [0; 10];

// ============================================
// Lambdas/Closures
// ============================================
let sumar = |x, y| x + y;
let resultado_lambda = sumar(10, 5);

let multiplicar = |a: i32, b: i32| -> i32 { a * b };
let resultado_mult = multiplicar(3, 4);

let sin_params = || 42;
let valor = sin_params();

let factor = 2;
let duplicar = |n| n * factor;
let duplicado = duplicar(21);

// ============================================
// Estructuras de control
// ============================================
let mut i = 0;
while i < 5 {
    i = i + 1;
}

for num in numeros {
    println!("Numero");
}

if a > b {
    println!("a es mayor");
}

// ============================================
// Funciones
// ============================================
fn saludar() {
    println!("Hola");
}

fn calcular() -> i32 {
    return 42;
}

// ============================================
// Llamadas a funciones
// ============================================
saludar();
let res = calcular();
let res_lambda = sumar(7, 8);

// ============================================
// Referencias
// ============================================
let valor = 100;
let referencia = &valor;

let mut mutable = 200;
let ref_mutable = &mut mutable;

// ============================================
// Cast
// ============================================
let entero = 10;
let flotante = entero as f64;

// ============================================
// Bloques complejos correctos
// ============================================
let mut total = 0;
let datos = [1, 2, 3, 4, 5];

for dato in datos {
    total = total + dato;
}

let promedio = total / 5;

// ============================================
// Lambda con bloque
// ============================================
let calcular_complejo = |x, y| {
    let temp = x + y;
    temp * 2
};

let resultado_complejo = calcular_complejo(5, 3);

// ============================================
// Variables bien inicializadas
// ============================================
let primero = 1;
let segundo = 2;
let tercero = 3;
let suma_tres = primero + segundo + tercero;

// ============================================
// Función con lógica completa
// ============================================
fn procesar() -> i32 {
    let mut suma = 0;
    let mut i = 1;
    
    while i <= 10 {
        suma = suma + i;
        i = i + 1;
    }
    
    return suma;
}

let resultado_fn = procesar();