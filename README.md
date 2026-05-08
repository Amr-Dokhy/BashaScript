# BashaScript Compiler

Custom Arabic-inspired programming language compiler built with Python, featuring GUI, lexer, parser, semantic analysis, Python code generation, and execution support.

## Features

* Lexical Analysis (Scanner)
* Parsing & AST Generation
* Semantic Analysis
* Python Code Generation
* GUI Compiler Interface
* Custom Arabic-like Syntax

## Example

```bashascript
yalla {
    daraga = 75
    lw daraga >= 50 {
        ekteb("ناجح")
    } nafez {
        ekteb("راسب")
    }
}
```

## Run

```bash
python gui.py
```

## Project Structure

* `main.py` → Compiler core
* `gui.py` → GUI interface
* `code.txt` → Source code input
