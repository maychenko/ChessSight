"""
boardgrid.py

Provides a shared helper for splitting a chessboard image into 64 cells.

The function in this module is used by both the template generation
tools and the board reader, so the image-splitting logic is kept here
instead of being duplicated in multiple files.
"""


def split_into_cells(board_img):
    """
    Split a board image into an 8x8 grid of image cells.

    Returns:
        A list of 8 rows containing 8 cells each.

    The returned coordinates follow the image layout:
    row 0 is the top row and column 0 is the leftmost column.
    Chessboard orientation is handled separately by the caller.
    """
    height, width = board_img.shape[:2]

    cell_height = height // 8
    cell_width = width // 8

    cells = []

    for row in range(8):
        row_cells = []

        for col in range(8):
            y1 = row * cell_height
            y2 = (row + 1) * cell_height

            x1 = col * cell_width
            x2 = (col + 1) * cell_width

            row_cells.append(
                board_img[y1:y2, x1:x2]
            )

        cells.append(row_cells)

    return cells