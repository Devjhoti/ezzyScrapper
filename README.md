# ezzyScrapper

Turns business-lead screenshots into a structured CSV file — no manual scraping.

`ezzyScrapper` runs OCR on your screenshot images, extracts the business info
(**Business Name**, **Category**, **Address**, **Phone**), removes duplicates and
exports the result to a `.csv` file.

## How to use

1. Run `ezzyScrapper.exe`.
2. Click **+ Select Images** to pick screenshots, or **Open Folder** to load a whole folder.
3. Use **Select All** / **Clear**, or tick/untick individual files.
4. Click **Start Scraping** — a progress bar shows the OCR running over each image.
5. Click **Save CSV…** to write the result wherever you like, then **Open output**
   to view the saved file.

The CSV has four columns:

| Business Name | Category            | Address                | Phone         |
|---------------|---------------------|------------------------|---------------|
| StarCitiesPlumbing | PLUMBING        | 1088thAveSte3R, NewYork | (917) 979-6102 |

## Notes

- Duplicate leads (same business) are removed automatically.
- OCR runs entirely offline on your machine — nothing is uploaded.

## Development

```
pip install -r requirements.txt
python main.py            # run the GUI
pyinstaller ezzyScrapper.spec --noconfirm   # build the exe (output in dist/)
```

- `core.py` — OCR engine + lead parsing.
- `app_gui.py` — the desktop UI.
- `main.py` — entry point (also supports a hidden `--cli <folder>` mode).