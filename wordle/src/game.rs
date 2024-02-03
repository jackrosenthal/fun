use lazy_static::lazy_static;
use std::str::Lines;
use rand::seq::IteratorRandom;
use itertools::{enumerate, izip};

const WORDS_RAW: &str = include_str!("words.txt");

lazy_static! {
    static ref WORDS: Lines<'static> = WORDS_RAW.lines();
}

fn get_random_word() -> String {
    let mut rng = rand::thread_rng();
    return WORDS.clone().choose(&mut rng).unwrap().to_string();
}

pub fn is_valid_word(word: &String) -> bool {
    let word = word.to_uppercase();

    match WORDS.clone().find(|w| w.to_string() == word) {
        Some(_) => {
            return true;
        }
        None => {
            return false;
        }
    }
}

#[derive(Clone, Eq, PartialEq)]
pub enum LetterScore {
    Correct,
    IncorrectSpot,
    NotInWord,
}

pub struct GuessResponse {
    guess: String,
    letter_scores: Vec<LetterScore>,
}

impl GuessResponse {
    fn new(guess: &String, answer: &String) -> GuessResponse {
        let mut response = GuessResponse {
            guess: guess.to_uppercase(),
            letter_scores: Vec::new(),
        };
        let mut used = vec![false; answer.len()];

        for (i, (guess_letter, answer_letter)) in
            enumerate(izip!(response.guess.chars(), answer.chars()))
        {
            if guess_letter == answer_letter {
                response.letter_scores.push(LetterScore::Correct);
                used[i] = true;
                continue;
            }
            let mut found_incorrect_spot = false;
            for (j, (used_letter, answer_j)) in enumerate(izip!(used.clone(), answer.chars())) {
                if used_letter {
                    continue;
                }
                if answer_j != guess_letter {
                    continue;
                }
                if answer_j == response.guess.chars().nth(j).unwrap() {
                    continue;
                }
                response.letter_scores.push(LetterScore::IncorrectSpot);
                used[j] = true;
                found_incorrect_spot = true;
                break;
            }
            if !found_incorrect_spot {
                response.letter_scores.push(LetterScore::NotInWord);
            }
        }

        return response;
    }

    pub fn is_winning(&self) -> bool {
        return self
            .letter_scores
            .iter()
            .all(|score| *score == LetterScore::Correct);
    }

    pub fn print(&self) {
        println!(
            "  {}\x1b[0m",
            self.guess
                .chars()
                .zip(self.letter_scores.clone())
                .map(|(letter, score)| format!(
                    "{}{}",
                    match score {
                        LetterScore::Correct => "\x1b[1;32m",
                        LetterScore::IncorrectSpot => "\x1b[1;33m",
                        LetterScore::NotInWord => "\x1b[1;31m",
                    },
                    letter.to_ascii_uppercase()
                ))
                .collect::<Vec<String>>()
                .join("")
        );
    }
}

pub trait WordleGame {
    fn new() -> Self;
    fn guess(&mut self, guess: &String) -> GuessResponse;
}

pub struct NormalGame {
    answer: String,
    tries: u8,
}

impl WordleGame for NormalGame {
    fn new() -> NormalGame {
        return NormalGame {
            answer: get_random_word(),
            tries: 0,
        };
    }

    fn guess(&mut self, guess: &String) -> GuessResponse {
        self.tries += 1;
        return GuessResponse::new(guess, &self.answer);
    }
}
