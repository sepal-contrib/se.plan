def hex_to_RGB(hex):
    """Changes from hex to RGB.

    #FFFFFF -> [255,255,255].
    """
    # Pass 16 to the integer function for change of base
    return [int(hex[i : i + 2], 16) for i in range(1, 6, 2)]


def RGB_to_hex(RGB):
    """[255,255,255] -> "#FFFFFF"."""
    # Components need to be integers for hex to make sense
    RGB = [int(x) for x in RGB]

    return "#" + "".join(
        ["0{0:x}".format(v) if v < 16 else "{0:x}".format(v) for v in RGB]
    )


def linear_gradient(start_hex, finish_hex="#FFFFFF", n=10):
    """Returns a gradient list of (n) colors between two hex colors.

    start_hex and finish_hex should be the full six-digit color string, inlcuding the number sign ("#FFFFFF").
    """
    # Starting and ending colors in RGB form
    s = hex_to_RGB(start_hex)
    f = hex_to_RGB(finish_hex)

    # Initilize a list of the output colors with the starting color
    RGB_list = [s]

    # Calcuate a color at each evenly spaced value of t from 1 to n
    for t in range(1, n):
        # Interpolate RGB vector for color at the current value of t
        curr_vector = []
        for j in range(3):
            curr_vector.append(int(s[j] + (float(t) / (n - 1)) * (f[j] - s[j])))

        # Add it to our list of output colors
        RGB_list.append(curr_vector)

    return color_dict(RGB_list)


def color_dict(gradient):
    """Takes in a list of RGB sub-lists and returns dictionary of colors in Hex."""
    return [RGB_to_hex(RGB) for RGB in gradient]


def gradient(levels: int, palette: list) -> list:
    """Returns a list of colors forming linear gradients between all sequential pairs of colors.

    "lavels" specifies the total number of desired output colors.
    """
    # The number of colors per individual linear gradient
    levels_out = int(float(levels) / (len(palette) - 1))

    # create an initial dictionary for a single pair
    nb_palette = (levels_out + 1) if levels % 2 else levels_out
    gradient = linear_gradient(palette[0], palette[1], nb_palette)

    # add the other color pairs if needed
    if len(palette) > 1:
        for i in range(1, len(palette) - 1):
            next_ = linear_gradient(palette[i], palette[i + 1], levels_out + 1)
            gradient += next_[1:]

    return gradient
