fn main() {
    let mut a = true;
    let mut b = false;
    let mut contador = 0;

    
    if a && !b {
        println!("Caso 1: a && !b es verdadero");
    }

   
    if a || b {
        println!("Caso 2: a || b es verdadero");
    }

  
    if (a && b) || !b {
        println!("Caso 3: (a && b) || !b es verdadero");
    }


    while contador < 3 && a {
        println!("Caso 4: while con contador = {}", contador);
        contador += 1;
    }

   
    if !a && !b || (a && !(!b)) {
        println!("Caso 5: expresión lógica más compleja");
    } else {
        println!("Caso 5: rama else ejecutada");
    }

    return;
}