import os
import re
import ebooklib
import nltk
import pickle
from ebooklib import epub
from bs4 import BeautifulSoup
from tqdm import tqdm
from string import punctuation
from nltk.corpus import stopwords
from nltk import sent_tokenize, wordpunct_tokenize

import config

nltk.download('punkt')
nltk.download('stopwords')


def epub2thtml(epub_path):
    book = epub.read_epub(epub_path)
    chapters = []
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            chapters.append(item.get_content())
    return chapters


# there may be more elements you don't want, such as "style", etc.
blacklist = [
    '[document]',
    'noscript',
    'header',
    'html',
    'meta',
    'head',
    'input',
    'script',
]


def chap2text(chap):
    output = ''
    soup = BeautifulSoup(chap, 'html.parser')
    text = soup.find_all(text=True)
    for t in text:
        if t.parent.name not in blacklist:
            output += '{} '.format(t)
    return output


def thtml2ttext(thtml):
    Output = []
    for html in thtml:
        text = chap2text(html)
        Output.append(text)
    return Output


def epub2text(epub_path):
    chapters = epub2thtml(epub_path)
    ttext = thtml2ttext(chapters)
    return ttext


def get_book_text(book_filepath):
    if book_filepath.endswith('.txt'):
        try:
            with open(book_filepath, 'r') as fin:
                book_text = fin.read()
                return book_text
        except UnicodeDecodeError:
            with open(book_filepath, 'r', encoding='cp1251') as fin:
                book_text = fin.read()
                return book_text
        except:
            print(f"Could not open '{book_filepath}'. Skipping it.\n")
            return None
    elif book_filepath.endswith('.epub'):
        try:
            book_text_list = epub2text(book_filepath)
            book_text = " ".join(book_text_list)
            return book_text
        except:
            print(f"Could not open '{book_filepath}'. Skipping it.\n")
            return None
    else:
        print(f"Wrong format of book '{book_filepath}'. Can process only '.txt' or '.epub' formats.\n")
        return None


# ------------------ Version 1 --------------------

def read_common_words(filepath: str):
    with open(filepath, 'r') as fin:
        common_words = fin.read().split("\n")

    common_words = [w.lower() for w in common_words]
    common_words = set(common_words).union(set(stopwords.words('english')))
    return common_words


def clean_word(word):
    for p in punctuation:
        if p in word:
            word = word.replace(p, "")
    return word.lower()


def get_book_stats(book_filepath):
    book_text = get_book_text(book_filepath)
    chapters = book_text.split("\n\n")

    common_words = read_common_words(config.BookScoreConfigV1.common_words_path)

    n_sents = 0
    n_words = 0
    n_uncommon_words = 0
    unique_words = set()

    for ch in tqdm(chapters, desc="Chapters", disable=config.tqdm_disable):
        sents = sent_tokenize(ch)
        n_sents += len(sents)
        for sent in tqdm(sents, desc="Sentences", leave=False, disable=config.tqdm_disable):
            words = [clean_word(w) for w in sent.split()]
            n_words += len(words)
            n_uncommon_words += len([w for w in words if w not in common_words])
            unique_words = unique_words.union(set(words))

    return {'n_sents': n_sents,
            'n_words': n_words,
            'n_uncommon_words': n_uncommon_words,
            'n_unique_words': len(unique_words),
            'average_sentence_length': round(n_words / n_sents, 1)}


def get_book_score_v1(book_filepath: str):
    book_stats = get_book_stats(book_filepath=book_filepath)

    weights = config.BookScoreConfigV1.weights
    normalization_coefs = config.BookScoreConfigV1.normalization_coefs

    book_score = 0
    for k in weights.keys():
        v = book_stats[k]
        score = round((v / normalization_coefs[k]) * weights[k] * 10) * 10
        book_score += score

    book_score = max(config.BookScoreConfigV1.MIN_BOOK_SCORE, book_score)
    book_score = min(config.BookScoreConfigV1.MAX_BOOK_SCORE, book_score)

    return book_score


# ----------------------------------------------------------------

# ---------------------- Version 2 -------------------------------


def is_special_match(w, search=re.compile(r"[^a-zA-Z.’'-]").search):
    return not bool(search(w))


def is_word(w):
    if "-" in w:
        splits = w.split("-")
        for sub_w in splits:
            if not sub_w.isalpha():
                return False
        return True

    elif w.isalpha():
        return True
    else:
        return is_special_match(w)


def get_top_word_freqs_blocks():
    if os.path.exists(config.BookScoreConfigV2.top_wiki_word_blocks_path):
        with open(config.BookScoreConfigV2.top_wiki_word_blocks_path, "rb") as f:
            top_wiki_word_blocks = pickle.load(f)
        return top_wiki_word_blocks

    with open(config.BookScoreConfigV2.word_freqs_path, "r") as fin:
        top_wiki_text = fin.read()

    top_wiki_words = []
    for s in top_wiki_text.split("\n"):
        try:
            top_wiki_words.append(s.split()[0])
        except Exception as e:
            print(s)
            print(e)
            continue

    top_wiki_words = [w for w in top_wiki_words if is_word(w)]

    top_wiki_word_blocks = {}

    word_order_sep_indices = config.BookScoreConfigV2.word_order_sep_indices

    for i in range(len(word_order_sep_indices) - 1):
        start_idx = word_order_sep_indices[i]
        end_idx = word_order_sep_indices[i + 1]

        block_name = f"{i} block [{start_idx} - {end_idx}]"

        set_of_block_words = set(top_wiki_words[start_idx:end_idx])

        top_wiki_word_blocks[block_name] = set_of_block_words

    with open(config.BookScoreConfigV2.top_wiki_word_blocks_path, "wb") as f:
        pickle.dump(top_wiki_word_blocks, f)

    return top_wiki_word_blocks


def get_book_score_v2(book_filepath):
    top_wiki_word_blocks = get_top_word_freqs_blocks()

    book_text = get_book_text(book_filepath)
    book_words = wordpunct_tokenize(book_text)
    book_words_clean = [w.lower() for w in book_words if is_word(w)]

    word_indices_block_count = {}
    for block_name, set_of_words in top_wiki_word_blocks.items():
        word_indices_block_count[block_name] = 0
    word_indices_block_count[f"{len(top_wiki_word_blocks)} block out_of_range"] = 0

    out_of_range_words = set()

    for w in tqdm(book_words_clean, disable=config.tqdm_disable):
        found = False
        for block_name, set_of_words in top_wiki_word_blocks.items():
            if w in set_of_words:
                word_indices_block_count[block_name] += 1
                found = True
                break
        if not found:
            word_indices_block_count[f"{len(top_wiki_word_blocks)} block out_of_range"] += 1
            out_of_range_words.add(w)

    x = sorted(word_indices_block_count.keys(), key=lambda x: int(x.split()[0]))
    y = [word_indices_block_count[k] for k in x]
    x = ["".join(k.split()[2:]) for k in x]

    coeffs = config.BookScoreConfigV2.get_coeffs(y)
    normalization_coef = config.BookScoreConfigV2.normalization_coef

    score= 0
    score_2 = 0

    for c, freq in zip(coeffs, y):
        score += c * freq

    # skip out of range score
    score_2 = score - c * freq

    score = score // normalization_coef
    score_2 = score_2 // normalization_coef

    return {"score": score,
            "score_2": score_2,
            "bins": x,
            "counts": y,
            "out_of_range_words": out_of_range_words}
# ----------------------------------------------------------------
