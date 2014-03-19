import collections
import csv
import sys

class SimilarityGrid(collections.MutableMapping):
    """A dictionary of similarity scores by rating pairs."""
    def __init__(self, minRating, maxRating, stepRating):
        self.minRating = minRating
        self.maxRating = maxRating
        self.stepRating = stepRating
        self.store = {}
        # initialize grid
        for key in self:
            self[key] = [0, 0]
        # include null entry for bad keys
        self[(self.maxRating, self.maxRating)] = None

    def __keytransform__(self, key):
        rating1 = min(key[0], key[1])
        rating2 = max(key[0], key[1])
        if rating1 < self.minRating or\
           rating2 > self.maxRating - self.stepRating:
            return -1
        idx = 0
        p = self.minRating
        while p < self.maxRating:
            q = p
            while q < self.maxRating:
                if rating1 >= p and rating1 < p + self.stepRating and\
                   rating2 >= q and rating2 < q + self.stepRating:
                    return idx
                idx += 1
                q += self.stepRating
            p += self.stepRating
        raise Exception("Unreachable code.")

    def __getitem__(self, key):
        return self.store[self.__keytransform__(key)]

    def __setitem__(self, key, value):
        self.store[self.__keytransform__(key)] = value

    def __delitem__(self, key):
        del self.store[self.__keytransform__(key)]

    def __len__(self):
        return len(self.store)

    def __iter__(self):
        self.current = [self.minRating, self.minRating]
        return self

    def next(self):
        if self.current[0] >= self.maxRating and\
           self.current[1] >= self.maxRating:
            raise StopIteration
        elif self.current[1] >= self.maxRating:
           self.current[0] += self.stepRating
           self.current[1] = self.current[0] + self.stepRating
        else:
           self.current[1] += self.stepRating
        return (round(self.current[0], 3),
                round(self.current[1] - self.stepRating, 3))

    def writeToFile(self, outputFile):
        writer = csv.writer(outputFile)
        for (rating1, rating2) in self:
            entry = self[(rating1, rating2)]
            if entry:
                writer.writerow([round(rating1, 3), round(rating2, 3),
                                 entry[0], entry[1]])

    def readFromFile(self, inputFile):
        reader = csv.reader(inputFile)
        for row in reader:
            rating1 = float(row[0])
            rating2 = float(row[1])
            scoreTotal = float(row[2])
            count = int(row[3])
            if not self[(rating1, rating2)]:
                print >> sys.stderr,\
                    'WARNING: (%0.3f, %0.3f) not found.' % (rating1, rating2)
            else:
                self[(rating1, rating2)][0] = scoreTotal
                self[(rating1, rating2)][1] = count

