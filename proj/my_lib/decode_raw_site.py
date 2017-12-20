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
    #"http://www.tripadvisor.cn" +
    return asdf(raw_site)


if __name__ == '__main__':
    encode_str = 'LqMWJQzZYUWJQpEcYGII26XombQQoqnQQQQoqnqgoqnQQQQoqnQQQQoqnQQQQoqnqgoqnQQQQoqnQQuuuQQoqnQQQQoqnxioqnQQQQoqnQQt9gIi2iEnGJEMQQoqnQQQQoqnxioqnQQQQoqnQQniaQQoqnQQQQoqnqgoqnQQQQoqnQQWJQzhY3Knd3ddXATXMMVmUoB'
    # encode_str = 'LqMWJQzZYUWJQpEcYGII26XombQQoqnQQQQoqnqgoqnQQQQoqnQQQQoqnQQQQoqnqgoqnQQQQoqnQQuuuQQoqnQQQQoqnxioqnQQQQoqnQQcVHEStIic2JEStQQoqnQQQQoqnxioqnQQQQoqnQQniaQQoqnQQQQoqnqgoqnQQQQoqnQQTEQQoqnQQQQoqnqgoqnQQQQoqnQQEVtIJpEJCItQQoqnQQQQoqnqHoqnQQQQoqnQQVIQQoqnQQQQoqnqHoqnQQQQoqnQQHJEtQQoqnQQQQoqnqgoqnQQQQoqnQQV2SnpEVQQoqnQQQQoqnqgoqnQQQQoqnQQWJQzhY3VddU3mVdHHMVvkMMB'
    # print decode_raw_site('PFC2tYyisLGJsi')
    print decode_raw_site('LzW421z1fiaX0tEn1mdokvvmm0zH13dXmKo0zq1U0ze1qWxMJIVxPQz10zL1d0iit1U30tSci13Kd30Hpn9VI1kAvUo30CEJC91U0nEJC91U0ncI1xM0Ia1Am3UKKdm0aJCJyVM1TJctV0nJ22VM1TJctV0GJn1bqiblRb7Rzs0EJIV1UdAkYKk0TVVt1XkAYA30npE1eD70aHc1RNhzs0aHcMVcIJ13mXm0yitixE1RN2Zxd3Nx5dVKHEabx5n55subUtfqIHGkk5CzsxGzz7IuEqnEtku2yv5Ju2i7EqiJbq8EdnTxbIJntq8qiteZtKx2q8rANgIq8xEOrUflqnxXcbSxGIgSzsx5lxXGJQf3QxEqQxXxbq8ohviEqnxEd7sZEGqnQqn0JpSM1AkAHAKvkWvnkMWddmMWJJn3WXH3XUAUTKodH0IIg2V1xMVt9Ii2DVIJ0SCDiCIG1UX0SCq8VJE1XKUk0SCxMJg1Xd0ipIDiCIG1UX0ipIq8VJE1XKUk0ipIxMJg1Xo0MVTQM1TJctV0JMpcIt1X0nGScMQEaQJyVt10Eiiat1U0at91xXfQDVIJW3dXmKoUoUdKAU3KKKKKUoUdUkvKKKKKKUW7dXbbfKmxMbbUzszsXo7KkKqnvdK7k7vzsUXoWK0S91oAvkHmAvk3TmddVUAomodVJXJHTAoHAn0qK1X0zb1xXfQDVIJzQxBzQbsJScJHcVzQDJSCzQxMVt9Ii202ESnVhGiuC1Ukkk0I21z1QDJSCRStI0iH1CVuQIJH0Ji91dnmVUmnonHvXdAdKJUMKX3HK3mkdAVUd')
    # print decode_raw_site('LOpNW6OZ4e0brmAZcHHvwA1sCXbh77HnEUGBtwrFrs7wpg8HawpoBrVaAYr4cfKtacsYVsRNs0JYT9OytYxjTzKhQODUZJaapV5gOrPB32A')
    print decode_raw_site('LzW4217ii9SCyfZ0tEn1UKm3UkvUK0zH13dXmKo0zq1U0ze1qWxMJIVxPQz10zL1d0iit1U30tSci1XdKXA0Hpn9VI1vdKoUm0CEJC91m0nEJC91m0ncI1xM0Ia1Am3UKKdm0aJCJyVM1TJctV0nJ22VM1TJctV0GJn1bqiblRb7Rzs0EJIV1UdAoYkK3dmvKmUmKK0TVVt1XkAY3AmKKom3UooK0npE1eD70aHc1RNhzs0aHcMVcIJ13XAm0yitixE1xEyxMTgMxGZNqnexXUJqQsqn25AUyNrasTzzCAfKx2zCnxdxGxbqitvx23zz2x5zCx2xXNtCKqIqIfGTqihpJoqQxMxEGR9x5MyyCUJhxXqQzsk5HzzmlAZqIrfVxMxdsmssx2WyUQlbzsxExGkOoTxEkX2hWrpvqIohWpXk0JpSM1AkAHAKvkWvnkMWddmMWJJn3WXH3XUAUTKodH0IIg2V1xMVt9Ii2DVIJ0SCDiCIG1UX0SCq8VJE1XKUk0SCxMJg1Xd0ipIDiCIG1UX0ipIq8VJE1XKUk0ipIxMJg1Xo0MVTQM1TJctV0JMpcIt1X0nGScMQEaQJyVt10Eiiat1U0at91xXfQDVIJW3dXmKoUoUdKAU3KKKKKUoUdUkvKKKKKKUW7dXbbfKmxMbbUzszsXo7KkKqnvdK7k7vzsUXoWK0S91oAvkHmAvk3TmddVUAomodVJXJHTAoHAn0qK1m0zb1xXfQDVIJzQxBzQbsJScJHcVzQDJSCzQxMVt9Ii202ESnVhGiuC1Ukko0I21z1QDJSCRStI0iH1CVuQIJH0Ji91mKTkvHXoA3vddXTMJMn3HXXVTJoTHmKA')