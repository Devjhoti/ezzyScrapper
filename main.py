import sys
import os

if getattr(sys, "frozen", False):
    os.environ["RAPIDOCRONNXRULE_MODEL_DIR"] = os.path.join(
        sys._MEIPASS, "rapidocr_onnxruntime", "models"
    )


def cli_run():
    import traceback

    log_path = os.path.abspath("ezzylog.txt")
    try:
        import glob
        import csv

        import core

        args = [a for a in sys.argv[1:] if a != "--cli"]
        target = args[0] if args else "."
        if os.path.isdir(target):
            images = [
                os.path.join(target, f)
                for f in sorted(os.listdir(target))
                if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".webp", ".tiff", ".gif"))
            ]
        else:
            images = glob.glob(target)
        rows = core.scrape_images(images)
        out = os.path.abspath("leads.csv")
        with open(out, "w", newline="", encoding="utf-8-sig") as fh:
            writer = csv.writer(fh)
            writer.writerow(["Business Name", "Category", "Address", "Phone"])
            writer.writerows(rows)
        with open(log_path, "w", encoding="utf-8") as fh:
            fh.write(f"OK {len(rows)} rows\n")
        print(f"WROTE {len(rows)} ROWS TO {out}")
    except Exception as e:
        with open(log_path, "w", encoding="utf-8") as fh:
            fh.write(traceback.format_exc())
        print(f"ERROR {e}")


if __name__ == "__main__":
    if "--cli" in sys.argv:
        cli_run()
    else:
        from app_gui import main

        main()