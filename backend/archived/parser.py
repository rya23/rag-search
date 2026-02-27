import os
import re
from dataclasses import dataclass
from typing import List
import pymupdf


@dataclass
class ChapterRef:
    book_index: int
    book_title: str
    chapter_title: str
    start_page: int


@dataclass
class ChapterText(ChapterRef):
    text: str


def fix_leading_dropcap_before_heading(text: str) -> str:
    pattern = re.compile(
        r"^\s*([A-Z])\s*\n\s*\n\s*"
        r"(CHAPTER\s+[A-Z0-9\s—-]+)\s*\n\s*"
        r"([A-Z][^\n]+)\s*\n\s*"
        r"([A-Za-z])",
        re.DOTALL,
    )

    def repl(m):
        return f"{m.group(1)}{m.group(4)}"

    return pattern.sub(repl, text)


def extract_chapter_refs(
    doc: pymupdf.Document,
    books_to_skip: int = 0,
) -> List[ChapterRef]:
    toc = doc.get_toc()

    chapters: List[ChapterRef] = []
    current_book_index = 0
    current_book_title = None

    for level, title, page in toc:
        if level == 1:
            current_book_index += 1
            if current_book_index <= books_to_skip:
                current_book_title = None
                continue
            current_book_title = title

        elif level == 2 and current_book_title and title.startswith("Chapter"):
            chapters.append(
                ChapterRef(
                    book_index=current_book_index - books_to_skip,
                    book_title=current_book_title,
                    chapter_title=title,
                    start_page=page - 1,
                )
            )

    return chapters


def extract_chapter_texts(
    file_path: str,
    books_to_skip: int = 0,
) -> List[ChapterText]:
    doc = pymupdf.open(file_path)
    chapters = extract_chapter_refs(doc, books_to_skip)

    results: List[ChapterText] = []

    for i, ch in enumerate(chapters):
        end_page = chapters[i + 1].start_page if i + 1 < len(chapters) else len(doc)
        text_parts = []

        for p in range(ch.start_page, end_page):
            page_text = doc[p].get_text("text")

            stop_idx = page_text.find("Text copyright")
            if stop_idx != -1:
                text_parts.append(page_text[:stop_idx])
                break

            text_parts.append(page_text)

        text = fix_leading_dropcap_before_heading("\n".join(text_parts).strip())

        results.append(
            ChapterText(
                **ch.__dict__,
                text=text,
            )
        )

    return results


def write_chapters_to_dir(
    chapters: List[ChapterText],
    output_dir: str,
) -> None:
    os.makedirs(output_dir, exist_ok=True)

    for ch in chapters:
        filename = f"{ch.book_index} - {ch.book_title} - {ch.chapter_title}.txt"
        path = os.path.join(output_dir, filename)

        with open(path, "w", encoding="utf-8") as f:
            f.write(ch.chapter_title + "\n\n")
            f.write(ch.text)


if __name__ == "__main__":
    chapters = extract_chapter_texts(
        file_path="data/harrypotter.pdf",
        books_to_skip=3,
    )
    write_chapters_to_dir(chapters, "data/txt")
