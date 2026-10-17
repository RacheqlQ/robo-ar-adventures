# Robo Learns to See: book source

    pip install reportlab pillow
    python make_books.py     # builds the 3 KDP interior PDFs + classroom QR cards into ./out
    python preflight.py      # optional checks (needs poppler-utils, opencv-python)

* Edit `urls.json` to change where the QR codes point, then re-run `make_books.py`.
* Edit `bookcopy.py` for front/back-matter wording and the AR guide page.
* Fonts: Poppins (set POPPINS_DIR to the folder containing Poppins-*.ttf).
* `build_ar.py` regenerates the three AR web pages.
* The preflight script reads `urls.json`; paths inside it point at /mnt/user-data/outputs, so edit them if you run it elsewhere.
