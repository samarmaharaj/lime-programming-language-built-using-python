# 🍋 Lime Programming Language

A modern, expressive programming language built with Python and LLVM, featuring unique syntax and powerful compilation capabilities.

![Lime Logo](assets/lime_icon.ico)

## 🌟 Features

- **Modern Syntax**: Clean, expressive syntax with unique language constructs
- **LLVM Backend**: High-performance compilation using LLVM infrastructure
- **Strong Typing**: Static type system with explicit type annotations
- **Multiple Execution Modes**: Direct execution, compilation, and debugging options
- **Cross-Platform**: Works on Windows, Linux, and macOS
- **Built-in Functions**: Printf, mathematical operations, and more
- **Control Flow**: Support for loops, conditionals, and function calls
- **Import System**: Modular code organization with file imports

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Conda (recommended for environment management)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/lime-programming-language-built-using-python.git
   cd lime-programming-language-built-using-python
   ```

2. **Set up the environment**
   ```bash
   conda create -n lime python=3.12
   conda activate lime
   pip install llvmlite
   ```

3. **Run your first Lime program**
   ```bash
   # Windows Command Prompt
   lime.bat tests/ifAndBoolean.lime
   
   # Windows PowerShell
   ./lime.ps1 tests/ifAndBoolean.lime
   
   # Direct Python execution
   python main.py tests/ifAndBoolean.lime
   ```

## 📝 Language Syntax

### Hello World
```lime
fn main() -> int {
    printf("Hello, Lime! 🍋\n");
    return 0;
}
```

### Variables and Types
```lime
fn main() -> int {
    let a: int = 10;            ... standard declaration ...
    lit b: int be 15 rn         ... alternative syntax ...
    let pi: float = 3.14159;
    return a + b;
}
```

### Functions
```lime
... Standard function declaration ...
fn add(a: int, b: int) -> int {
    return a + b;
}

... Alternative function syntax ...
bruh multiply(a: int, b: int) -> int {
    pause a * b rn              ... pause = return, rn = statement end ...
}

fn main() -> int {
    printf("5 + 3 = %i\n", add(5, 3));
    printf("4 * 7 = %i\n", multiply(4, 7));
    return 0;
}
```

### Control Flow
```lime
fn main() -> int {
    let count: int = 0;
    
    ... While loop ...
    while count < 5 {
        printf("Count: %i\n", count);
        count = count + 1;
    }
    
    ... For loop ...
    for (let i: int = 0; i < 3; i++) {
        printf("Iterator: %i\n", i);
    }
    
    ... Conditional statements ...
    if count == 5 {
        printf("Reached target count!\n");
    } else {
        printf("Count mismatch!\n");
    }
    
    return count;
}
```

### Comments
```lime
... This is a single-line comment ...

... 
   Multi-line comments
   span multiple lines
   like this
...

fn main() -> int {
    let x: int = 42;  ... inline comment ...
    return x;
}
```

### Imports
```lime
import "math.lime"

fn main() -> int {
    let result: int = add(5, 10);  ... function from math.lime ...
    return result;
}
```

## 🛠️ Command Line Usage

### Basic Execution
```bash
lime.bat program.lime                    # Run program
lime.bat program.lime --debug-lexer     # Debug lexer output  
lime.bat program.lime --debug-parser    # Debug parser output
lime.bat program.lime --debug-compiler  # Debug compiler output
lime.bat program.lime --no-run          # Compile only, don't execute
```

### Debug Options
- `--debug-lexer`: Shows tokenization process
- `--debug-parser`: Outputs AST to `debug/ast.json`
- `--debug-compiler`: Outputs LLVM IR to `debug/ir.ll`
- `--no-run`: Compile without execution

## 📁 Project Structure

```
lime-programming-language/
├── 📄 main.py              # Entry point and CLI interface
├── 🔧 lime_lexer.py        # Tokenization and lexical analysis
├── 🏗️ lime_parser.py       # Syntax parsing and AST generation
├── 🌳 lime_ast.py          # Abstract Syntax Tree definitions
├── 🏷️ lime_token.py        # Token definitions and types
├── ⚙️ compiler.py          # LLVM IR generation and compilation
├── 🌍 environment.py       # Variable and function scope management
├── 🦇 lime.bat             # Windows batch launcher
├── 💻 lime.ps1             # PowerShell launcher
├── 📁 tests/               # Example Lime programs
│   ├── ifAndBoolean.lime
│   ├── whileLoop.lime
│   ├── math.lime
│   ├── string.lime
│   └── ...
├── 📁 assets/              # Resources and icons
├── 📁 debug/               # Debug output files
└── 📁 dist/                # Distribution builds
```

## 🧪 Example Programs

### Mathematical Operations
```lime
fn fibonacci(n: int) -> int {
    if n <= 1 {
        return n;
    }
    return fibonacci(n - 1) + fibonacci(n - 2);
}

