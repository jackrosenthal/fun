use std::borrow::Cow::{self, Owned};
use std::process::ExitCode;
use crate::game::{WordleGame, NormalGame, is_valid_word};

mod game;

#[derive(rustyline::Completer, rustyline::Helper, rustyline::Hinter)]
struct WordleInputHelper;

impl rustyline::highlight::Highlighter for WordleInputHelper {
    fn highlight<'l>(&self, line: &'l str, _pos: usize) -> Cow<'l, str> {
        return Owned(line.to_uppercase());
    }

    fn highlight_char(&self, _line: &str, _pos: usize) -> bool {
        return true;
    }
}

impl rustyline::validate::Validator for WordleInputHelper {
    fn validate(
        &self,
        ctx: &mut rustyline::validate::ValidationContext,
    ) -> rustyline::Result<rustyline::validate::ValidationResult> {
        use rustyline::validate::ValidationResult::{Invalid, Valid};

        let input = ctx.input();
        let err = if input.len() < 5 {
            Some("Too short")
        } else if input.len() > 5 {
            Some("Too long")
        } else if !is_valid_word(&input.to_string()) {
            Some("Not a valid word")
        } else {
            None
        };
        return Ok(match err {
            Some(e) => Invalid(Some(format!("\n\x1b[1;31mE: {}\x1b[0m", e))),
            None => Valid(Some("\x1b[F".to_owned())),
        });
    }
}

fn main() -> ExitCode {
    let mut game = NormalGame::new();
    let helper = WordleInputHelper;
    let mut rl_editor = rustyline::Editor::new().unwrap();
    rl_editor.set_helper(Some(helper));

    loop {
        let result = rl_editor.readline("> ");
        match result {
            Ok(line) => {
                let response = game.guess(&line);

                response.print();
                if response.is_winning() {
                    println!("Congratulations, you have won!");
                    return ExitCode::SUCCESS;
                }
            }
            Err(rustyline::error::ReadlineError::Interrupted) => {
                println!("Ctrl-C");
                return ExitCode::SUCCESS;
            }
            Err(rustyline::error::ReadlineError::Eof) => {
                println!("Ctrl-D");
                return ExitCode::SUCCESS;
            }
            Err(err) => {
                println!("Error: {:?}", err);
                return ExitCode::FAILURE;
            }
        }
    }
}
