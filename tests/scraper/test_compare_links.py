from src.scraper.compare_links import mark_new_links

def test_mark_new_links_first_time():
    new_links = [
        {"civico_id": "gamonal_norte", "filename": "a.pdf", "url": "u1"}
    ]
    result = mark_new_links([], new_links)

    assert result[0]["is_new"] is True

def test_mark_existing_links():
    old_links = [
        {"civico_id": "gamonal_norte", "filename": "a.pdf", "url": "u1"}
    ]
    new_links = [
        {"civico_id": "gamonal_norte", "filename": "a.pdf", "url": "u1"}
    ]

    result = mark_new_links(old_links, new_links)

    assert result[0]["is_new"] is False

def test_mark_mixed_links():
    old_links = [
        {"civico_id": "gamonal_norte", "filename": "a.pdf", "url": "u1"}
    ]
    new_links = [
        {"civico_id": "gamonal_norte", "filename": "a.pdf", "url": "u1"},
        {"civico_id": "capiscol", "filename": "b.pdf", "url": "u2"},
    ]

    result = mark_new_links(old_links, new_links)

    assert result[0]["is_new"] is False
    assert result[1]["is_new"] is True
