from __future__ import annotations

from backend.app.domain import Matrix4


def identity_matrix() -> Matrix4:
    return [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]


def translation_matrix(x: float, y: float, z: float) -> Matrix4:
    matrix = identity_matrix()
    matrix[0][3] = float(x)
    matrix[1][3] = float(y)
    matrix[2][3] = float(z)
    return matrix


def multiply_matrix(left: Matrix4, right: Matrix4) -> Matrix4:
    result = [[0.0 for _ in range(4)] for _ in range(4)]
    for row in range(4):
        for column in range(4):
            result[row][column] = sum(
                left[row][index] * right[index][column] for index in range(4)
            )
    return result


def rigid_inverse(matrix: Matrix4) -> Matrix4:
    rotation = [[matrix[row][column] for column in range(3)] for row in range(3)]
    translation = [matrix[row][3] for row in range(3)]
    inverse_rotation = [
        [rotation[column][row] for column in range(3)] for row in range(3)
    ]
    inverse_translation = [
        -sum(inverse_rotation[row][column] * translation[column] for column in range(3))
        for row in range(3)
    ]
    inverse = identity_matrix()
    for row in range(3):
        for column in range(3):
            inverse[row][column] = inverse_rotation[row][column]
        inverse[row][3] = inverse_translation[row]
    return inverse


def translation_of(matrix: Matrix4) -> tuple[float, float, float]:
    return matrix[0][3], matrix[1][3], matrix[2][3]


def axis_to_usd_token(axis: tuple[float, float, float] | None) -> str:
    if axis is None:
        return "Z"
    absolute = [abs(value) for value in axis]
    index = absolute.index(max(absolute))
    return ["X", "Y", "Z"][index]


def format_usd_matrix(matrix: Matrix4) -> str:
    row_strings = []
    for row in matrix:
        row_strings.append(
            "(" + ", ".join(f"{value:.6f}" for value in row) + ")"
        )
    return "(" + ", ".join(row_strings) + ")"

