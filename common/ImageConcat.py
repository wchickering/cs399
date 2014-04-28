#!/usr/bin/env python

"""
Constructs an image by concatenating two provided images side-by-side.
"""

from PIL import Image
import sys

def concatImages(images):
    width = sum(i.size[0] for i in images)
    height = max(i.size[1] for i in images)
    resultImage = Image.new('RGBA', (width, height))
    x = 0
    for i in images:
        resultImage.paste(i, (x, 0))
        x += i.size[0]
    return resultImage

def concatImageFiles(imageFileNames, saveFileName):
    images = map(Image.open, imageFileNames)
    resultImage = concatImages(images)
    resultImage.save(saveFileName)

def main():
    if not len(sys.argv) > 3:
        raise SystemExit("Usage: %s src1 [src2] .. dest" % sys.argv[0])

    concatImageFiles(sys.argv[1:-1], sys.argv[-1])

if __name__ == '__main__':
    main()

