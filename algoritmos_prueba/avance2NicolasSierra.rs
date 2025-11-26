async fn procesar_edades() {
    let mut edades = HashMap::new();

    edades.insert(1, 30);
    edades.insert(2, 25);

    let mut id = 1;

    while id < 3 {
        let valor = edades.get(&id);
        println!(id);
        id = id + 1;
    }
}

fn main() {
    let x = 1;
}
