# The Cofty Programming Language
![Cofty](/cofty_banner.jpg)
This is the main source code repository for Cofty. It contains the compiler, standard library, and documentation.

### The main directions in which we are working in the process of developing this programming language
- More abstractions and syntax sugar (advanced parser)
- Performance and flexibility
<!--A smart compiler makes it possible to write less code with the same efficiency and safy of its execution as if you were writing it by [Rust](https://www.rust-lang.org).-->

[`Python >= 3.10`]: https://www.python.org/downloads/

<!--
### Current project version
- Has
  - tokenizer
  - generator a syntax tree by primitive Cofty syntax
  - smart name handler for name managment
  - errors handler
- Also
  - works only with [`Python >= 3.10`]
- Syntax progress
  - [x] singleline comments
  - [ ] supports value expressions
    - [x] operators
      - [x] priority
      - [x] left
      - [x] middle
    - [ ] number value
      - [x] automatic decimal type specification
      - [x] `i8`, `i16`, `i32`, `i64`
      - [ ] `i128`
      - [x] `u8`, `u16`, `u32`, `u64`
      - [ ] `u128`
      - [x] automatic float type specification
      - [x] `f32`, `f64`
    - [x] string value
    - [x] char value
    - [x] bool value
    - [x] value from name
    - [ ] None value
  - [x] variables system
    - [x] initialization
      - [x] without value
      - [x] automatic type specifications
    - [x] setting values
    - [x] modificators
      - [x] let
      - [x] val
      - [x] mut
  - [ ] base constructions
    - [x] `if`, `elif`, `else`
    - [ ] `while`
    - [ ] `for`
  - [x] functions initialization
    - [x] without arguments
    - [x] with arguments
    - [x] supports returned type specifications
  - [x] calling names
    - [x] without arguments
    - [x] with arguments
  - [ ] supports single line code body
  - [ ] types
    - [x] structures
      - [x] prototype initialization
      - [x] self initialization
    - [ ] classes
-->

### Installing
At first, you need
- `gcc`
- [`Python >= 3.10`]

> __*The compilation of the code is not ready yet, and the language itself is not finished yet and does not have support for the minimum allowable syntax. Using the project's capabilities at this stage is at your own risk!*__

### Code examples

You can also familiarize yourself with the syntax of the language in the [sample code files](https://github.com/aratakileo/cofty/tree/main/syntax-examples) in this programming language.

#### Hello World
```py
print('Hello World!')
```

#### Comment
```sql
-- insert comment here
```

#### Using variables
Just a variable (immutable)
```sql
let a = 123
a = 1234  -- error
```

Mutable variable
```py
let mut hello_world = 'Hello World'
hello_world = 'Hello World!'
```

Constant variable
```kt
val ENDL = c'\n'
```
