"""
boardgrid.py

Общая функция разбиения изображения доски на 64 клетки.
Вынесена отдельно, чтобы её использовали и generate_templates.py, и board_reader.py
— раньше она была продублирована в generate_templates.py.
"""


def split_into_cells(board_img):
    """Возвращает список 8 строк по 8 клеток: cells[row][col] — вырезанный кусок картинки.
    row=0 — верхняя строка изображения, col=0 — левая колонка изображения
    (то есть это "как на экране", а не "как в FEN" — ориентацию учитываем отдельно)."""
    h, w = board_img.shape[:2]
    cell_h, cell_w = h // 8, w // 8
    cells = []
    for row in range(8):
        row_cells = []
        for col in range(8):
            y1, y2 = row * cell_h, (row + 1) * cell_h
            x1, x2 = col * cell_w, (col + 1) * cell_w
            row_cells.append(board_img[y1:y2, x1:x2])
        cells.append(row_cells)
    return cells
