"""
core/size.py
============
Size-এর সব function ও logic (SS27 / app 1 থেকে)।

  extract_sizes_from_pdf()  PDF-এর "Sizes" অংশ থেকে সব size -> "S, M, L"
  split_sizes()             "S, M, L" -> ["S", "M", "L"]
"""
import re

# একটা size token: 9/10, 15, 3/4, 92-98, S, M, XL, XXL, S/M ...
SIZE_PATTERN = re.compile(
    r"^(?:\d+(?:[/-]\d+)?|[A-Za-z]{1,4}(?:/[A-Za-z]{1,4})?)$",
    re.IGNORECASE,
)


def extract_sizes_from_pdf(pages_text):
    """
    PDF থেকে size বের করে, লাইন ভেঙে থাকলেও কাজ করে।
    Supports:
      - 9/10, 11/12, 13/14, 15
      - S, M, L, XL, XXL
      - 3/4, 4/5, 5/6 ...
      - 6/9, 9/12, 12/18 ...
      - 92-98, 98-104, 110-116, 122-128
      - এক লাইনে কমা দিয়ে একাধিক size

    "Sizes" লাইনের পর থেকে "TOTAL" পর্যন্ত পড়ে ("COLOUR" লাইন বাদ)।
    Return: "S, M, L" (কমা দিয়ে জোড়া)। না পেলে ""।
    """
    for text in pages_text:
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        for idx, line in enumerate(lines):
            if line.lower() != "sizes":
                continue

            sizes = []
            for next_line in lines[idx + 1:]:
                upper = next_line.upper()

                if upper == "TOTAL":
                    break
                if upper == "COLOUR":
                    continue

                for cand in re.split(r"\s*,\s*", next_line):
                    cand = cand.strip()
                    if not cand:
                        continue
                    if SIZE_PATTERN.fullmatch(cand) and cand.upper() not in ("COLOUR", "TOTAL"):
                        sizes.append(cand)

            if sizes:
                return ", ".join(sizes)

    return ""


def split_sizes(sizes):
    """
    "S, M, L" -> ["S", "M", "L"]।
    ফাঁকা / None হলে [""] (app 1-এর মতো, যাতে zip-এ কাজ করে)।
    """
    return [s.strip() for s in sizes.split(",")] if sizes else [""]
