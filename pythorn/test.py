import math
import random
from math import ceil

import matplotlib.pyplot as plt

from pythorn.math import rand, number


def letter_to_number(sentence: str):
    """Randomly replace mapped letters in a sentence with lookalike digits."""

    mapping = {
        'o': '0', 'u': '0',
        'i': '1', 'l': '1', 'j': '1',
        'z': '2', 'r': '2', 'n': '2',
        'e': '3', 'c': '3', 'm': '3',
        'a': '4', 'd': '4', 'f': '4',
        's': '5', 'v': '5', 'k': '5',
        'b': '6', 'g': '6', 'w': '6',
        't': '7', 'y': '7', 'x': '7',
        'h': '8', 'q': '8',
        'p': '9'
    }
    letters = {
        "chars": [[], [], [], []]
    }
    chars_1 = ["a", "o", "e", "p", "i", "l", "t", "s", "z"]
    chars_2 = ["j", "f", "b", "g", "r", "y", "m", "u", "k"]
    chars_3 = ["c", "d", "h", "n", "q", "w", "x", "v"]
    total = 0
    chars = list(sentence.lower())
    i = 0
    for char in chars:
        if char in mapping:
            total += 1
            if char not in letters["chars"][0]:
                letters["chars"][0].append(char)
                if char in chars_1:
                    letters["chars"][1].append(char)
                elif char in chars_2:
                    letters["chars"][2].append(char)
                elif char in chars_3:
                    letters["chars"][3].append(char)
                letters[char] = [i]
            else:
                letters[char].append(i)
        i += 1
    print(f"Sentence length: {len(sentence)}")
    print(f"Start Total: {total}")

    # Generate a skewed random percentage between 6% and 90%
    percent_to_convert = min(max(int(random.betavariate(2.5, 4) * 90), 6), 90)
    chars_to_convert = int((percent_to_convert / 100) * total)
    print(f"Percent of total to be converted: {percent_to_convert}")
    print(f"Amount that should be converted: {chars_to_convert}")

    to_convert = []
    pulling = 0
    while len(to_convert) != chars_to_convert:
        if len(letters["chars"][pulling]) == 0:
            pulling += 1
        key = random.choice(letters["chars"][pulling])
        if len(letters[key]) == 0 or (len(letters[key]) <= 1 and pulling != 0):
            letters["chars"][pulling].remove(key)
        else:
            value = random.choice(letters[key])
            letters[key].remove(value)
            to_convert.append(value)
            total -= 1
    print(f"Amount being converted: {len(to_convert)}")
    print(f"End Total: {total}")

    sentence_list = list(sentence)
    for i in to_convert:
        s = sentence_list[i].lower()
        sentence_list[i] = mapping[s]

    return "".join(sentence_list)


# Example Usage
#sent = "The quick brown fox jumps over the lazy dog."
#converted_sentence = letter_to_number(sent)
#print(converted_sentence)


# Generate a new sample with the custom skew function
def skew_test():
    """Plot a large sample from the skew distribution helper."""

    samples = [rand.skew(is_int=True) for _ in range(1000000)]
    samples_counted = {x: 0 for x in range(0, 101)}
    for sample in samples:
        samples_counted[sample] += 1
    print(samples_counted)

    # Display the updated histogram
    plt.hist(samples, bins=101, edgecolor='black', alpha=0.7)
    plt.xlabel('Percentage of Characters Converted')
    plt.ylabel('Frequency')
    plt.title('Custom Skew Distribution')
    plt.axvline(90, color='red', linestyle='dashed', linewidth=1, label=f'Count of 90%: {samples_counted[90]}')
    plt.legend()
    plt.grid(axis='y', linestyle='--', alpha=0.6)
    plt.show()

def number_test():
    """Exercise number helpers interactively from this ad hoc test script."""

    #real = number.RealNum.from_any(0.01)
    #print(real)
    #larger = 0.1
    #print(larger)
    #print(real < larger)
    cal = number.Compute()
    lis = [56, -42, 14, 98]
    print(cal.lcm(*lis))
    print(math.lcm(*lis))
    #print("nth_root(3, 27) =", cal.nth_root(3, 27))  # Should return exactly 3
    #print("nth_root(4, 16) =", cal.nth_root(4, 16))  # Should return exactly 2
    #print("nth_root(3, -27) =", cal.nth_root(3, -27))  # Should return exactly -3
    #print("nth_root(-5, 32) =", cal.nth_root(-5, 32))  # Should return 1/nth_root(32, 5)
    #print("nth_root(-10, 1024) =", cal.nth_root(-10, 1024))  # Should return 1/2
    #print("nth_root(4, 0.0001) =", cal.nth_root(4, 0.0001))  # Should return exactly 0.1
    #print("nth_root(-4, 0.0001) =", cal.nth_root(-4, 0.0001))  # Should return exactly 10
    #print("nth_root(-16, 4) =", cal.nth_root(4, -16))  # Should raise an error (even root of negative)
number_test()
