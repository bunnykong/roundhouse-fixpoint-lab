fn exclusion(eligible: bool, constructor_invalid: bool) -> Option<&'static str> {
    if !eligible { Some("ineligible writer") }
    else if constructor_invalid { Some("typed Proc receiver is not constant Proc") }
    else { None }
}
fn main() {
    let mut checked = 0;
    for (eligible, invalid, actual, expected) in [
        (false, false, false, true), (true, true, false, true), (true, false, true, true)
    ] {
        let excluded = exclusion(eligible, invalid);
        if excluded.is_none() { assert_eq!(actual, expected); checked += 1; }
    }
    assert_eq!(checked, 1);
    println!("pre-arm synthetic exclusion control passed: both permitted exclusions skip mismatched harvests");
}
