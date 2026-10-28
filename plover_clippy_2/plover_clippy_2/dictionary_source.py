import os

_DELETED = "{plover:deleted}"


def outline_of(translation):
    rtfcre = translation.rtfcre
    if isinstance(rtfcre, str):
        return tuple(part for part in rtfcre.split("/") if part)
    return tuple(rtfcre)


def _matches(engine, outline):
    lookup = getattr(engine, "lookup_from_all", None)
    if lookup is not None:
        return lookup(outline) or []

    collection = getattr(engine, "dictionaries", None)
    if collection is None:
        return []
    matches = []
    for dictionary in collection.dicts:
        if not getattr(dictionary, "enabled", True):
            continue
        value = dictionary.get(outline)
        if value:
            matches.append((value, dictionary))
    return matches


def dictionary_name(dictionary):
    path = getattr(dictionary, "path", None) or ""
    return os.path.basename(str(path).replace("\\", "/"))


def dictionary_for_translation(engine, translation):
    outline = outline_of(translation)
    if not outline:
        return ""
    matches = _matches(engine, outline)
    if not matches:
        return ""
    text, dictionary = matches[0]
    if text is None or str(text).lower() == _DELETED:
        return ""
    return dictionary_name(dictionary)


def dictionaries_for_phrase(engine, phrase):
    names = []
    for translation in phrase:
        name = dictionary_for_translation(engine, translation)
        if name and (not names or names[-1] != name):
            names.append(name)
    return ", ".join(names)


def dictionary_suffix(name):
    if not name:
        return ""
    return f" ({name})"
