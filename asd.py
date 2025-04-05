import matplotlib.pyplot as plt
import numpy as np

# Данные по популярным зонам (пример вашего JSON)
popular_zones = [
    {"x": 0, "z": 0, "visits": 11},
    {"x": 1, "z": 0, "visits": 6},
    {"x": 2, "z": 0, "visits": 6},
    {"x": 3, "z": 0, "visits": 6},
    {"x": 4, "z": 0, "visits": 6},
    {"x": 5, "z": 0, "visits": 6},
    {"x": 6, "z": 0, "visits": 6},
    {"x": 7, "z": 0, "visits": 6},
    {"x": 8, "z": 0, "visits": 6},
    {"x": 9, "z": 0, "visits": 6},
    {"x": 10, "z": 0, "visits": 6},
    {"x": 11, "z": 0, "visits": 6},
    {"x": 12, "z": 0, "visits": 6},
    {"x": 13, "z": 0, "visits": 6},
    {"x": 14, "z": 0, "visits": 6},
    {"x": 15, "z": 0, "visits": 6},
    {"x": 16, "z": 0, "visits": 6},
    {"x": 16, "z": 1, "visits": 5},
    {"x": 16, "z": 2, "visits": 5},
    {"x": 16, "z": 3, "visits": 5},
    {"x": 16, "z": 4, "visits": 5},
    {"x": 16, "z": 5, "visits": 5},
    {"x": 16, "z": 6, "visits": 5},
    {"x": 16, "z": 7, "visits": 5},
    {"x": 16, "z": 8, "visits": 5},
    {"x": 16, "z": 9, "visits": 5},
    {"x": 16, "z": 10, "visits": 5},
    {"x": 16, "z": 11, "visits": 5},
    {"x": 16, "z": 12, "visits": 5},
    {"x": 16, "z": 13, "visits": 5},
    {"x": 16, "z": 14, "visits": 5},
    {"x": 16, "z": 15, "visits": 5},
    {"x": 16, "z": 16, "visits": 5},
    {"x": 17, "z": 0, "visits": 1},
    {"x": 18, "z": 0, "visits": 1},
    {"x": 19, "z": 0, "visits": 1}
]

# Создаем матрицу 20x20, заполненную нулями
grid = np.zeros((20, 20))

# Заполняем матрицу данными. При этом по оси x соответствуют столбцы, а по оси z — строки.
for zone in popular_zones:
    x = zone["x"]
    z = zone["z"]
    visits = zone["visits"]
    grid[z, x] = visits

plt.figure(figsize=(8, 8))
# Визуализируем матрицу. origin="lower" чтобы ось z росла снизу вверх.
img = plt.imshow(grid, cmap="YlOrRd", origin="lower")
plt.colorbar(img, label="Количество визитов")
plt.title("Популярные зоны (сетка 20×20)")
plt.xlabel("x")
plt.ylabel("z")
plt.xticks(range(20))
plt.yticks(range(20))
plt.grid(False)

# Добавляем аннотации для ячеек с ненулевыми визитами
for z in range(20):
    for x in range(20):
        if grid[z, x] > 0:
            plt.text(x, z, int(grid[z, x]), ha='center', va='center', fontsize=8, color='black')

plt.show()
