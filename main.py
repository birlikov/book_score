from utils import get_book_score_v1, get_book_score_v2


if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("-p", "--path", required=True, help="Path to the book file in format .epub or .txt")

    args = parser.parse_args()
    path = args.path

    score = get_book_score_v1(book_filepath=path)
    print(f"Book score V1: {score}")

    res = get_book_score_v2(book_filepath=path)
    print(f"Book score V2 type 1: ", res["score"])
    print(f"Book score V2 type 2: ", res["score_2"])