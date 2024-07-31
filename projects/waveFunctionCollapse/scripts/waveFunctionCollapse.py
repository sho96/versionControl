import random
import cv2
import numpy as np
from tqdm import tqdm

class imgGrid:
    def __init__(self, cellSize, gridSize):
        self.cellSize = cellSize
        self.gridSize = gridSize
        self.wholeImg = np.zeros((cellSize[1] * gridSize[1], cellSize[0] * gridSize[0], 3))
    def fill(self, pos, img):
        realorigin = np.array(pos) * self.cellSize
        endingPoint = (realorigin[0] + img.shape[1], realorigin[1] + img.shape[0])
        self.wholeImg[realorigin[1]:endingPoint[1], realorigin[0]:endingPoint[0]] = img/255
    def getImg(self):
        return self.wholeImg
    def showImg(self, winname="grid", waitkey = 0, ratio=1):
        result = cv2.resize(self.wholeImg, dsize=(int(self.gridSize[1]*self.cellSize[1]*ratio), int(self.gridSize[0]*self.cellSize[0]*ratio)), interpolation=cv2.INTER_NEAREST)
        cv2.imshow(winname, self.wholeImg)
        cv2.waitKey(waitkey)


w, h = (100, 100)
grid = imgGrid((16,16), (w, h))
blank = cv2.imread("blank1.png")
cross = cv2.imread("cross2.png")
right = cv2.imread("right2.png")
left = cv2.rotate(right, cv2.ROTATE_180)
cv2.imshow("left", left)
up = cv2.rotate(right, cv2.ROTATE_90_COUNTERCLOCKWISE)
down = cv2.rotate(right, cv2.ROTATE_90_CLOCKWISE)
tiles = [
    blank,
    cross,
    up,
    right,
    down,
    left
]
#up, right, down, left
rules = [
    (
        [0, 2],
        [0, 3],
        [0, 4],
        [0, 5]
    ),
    (
        [1, 3, 4, 5],
        [1, 2, 4, 5],
        [1, 2, 3, 5],
        [1, 2, 3, 4],
    ),
    (
        [1, 3, 4, 5],
        [1, 2, 4, 5],
        [0, 4],
        [1, 2, 3, 4],
    ),
    (
        [1, 3, 4, 5],
        [1, 2, 4, 5],
        [1, 2, 3, 5],
        [0, 5],
    ),
    (
        [0, 2],
        [1, 2, 4, 5],
        [1, 2, 3, 5],
        [1, 2, 3, 4],
    ),
    (
        [1, 3, 4, 5],
        [0, 3],
        [1, 2, 3, 5],
        [1, 2, 3, 4],
    ),
]

def printGrid(grid):
    for line in grid:
        print(line)

def optimize(currentOptions, direction, tile):
    if len(currentOptions) == 0:
        raise Exception()
    if len(currentOptions) == 1:
        return currentOptions
    newoptions = []
    #print(currentOptions)
    for i, rule in enumerate(rules):
        #print(rule[direction])
        if tile in rule[direction]:
            if i in currentOptions:
                newoptions.append(i)
    #print(newoptions)
    return newoptions

def update(pos, tile, options):
    global filledCells
    options = list(options)
    #print(f"filled with {tile} at {pos}")
    filledCells.add(pos)
    grid.fill(pos, tiles[tile])
    x, y = pos
    ops=[
        "options[y-1][x] = optimize(options[y-1][x], 2, tile)",
        "options[y][x+1] = optimize(options[y][x+1], 3, tile)",
        "options[y+1][x] = optimize(options[y+1][x], 0, tile)",
        "options[y][x-1] = optimize(options[y][x-1], 1, tile)"
    ]
    supported = [0, 1, 2, 3]
    if x == 0:
        supported.remove(3)
    if x == w-1:
        supported.remove(1)
    if y == 0:
        supported.remove(0)
    if y == h-1:
        supported.remove(2)
    for op in supported:
        #print("op", op)
        exec(ops[op])
    return options
    

options=[]
for y in range(h):
    temp = []
    for x in range(w):
        temp.append([0,1,2,3,4,5])
    options.append(temp)

filledCells = set()

options[0][0] = [1,]
update((0,0), 1, options)

for i in tqdm(range(w*h)):
    #printGrid(options)
    minimumNumberOfOptions = 5
    for y in range(h):
        for x in range(w):
            if len(options[y][x]) < minimumNumberOfOptions and len(options[y][x]) != 1:
                minimumNumberOfOptions = len(options[y][x])
    if minimumNumberOfOptions == 5:
        break
    found = False
    for y in range(h):
        for x in range(w):
            if len(options[y][x]) == minimumNumberOfOptions:
                options[y][x] = [random.choice(options[y][x]),]
                options = update((x, y), options[y][x][0], options)
                found = True
                break
        if found:
            break
    for y in range(h):
        for x in range(w):
            if len(options[y][x]) == 1 and not((x, y) in filledCells):
                grid.fill((x,y), tiles[options[y][x][0]])
                options = update((x,y), options[y][x][0], options)

    #printGrid(options)
    #grid.showImg(waitkey=1, ratio=0.5)

for y in range(h):
    for x in range(w):
        grid.fill((x,y), tiles[options[y][x][0]])

grid.showImg(ratio=5)