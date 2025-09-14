class MovingAverage:
    def __init__(self, size=5):
        self.size = size
        self.numbers = []

    def add(self, num):
        self.numbers.append(num)
        if len(self.numbers) > self.size:
            self.numbers.pop(0)
        return sum(self.numbers) / len(self.numbers)