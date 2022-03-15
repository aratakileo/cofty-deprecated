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

### Installing
At first, you need
- `gcc`
- [`Python >= 3.10`]

> __*The compilation of the code is not ready yet, and the language itself is not finished yet and does not have support for the minimum allowable syntax. Using the project's capabilities at this stage is at your own risk!*__

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
<!--```python
printf('Hello World!')
```-->
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
