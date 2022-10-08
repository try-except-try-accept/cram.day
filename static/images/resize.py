from PIL import Image
from os import listdir, mkdir


for f in listdir():

    if f.endswith("jpg") or f.endswith("png"):

        img = Image.open(f)

        x, y = img.size

        if x > 400:

            y = int((400 / x) * y)
            x = 400

        elif y > 600:
            x = int((600 / y) * x)
            y = 600

        img = img.resize((x, y), Image.Resampling.LANCZOS)

        img.save("resized/"+f, quality=95)
