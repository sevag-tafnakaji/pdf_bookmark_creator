import argparse
from typing import Tuple, List

from pypdf import PdfReader, PdfWriter


# TODO: Determine if this is valid for all or a majority of PDFs
def check_valid(text: str):

    return len(text) != 0 and text[0].isdigit()


def combine_next_line_text(text1: str, text2: str):
    new_text = ""
    # text1 = text1[:-1]  # remove \r
    if text1[-1] == "-":
        text1 = text1[:-1]  # remove hyphen

        new_text = text1 + text2
    else:
        new_text = text1 + " " + text2

    return new_text


# TODO: Determine if this is valid for all or a majority of PDFs
def filter_name(text: str) -> Tuple[str, str, int]:
    """
    Assume that text is chapter name

    Args:
        text (str): _description_
    """
    # text = text[:-1]  # remove \r

    text_list: List[str] = text.split(' ')

    chapter_num, chapter_name, page_number = \
        text_list[0], ' '.join(text_list[1:-1]), int(text_list[-1])

    return (chapter_num, chapter_name, page_number)


def filter_names(texts: List[str]) -> List[Tuple[str, str, int]]:
    filtered_texts = []
    for text_idx, text in enumerate(texts):
        if check_valid(text):
            next_text = texts[text_idx + 1] if text_idx < (len(texts) - 2) else None

            # in case next_text is the page number in roman numerals
            next_text = next_text if next_text and len(next_text) > 4 else None

            if next_text and not next_text[0].isdigit():
                text = combine_next_line_text(text, next_text)

            filtered_texts.append(filter_name(text))

    return filtered_texts


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="PDF Bookmark Adder",
        description="Add bookmarks to your desired PDF"
    )

    parser.add_argument("-f", "--filepath", required=True, help="Path to PDF")
    parser.add_argument("-b", "--begin", required=True, type=int,
                        help="Page index where table of contents starts (index = page number - 1)")
    parser.add_argument("-e", "--end", required=True, type=int,
                        help="Page index where table of contents ends (index = page number - 1)")
    parser.add_argument("-o", "--offset", required=True, type=int,
                        help="Offset between beginning of the book and actual page number "
                             "(offset = page number - 1)")

    args = parser.parse_args()

    file_path: str = args.filepath

    file_name = file_path.split("\\")[-1]

    reader = PdfReader(file_path)

    file_path = file_path.split("\\")[:-1]

    writer = PdfWriter()

    first_toc_page_idx = args.begin
    last_toc_page_idx = args.end
    page_offset = args.offset

    # TODO: Add logic for depth of chapters to be set by user (depends on count of . IG?)
    current_parent = None
    current_sub_parent = None

    # Add all pages to writer
    for page in reader.pages:
        writer.add_page(page)

    # Go through Table of Contents to add bookmarks
    for page_idx in range(first_toc_page_idx, last_toc_page_idx + 1):
        page_contents = reader.pages[page_idx].extract_text()
        split_page_contents = page_contents.split("\n")
        if split_page_contents == ['']:
            print("Page empty!")
            continue
        filtered_bookmark_infos = filter_names(split_page_contents)

        for bookmark_info_idx, bookmark_info in enumerate(filtered_bookmark_infos):
            current_bookmark = None
            # initialising
            if current_parent is None:
                current_bookmark = writer.add_outline_item(
                    title=bookmark_info[0] + " " + bookmark_info[1],
                    page_number=bookmark_info[2] + page_offset - 1
                )
                current_parent = current_bookmark
            # New chapter/parent, update pointer to parent
            elif bookmark_info[0].count(".") == 0:
                current_bookmark = writer.add_outline_item(
                    title=bookmark_info[0] + " " + bookmark_info[1],
                    page_number=bookmark_info[2] + page_offset - 1
                )
                current_parent = current_bookmark
            # new sub-chapter/sub-parent, update pointer to sub-parent
            elif bookmark_info[0].count(".") == 1:
                current_bookmark = writer.add_outline_item(
                    title=bookmark_info[0] + " " + bookmark_info[1],
                    page_number=bookmark_info[2] + page_offset - 1,
                    parent=current_parent
                )
                current_sub_parent = current_bookmark
            # new sub-sub-chapter
            elif bookmark_info[0].count(".") == 2:
                current_bookmark = writer.add_outline_item(
                    title=bookmark_info[0] + " " + bookmark_info[1],
                    page_number=bookmark_info[2] + page_offset - 1,
                    parent=current_sub_parent
                )

    output_file = "\\".join(file_path) + "\\With Bookmarks - " + file_name
    writer.write(output_file)
