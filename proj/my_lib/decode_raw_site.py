def get_offset(a):
    if 97 <= a <= 122:
        return a - 61
    if 65 <= a <= 90:
        return a - 55
    if 48 <= a <= 71:
        return a - 48
    return -1


def asdf(d):
    g = {
        "": ["&", "=", "p", "6", "?", "H", "%", "B", ".com", "k", "9", ".html", "n", "M", "r", "www.", "h", "b", "t",
             "a", "0", "/", "d", "O", "j", "http://", "_", "L", "i", "f", "1", "e", "-", "2", ".", "N", "m", "A", "l",
             "4", "R", "C", "y", "S", "o", "+", "7", "I", "3", "c", "5", "u", 0, "T", "v", "s", "w", "8", "P", 0, "g",
             0],
        "q": [0, "__3F__", 0, "Photos", 0, "https://", ".edu", "*", "Y", ">", 0, 0, 0, 0, 0, 0, "`", "__2D__", "X", "<",
              "slot", 0, "ShowUrl", "Owners", 0, "[", "q", 0, "MemberProfile", 0, "ShowUserReviews", '"', "Hotel", 0, 0,
              "Expedia", "Vacation", "Discount", 0, "UserReview", "Thumbnail", 0, "__2F__", "Inspiration", "V", "Map",
              ":", "@", 0, "F", "help", 0, 0, "Rental", 0, "Picture", 0, 0, 0, "hotels", 0, "ftp://"],
        "x": [0, 0, "J", 0, 0, "Z", 0, 0, 0, ";", 0, "Text", 0, "(", "x", "GenericAds", "U", 0, "careers", 0, 0, 0, "D",
              0, "members", "Search", 0, 0, 0, "Post", 0, 0, 0, "Q", 0, "$", 0, "K", 0, "W", 0, "Reviews", 0, ",",
              "__2E__", 0, 0, 0, 0, 0, 0, 0, "{", "}", 0, "Cheap", ")", 0, 0, 0, "#", ".org"],
        "z": [0, "Hotels", 0, 0, "Icon", 0, 0, 0, 0, ".net", 0, 0, "z", 0, 0, "pages", 0, "geo", 0, 0, 0, "cnt", "~", 0,
              0, "]", "|", 0, "tripadvisor", "Images", "BookingBuddy", 0, "Commerce", 0, 0, "partnerKey", 0, "area", 0,
              "Deals", "from", "\\", 0, "urlKey", 0, "'", 0, "WeatherUnderground", 0, "MemberSign", "Maps", 0,
              "matchID", "Packages", "E", "Amenities", "Travel", ".htm", 0, "!", "^", "G"]
    };

    b = ""
    a = 0
    while a < len(d):
        h = d[a]
        e = h
        if g.has_key(h) and a + 1 < len(d):
            a += 1
            e += d[a]
        else:
            h = ""

        f = get_offset(ord(d[a]))
        if f < 0:
            b += e
        else:
            b += g[h][f]
        a += 1
    return b


def decode_raw_site(raw_site):
    return "http://www.tripadvisor.cn" + asdf(raw_site)


if __name__ == '__main__':
    # encode_str = 'LqMWJQzZYUWJQpEcYGII26XombQQoqnQQQQoqnqgoqnQQQQoqnQQQQoqnQQQQoqnqgoqnQQQQoqnQQuuuQQoqnQQQQoqnxioqnQQQQoqnQQt9gIi2iEnGJEMQQoqnQQQQoqnxioqnQQQQoqnQQniaQQoqnQQQQoqnqgoqnQQQQoqnQQWJQzhY3Knd3ddXATXMMVmUoB'
    encode_str = 'LqMWJQzZYUWJQpEcYGII26XombQQoqnQQQQoqnqgoqnQQQQoqnQQQQoqnQQQQoqnqgoqnQQQQoqnQQuuuQQoqnQQQQoqnxioqnQQQQoqnQQcVHEStIic2JEStQQoqnQQQQoqnxioqnQQQQoqnQQniaQQoqnQQQQoqnqgoqnQQQQoqnQQTEQQoqnQQQQoqnqgoqnQQQQoqnQQEVtIJpEJCItQQoqnQQQQoqnqHoqnQQQQoqnQQVIQQoqnQQQQoqnqHoqnQQQQoqnQQHJEtQQoqnQQQQoqnqgoqnQQQQoqnQQV2SnpEVQQoqnQQQQoqnqgoqnQQQQoqnQQWJQzhY3VddU3mVdHHMVvkMMB'
    print decode_raw_site(encode_str)
