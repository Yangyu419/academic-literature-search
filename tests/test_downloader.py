from pathlib import Path

from literature_finder.downloader import filename_for, parse_selection
from literature_finder.models import LiteratureRecord


def test_parse_selection_ranges():
    assert parse_selection("1, 3, 8-10", 12) == {1, 3, 8, 9, 10}


def test_filename_is_safe_and_bounded():
    record = LiteratureRecord('A / title: with * unsafe?', authors=["Jane Doe"], publication_date="2024-10")
    filename = filename_for(1, record)
    assert filename.startswith("001_Doe_2024_")
    assert not any(character in filename for character in '/\\:*?"<>|')
    assert filename.endswith(".pdf")

