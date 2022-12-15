### Get score of a book based on statistics and word frequencies.

---
#### How it works
There are two versions:

`book_score_v1` - uses book statistics such as words counts, sentences count, uncommon words count, number of unique words and average sentence length.

`book_score_v2` - uses word frequencies. There are two types:
    
- `type_1`: does not ignore words that are out of range of frequencies.
- `type_2`: ignores words that are out of range of frequencies.

---

#### How to run:
```shell
python main.py -p /path/to/the/book
```

#### Example:
```shell
 python main.py -p sample_books/non-fiction/Blaser,_Martin_Missing_Microbes_How_the_Overuse_of_Antibiotics_Is.epub
```

Result:
```
Book score V1: 150
Book score V2 type 1:  344
Book score V2 type 2:  140
```