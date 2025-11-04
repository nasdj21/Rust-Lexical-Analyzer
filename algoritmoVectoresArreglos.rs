pub fn demo() -> i32 {
    let a = [1, 2, 3, 4];
    let tercero = a[2];

    let zeros = [0; 5];

    let s1 = &a[1..3];
    let s2 = &a[1..=3];

    let mut v = vec![10, 20, 30];
    let primero = v[0];
    let sv = &v[0..2];
    return tercero + primero + s1.len() as i32 + s2.len() as i32 + sv.len() as i32;
}