fn main() -> int {
    printf("Fibonacci(10) = %i\n", fibonacci(10));
    return 0;
}
```

### String Formatting
```lime
fn main() -> int {
    let name: string = "Lime";
    let version: float = 0.1;
    printf("Welcome to %s v%.1f! 🍋\n", name, version);
    return 0;
}
```

## 🏗️ Architecture

Lime follows a traditional compiler pipeline:

1. **Lexical Analysis** (`lime_lexer.py`)
   - Tokenizes source code into meaningful symbols
   - Handles keywords, operators, literals, and identifiers

2. **Syntax Analysis** (`lime_parser.py`) 
   - Builds Abstract Syntax Tree (AST) from tokens
   - Implements recursive descent parsing
   - Handles operator precedence and associativity

3. **Code Generation** (`compiler.py`)
   - Translates AST to LLVM Intermediate Representation
   - Performs type checking and optimization
   - Generates executable machine code

4. **Runtime Environment** (`environment.py`)
   - Manages variable and function scopes
   - Handles symbol resolution and type information

## 🎯 Language Features

### ✅ Implemented
- [x] Variable declarations and assignments
- [x] Arithmetic and logical operations  
- [x] Function definitions and calls
- [x] Control flow (if/else, while, for loops)
- [x] Type system (int, float, string)
- [x] Comments (single and multi-line)
- [x] Import system for modular code
- [x] Printf for formatted output
- [x] LLVM-based compilation

### 🚧 Planned Features
- [ ] Arrays and data structures
- [ ] Object-oriented programming
- [ ] Advanced type inference
- [ ] Standard library expansion
- [ ] Package manager integration
- [ ] IDE support and language server

## 🚀 Distribution

### Executables
The project can be distributed as:
- **Batch File**: `lime.bat` (Windows CMD)
- **PowerShell Script**: `lime.ps1` (Windows PowerShell)  
- **Directory Distribution**: `dist/lime/` (Standalone executable)

See [DISTRIBUTION.md](DISTRIBUTION.md) for detailed distribution information.

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** and add tests in the `tests/` directory
4. **Test your changes**: `lime.bat tests/your-test.lime`
5. **Commit your changes**: `git commit -m 'Add amazing feature'`
6. **Push to the branch**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**

### Development Setup
```bash
# Clone and setup
git clone https://github.com/yourusername/lime-programming-language.git
cd lime-programming-language-built-using-python

# Install development dependencies
conda create -n lime-dev python=3.12
conda activate lime-dev
pip install llvmlite pytest

# Run tests
python main.py tests/test.lime
```

## 📊 Performance

Lime leverages LLVM for high-performance compilation:
- **Compilation Speed**: Fast parsing and AST generation
- **Runtime Performance**: LLVM-optimized executable code
- **Memory Efficiency**: Static typing enables optimization
- **Debugging Support**: Rich debug information and error reporting

## 🏆 Acknowledgments

- **LLVM Project**: For the powerful compilation infrastructure
- **Python Community**: For the excellent development ecosystem  
- **Contributors**: Everyone who has contributed to this project

<div align="center">
  <strong>Built with 💚 and guide from [CodeDucker](https://youtube.com/playlist?list=PLCJHRjnsxJFoK8e-RaNZUa7R4BaPqczHX)</strong><br>
  Made by passionate developers for the programming community
</div>