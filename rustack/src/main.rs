enum StackObject {
    Nil,
    False,
    True,
    Integer(i64),
    Float(f64),
    String(String),
    List(Vec<StackObject>),
}

struct InterpreterState {
    stack: Vec<StackObject>,
    ns: Vec<BTreeMap<String, StackObject>>,
}

fn eval(state: InterpreterState, obj: StackObject) -> StackObject {

}

fn main() {
    let mut stack: Vec<StackObject> = Vec::new();
    let mut ns: Vec<BTreeMap<String, StackObject>> = Vec::new();
    ns.push(BTreeMap::new());

    let mut rl_editor = rustyline::Editor::new().unwrap();
    loop {
        match rl_editor.readline("> ") {
            Ok(line) => 
        }
    }
}
