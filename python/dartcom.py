from scipy import sum, average
import imageio
import requests
from io import BytesIO
import os

fdir = os.path.abspath(os.path.dirname(__file__))

zero = imageio.imread(os.path.join(fdir, '../ref_images/zero.png'))
one = imageio.imread(os.path.join(fdir, '../ref_images/one.png'))
two = imageio.imread(os.path.join(fdir, '../ref_images/two.png'))
three = imageio.imread(os.path.join(fdir, '../ref_images/three.png'))
four = imageio.imread(os.path.join(fdir, '../ref_images/four.png'))
five = imageio.imread(os.path.join(fdir, '../ref_images/five.png'))
six = imageio.imread(os.path.join(fdir, '../ref_images/six.png'))
seven = imageio.imread(os.path.join(fdir, '../ref_images/seven.png'))
eight = imageio.imread(os.path.join(fdir, '../ref_images/eight.png'))
nine = imageio.imread(os.path.join(fdir, '../ref_images/nine.png'))
dot = imageio.imread(os.path.join(fdir, '../ref_images/dot.png'))
black = imageio.imread(os.path.join(fdir, '../ref_images/black.png'))

numbers = [zero, one, two, three, four, five, six, seven, eight, nine, dot, black]


def return_digit(image, dig):
    n = 4 + dig * 12
    return image[25:45, n:n+12]

def to_grayscale(arr):
    if len(arr.shape) == 3:
        return average(arr, -1)
    else:   
        return arr

def match_digit(arr1, arr2):
    diff = arr2 - arr1
    return sum(abs(diff))

# Returns the position of the best match out of the possible images definited in numbers
def digit_to_value(arr):
    mini = 80000
    for i in range(0, len(numbers)):
        dum = match_digit(arr, to_grayscale(numbers[i]))
        if dum < mini:
            mini = dum
            result = i
    return result

def image_to_value(im, limit):
    string = ''
    for i in range(0, limit):
        dig = digit_to_value(return_digit(im, i))
        if dig < 10:
            string += str(dig)
        elif dig == 10:
            string += "."
        elif dig == 11: # case where digit is black image
            return string
    return string


def get_rainfall():
    url = "http://www.dartcom.co.uk/images/weather/vws1003.jpg"
    try:
        r = requests.get(url)
        r.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(err)
        sys.exit(1)
    im = imageio.imread(BytesIO(r.content))
    im = to_grayscale(im)
    return float(image_to_value(im, 6))


