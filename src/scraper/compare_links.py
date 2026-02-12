def link_key(link: dict) -> tuple:
    return (
        link["civico_id"],
        link["filename"],
        link["url"],
    )


def mark_new_links(old_links: list[dict], new_links: list[dict]) -> list[dict]:
    old_keys = {link_key(l) for l in old_links}

    result = []
    for link in new_links:
        key = link_key(link)
        link = dict(link)  # copia defensiva
        link["is_new"] = key not in old_keys
        result.append(link)

    return result
