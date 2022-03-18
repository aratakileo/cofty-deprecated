# The Cofty Programming Language
This is the main source code repository for Cofty. It contains the compiler, standard library, and documentation.

<!--A smart compiler makes it possible to write less code with the same efficiency and safy of its execution as if you were writing it by [Rust](https://www.rust-lang.org).-->

[`Python >= 3.10`]: https://www.python.org/downloads/

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
  - [ ] base constructions
    - [x] `if`, `elif`, `else`
    - [ ] `while`
    - [ ] `for`
  - [x] functions initialization
    - [x] without arguments
    - [x] with arguments
    - [x] supports returned type specifications
  - [ ] calling names
    - [ ] without arguments
    - [ ] with arguments
  - [ ] supports single line code body

### Installing
At first, you need
- `gcc`
- [`Python >= 3.10`]

> __*The compilation of the code is not ready yet, and the language itself is not finished yet and does not have support for the minimum allowable syntax. Using the project's capabilities at this stage is at your own risk!*__

<!--
# Different languages syntax comparison
### Program starting
- Cofty
```sql
-- your code here
```
- Cofty (alternative)
```applescript
fn main() {
    -- your code here
}
```

### Output `Hello World!`
- Future Cofty
```python
print('Hello World!')
```
- Current Cofty
```diff
! That method is not exist now
```
- Rust
```Rust
fn main() {
    println!("Hello World!");
}
```
- C++
```cpp
#include <iostream>

int main() {
    std::cout << "Hello World!" << std::endl;
    return 0;
}
```
-->
