from __future__ import division
import binascii
from SetSimilaritySearch import all_pairs


def similarity_comparison(scripts, threshold):
    """Computes Jaccard similarity for all pairs of scripts and returns pairs of scripts with similarity > threshold."""
    shingles = []

    print("similarity search")
    for script in scripts:
        data = script.replace("\n", " ")

        # table = data.maketrans(string.punctuation, ' '*len(string.punctuation))
        # data = data.translate(table)

        words = data.split()

        # shingles.append(words)

        shingles_in_doc = set()

        for index, _ in enumerate(words):  # - 2):
            # Construct the shingle text by combining three words together.
            # + " " + words[index + 1] + " " + words[index + 2]
            shingle = words[index]

            # Hash the shingle to a 32-bit integer.
            crc = binascii.crc32(shingle.encode('utf-8')) & 0xffffffff
            # Add the hash value to the list of shingles for the current document.
            # Note that set objects will only add the value to the set if the set
            # doesn't already contain it.

            shingles_in_doc.add(crc)

        shingles.append(shingles_in_doc)

    # elapsed = (time.time() - t0)
    # print("sim search prep took ", elapsed, " seconds")

    # t0 = time.time()

    pairs = all_pairs(shingles, similarity_func_name="jaccard",
                      similarity_threshold=threshold)

    list_pairs = list(pairs)

    # for n in list_pairs:
    #     print(names[n[0]], names[n[1]], n[2])

    return list_pairs

    # elapsed = (time.time() - t0)
    # print("sim search calc and printing prep took ", elapsed, " seconds")
