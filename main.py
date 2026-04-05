from contractual import Int, Float, contract, Dict


@contract
def example(x: Int > 1, y: Float == 0, z: Dict.max_len(3)):
    return x, y, z


@contract
def multiply(x: Float > 2, y: Float > 10) -> Float > 20:
    return x * y


if __name__ == "__main__":
    print(example(2, 0, {"x": 1, "y": 2, "z": 3}))
    print(multiply(4, 20))
