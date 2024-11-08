import pprint

class Matrice:
    def __init__(self, rows: int, cols: int, name: str = ""):
        self.data = [[[] for _ in range(cols)] for _ in range(rows)]
        self.rows = rows
        self.cols = cols
        self.name = name
        self.dimensions = f"{rows}x{cols}"

    def zeros_matrix(self):
        for i in range(self.rows):
            for j in range(self.cols):
                self.data[i][j] = 0

    """
    This method will return the number of rows.
    """
    def get_rows(self):
        return self.rows

    """
    This method will return the number of columns.
    """
    def get_cols(self):
        return self.cols

    """
    This method will return the name of the matrix.
    """
    def get_name(self):
        return self.name

    """
    This method will return one value of the matrix.
    """
    def get_element(self, row, col):
        return self.data[row][col]  # Access the element using list indexing

    """
    This method will return the dimensions of the matrix.
    """
    def get_dimensions(self):
        return self.dimensions

    """
    This method will set an element of a matrix.
    """
    def set_element(self, row, col, value):
        self.data[row][col] = value

    """
    This method will do a mathematical addition between the current matrix and another matrix.
    """
    def add(self, other):
        if self.rows != other.get_rows() or self.cols != other.get_cols():
            raise ValueError("Matrices must have the same dimensions to add.")

        result = Matrice(self.rows, self.cols, self.name + "'")
        for i in range(self.rows):
            for j in range(self.cols):
                result.set_element(i, j, self.get_element(i, j))  # Copy existing requests

        return result

    """
    This method will perform a mathematical subtraction between the current matrix and another matrix.
    """
    def subtraction(self, other):
        raise NotImplementedError("Subtraction is not defined for this matrix implementation.")

    """
    This method will transpose the current matrix and return a new matrix.
    """
    def transpose(self):
        result = Matrice(self.cols, self.rows, self.name + "_Transposed")
        for i in range(self.rows):
            for j in range(self.cols):
                result.set_element(j, i, self.get_element(i, j))  # Switch rows and columns
        return result

    """
    This method will multiply the current matrix with a scalar.
    """
    def multiply(self, scalar):
        result = Matrice(self.rows, self.cols, self.name + "'")
        for i in range(self.rows):
            for j in range(self.cols):
                for req in self.get_element(i, j):
                    result.set_element(i, j, req * scalar)  # Modify request according to your requirements

        return result

    """
    This method will modify the current matrix dimensions and return a new matrix with values set to 0.
    """
    def modify_dimensions(self, rows, cols):
        self.data = [[[] for _ in range(cols)] for _ in range(rows)]
        self.rows = rows
        self.cols = cols
        self.dimensions = f"{rows}x{cols}"

    def print_matrix(self):
        pprint.pprint(self.data)

    """
    This method will print out the current matrix.
    """
    def __repr__(self):
        return f"{self.name}:\n{self.data}"