import pytest
from app.services.git_service import filter_reviewable_files
from app.services.review_service import prepare_review_files, ReviewFile

def test_filter_reviewable_files():
    # Test that supported extensions are allowed
    files = ["main.py", "index.ts", "Dockerfile", "configs/base.yaml"]
    filtered = filter_reviewable_files(files)
    assert len(filtered) == 4
    assert "main.py" in filtered

    # Test that ignored files are filtered out
    files_with_ignored = ["main.py", "package-lock.json", "poetry.lock", "app.min.js"]
    filtered = filter_reviewable_files(files_with_ignored)
    assert len(filtered) == 1
    assert "main.py" in filtered
    assert "package-lock.json" not in filtered
    assert "poetry.lock" not in filtered
    assert "app.min.js" not in filtered

def test_prepare_review_files_size_limits():
    # Under limit
    file_diffs = [
        {"path": "small.py", "patch": "print('hello')\n" * 10}
    ]
    review_files = prepare_review_files(file_diffs)
    assert len(review_files) == 1
    assert review_files[0].path == "small.py"

    # Exceeding character length limit
    large_char_diffs = [
        {"path": "large_char.py", "patch": "a" * 1000}
    ]
    review_files = prepare_review_files(large_char_diffs, max_patch_length=500)
    assert len(review_files) == 0

    # Exceeding line limit
    large_line_diffs = [
        {"path": "large_lines.py", "patch": "line\n" * 100}
    ]
    review_files = prepare_review_files(large_line_diffs, max_patch_lines=50)
    assert len(review_files) == 0
