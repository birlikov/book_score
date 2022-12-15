tqdm_disable = True


class BookScoreConfigV1:
    weights = {
        'n_words': 0.6,
        'n_unique_words': 0.2,
        'average_sentence_length': 0.2
    }

    normalization_coefs = {
        'n_words': 60_000,
        'n_unique_words': 9_000,
        'average_sentence_length': 10
    }

    MIN_BOOK_SCORE = 10
    MAX_BOOK_SCORE = 500

    common_words_path = "assets/common_words.txt"


class BookScoreConfigV2:
    word_freqs_path = "assets/enwiki-20190320-words-frequency.txt"

    word_order_sep_indices = [0, 1_000, 3_000, 5_000, 10_000, 15_000, 20_000, 30_000, 50_000,
                              100_000, 200_000, 500_000, 1_000_000]

    top_wiki_word_blocks_path = "assets/top_wiki_word_blocks.pkl"

    @staticmethod
    def get_coeffs(y):
        coeffs = [(i + 2) ** 2 for i in range(len(y))]
        return coeffs

    normalization_coef = 10_000