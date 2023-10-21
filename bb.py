class BB:
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.x2 = x + w
        self.y2 = y + h
        self.xc = x + w / 2
        self.yc = y + h / 2
        self.t = -1


    def in_bb(self, x1, y1):
        return not (x1 < self.x or x1 > self.x2 or y1 < self.y or y1 > self.y2)

    def check_distance(self, xc1, yc1, d):
        return abs(self.xc - xc1) < d + self.w / 2 and abs(self.yc - yc1) < d + self.h / 2

    def __getitem__(self, key):
        if key == 'x':
            return self.x
        elif key == 'y':
            return self.y
        elif key == 'w':
            return self.w
        elif key == 'h':
            return self.h
        elif key == 'x2':
            return self.x2
        elif key == 'y2':
            return self.y2
        elif key == 'xc':
            return self.xc
        elif key == 'yc':
            return self.yc
        elif key == 't':
            return self.t
        else:
            raise KeyError(f"Key {key} not found")
