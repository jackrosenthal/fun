use std::io;
use serialport;
use clap::Parser;

#[derive(Parser)]
struct Args {
    #[arg(short, long, default_value = "/dev/ttyUSB0")]
    port: String,

    #[arg(short, long, default_value_t = 4800)]
    baud: u32,
}

fn run_console(&mut port: serialport::SerialPort, &mut input: io::Read,
               &mut output: io::Write) {
    let buf = String::new();

    port.write("hello world".as_bytes()).unwrap();
    input.read_to_string(&mut buf);
    output.write(buf);
}

fn main() {
    let args = Args::parse();

    let builder = serialport::new(args.port, args.baud);
    let mut port = builder.open().unwrap();

    run_console(&mut port, &mut io::stdin(), &mut io::stdout());
}
