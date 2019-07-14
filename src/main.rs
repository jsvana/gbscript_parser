use std::error::Error;
use std::fs::File;
use std::io::prelude::*;
use std::path::Path;
use std::vec::Vec;

struct Argument<'a> {
    name: &'a str,
    values: Vec<&'a str>,
}

struct Function<'a> {
    name: &'a str,
    params: Vec<Argument<'a>>,
}

trait Parser {
    fn parse<'a>(functions: &mut Vec<Function<'a>>, content: &'a str) -> Result<bool, Box<Error>>;
}

struct StartParser {}
struct InParenParser {}
struct ValueParser {}
struct ListParser {}
struct StringParser {}

fn parse_token_and_descend<'a, T: Parser>(
    functions: &mut Vec<Function<'a>>,
    content: &'a str,
    char_to_switch: char,
) -> Result<bool, Box<Error>> {
    let mut token = String::new();
    for (i, c) in content.chars().enumerate() {
        match c {
            c if c.is_alphanumeric() => token.push(c),
            '_' => token.push(c),
            c if c == char_to_switch => {
                println!("Token: {}", token);
                return T::parse(functions, &content[i + 1..]);
            }
            _ => return Err(From::from(format!("Unknown character {}", c))),
        }
    }

    Err(From::from("Not sure how we got here"))
}

impl Parser for StartParser {
    fn parse<'a>(functions: &mut Vec<Function<'a>>, content: &'a str) -> Result<bool, Box<Error>> {
        parse_token_and_descend::<InParenParser>(functions, content, '(')
    }
}

impl Parser for InParenParser {
    fn parse<'a>(functions: &mut Vec<Function<'a>>, content: &'a str) -> Result<bool, Box<Error>> {
        parse_token_and_descend::<ValueParser>(functions, content, '=')
    }
}

impl Parser for ValueParser {
    fn parse<'a>(functions: &mut Vec<Function<'a>>, content: &'a str) -> Result<bool, Box<Error>> {
        if content.len() == 0 {
            return Err(From::from("No value to parse"));
        }

        let first_char = content.chars().next().unwrap();
        if first_char == '[' {
            return ListParser::parse(functions, &content[1..]);
        }

        if first_char == '"' {
            ListParser::parse(functions, &content[1..]);
        }

        Ok(false)
    }
}

impl Parser for ListParser {
    fn parse<'a>(functions: &mut Vec<Function<'a>>, content: &'a str) -> Result<bool, Box<Error>> {
        Err(From::from("Not implemented"))
    }
}

impl Parser for StringParser {
    fn parse<'a>(functions: &mut Vec<Function<'a>>, content: &'a str) -> Result<bool, Box<Error>> {
        Err(From::from("Not implemented"))
    }
}
fn parse_content<'a>(content: &'a str) -> Result<bool, Box<Error>> {
    let mut functions: Vec<Function<'a>> = vec![];
    return StartParser::parse(&mut functions, content);
}

fn main() {
    let path = Path::new("example.gbscript");
    let display = path.display();

    let mut file = match File::open(&path) {
        Err(why) => panic!("Couldn't open {}: {}", display, why.description()),
        Ok(file) => file,
    };

    let mut s = String::new();
    if let Err(why) = file.read_to_string(&mut s) {
        panic!("Couldn't read {}: {}", display, why.description());
    }

    parse_content(&s[..]).unwrap();
}
