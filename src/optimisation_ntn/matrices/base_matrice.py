import numpy as np

class Matrice:
    def __init__(self, rows, cols, name):
        self.data = np.zeros((rows, cols))
        self.rows = rows
        self.cols = cols
        self.name = name
        self.dimensions = f"{rows}x{cols}"

    """
    This method will return the rows length
    """
    def get_rows(self):
        return self.rows

    """
    This method will return the cols length
    """
    def get_cols(self):
        return self.cols

    """
    This method will return one value of the matrix
    """
    def get_element(self, row, col):
        return self.data[row, col]

    """
    This method will return the dimensions of the matrix
    """
    def get_dimensions(self):
        return self.dimensions

    """
    This method will set an element of a matrix
    """
    def set_element(self, row, col, value):
        self.data[row, col] = value

    """
    This method will do a mathematical additio between the current matrix and the other
    """
    def add(self, other):
        if self.data.shape != other.data.shape:
            raise ValueError("Matrices must have the same dimensions to add.")
        result = Matrice(self.data.shape[0], self.data.shape[1])
        result.data = self.data + other.data
        return result

    """
    This method will transpose the current matrix and will return a new matrix
    """
    def transpose(self):
        result = Matrice(self.data.shape[1], self.data.shape[0])
        result.data = self.data.T
        return result

    """
    This method will multiply the current matrix with the other
    """
    def multiply(self, other):
        if self.data.shape[1] != other.data.shape[0]:
            raise ValueError("Number of columns of the first matrix must equal number of rows of the second.")
        result = Matrice(self.data.shape[0], other.data.shape[1])
        result.data = np.dot(self.data, other.data)
        return result

    """
    This method will modify the current matrix dimensions and will return a new matrix with values set to 0
    """
    def modify_dimensions(self, rows, cols):
        self.data = np.zeros((rows, cols))
        return self

    """
    This method will print out the current matrix
    """
    def __repr__(self):
        return f"{self.name}:\n{self.data}"