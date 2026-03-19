from contractual import Int, Float, contract, Dict


@contract
def example(x: Int > 1, y: Float == 0, z: Dict.max_len(2)):
    print(x, y, z)


if __name__ == "__main__":
    example(2, 0, {"x": 1, "y": 2, "z": 3})
