|============================|
|To list all the categories: |
|============================|

    - python3.6 1mg.py -lc
    - Output:
        
        Label | Count | Pages
        =====================
        a - 21548 - 431
        b - 6168 - 124
        c - 19766 - 396
        d - 10973 - 220
        e - 8886 - 178
        f - 7682 - 154
        g - 6855 - 138
        h - 3024 - 61
        i - 4316 - 87
        j - 1271 - 26
        k - 3626 - 73
        l - 9522 - 191
        m - 13023 - 261
        n - 9035 - 181
        o - 9800 - 196
        p - 12773 - 256
        q - 923 - 19
        r - 11768 - 236
        s - 11429 - 229
        t - 12516 - 251
        u - 2107 - 43
        v - 5654 - 114
        w - 1549 - 31
        x - 1446 - 29
        y - 456 - 10
        z - 5848 - 117

|============================|
|To get data for a category: |
|============================|

    - python3.6 1mg.py -l a -p1 1 -p2 7
    - Output:
        - Stored in excel: "<script-dir>/<output>/<label[a-z]>/<p1>_<p2>.xlsx"
        - Filename format: "<page_from>_<page_to>.xlsx"

|================|
|To get help:    |
|================|

    - python3.6 1mg.py -h
    - Output:
        usage: 1mg.py [-h] [-lc] [-l LABEL] [-p1 PAGE_FROM] [-p2 PAGE_TO]

        optional arguments:
            -h, --help            show this help message and exit
            -lc, --lc             To see how many records in the website
            -l LABEL, --label LABEL
                                    Enter any of [a-z] (lower-case)
            -p1 PAGE_FROM, --page_from PAGE_FROM
            -p2 PAGE_TO, --page_to PAGE_TO
