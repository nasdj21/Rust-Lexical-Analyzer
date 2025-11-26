let edad: i32 = 25;
let mut nombre: String = "Carlos";
const PI: f64 = 3.14159;
let activo: bool = true;
let mut tupla = (10, 3.14, true, 'A');
let letra: char = 'A';

for item in my_array {
    println!("{}", item);
}

for x in vec![1, 2, 3] {
    println!("{}", x);
}

for element in [1, 2, 3, 4] {
    println!("{}", element);
}

let suma = |a, b| a + b;
println!("{}", suma(2, 3)); // 5

let multiplicar = |x: i32, y: i32| -> i32 {
    x * y
};

let cuadrado = |x| x * x;

let proceso = |x: i32| {
    let y = x + 2;
    y * 3
};

let factor = 10;
let aplicar = |x| x * factor;

println!("{}", aplicar(5));

