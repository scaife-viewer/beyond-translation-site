def deep_morphology_human_parse(parse):
    if len(parse) == 8:
        if parse == "--------":
            return "INDECL"
        else:
            person = {
                "-": None,
            }.get(parse[0], parse[0])
            number = {
                "s": "SG",
                "d": "DU",
                "p": "PL",
                "-": None,
            }.get(parse[1], parse[1])
            tense = {
                "p": "PRES",
                "i": "IMPRF",
                "f": "FUT",
                "a": "AOR",
                "r": "PRF",
                "l": "PLPRF",
                "-": None,
            }.get(parse[2], parse[2])
            mood = {
                "i": "IND",
                "m": "IMP",
                "n": "INF",
                "s": "SBJV",
                "o": "OPT",
                "p": "PTCP",
                "-": None,
            }.get(parse[3], parse[3])
            voice = {
                "a": "ACT",
                "m": "MID",
                "e": "MID",
                "p": "PASS",
            }.get(parse[4], parse[4])
            gender = {
                "m": "M",
                "f": "F",
                "n": "N",
                "-": None,
            }.get(parse[5], parse[5])
            case = {
                "n": "NOM",
                "a": "ACC",
                "g": "GEN",
                "d": "DAT",
                "v": "VOC",
                "-": None,
            }.get(parse[6], parse[6])
            degree = {
                "c": "COMP",
                "s": "SUP",
                "-": None,
            }.get(parse[7], parse[7])
            if case and tense:
                if mood != "PTCP":
                    return f"@1@ {parse}"
                return f"{tense} {voice} {case}.{number} {gender} {mood}"
            elif case and not tense:
                if degree:
                    return f"{case}.{number} {gender} {degree}"
                if gender:
                    return f"{case}.{number} {gender}"
                else:
                    return f"{case}.{number}"
            elif tense and not case:
                if person:
                    return f"{tense} {voice} {person}{number} {mood}"
                elif mood == "INF":
                    return f"{tense} {voice} {mood}"
                else:
                    return f"@@@ {parse}"
            else:
                return f"@@@ {parse}"
    else:
        return "UNKNOWN"


def deep_morphology_human_pos(pos):
    return {
        "a-": "ADJ",
        "ae": "PROP.ADJ",
        "c-": "CONJ",
        "d-": "ADV",
        "dd": "ADV?",
        "de": "ADV?",
        "di": "ADV?",
        "dr": "ADV?",
        "dx": "ADV?",
        "g-": "PTCL",
        "gm": "MODAL.PTCL",
        "i-": "INTJ",
        "l-": "ART",
        "m-": "NUM",
        "n-": "NOUN",
        "ne": "PROP.NOUN",
        "p-": "PRONOUN",
        "pa": "PRONOUN?",
        "pc": "PRONOUN?",
        "pd": "PRONOUN?",
        "pi": "PRONOUN?",
        "pp": "PRONOUN?",
        "pr": "PRONOUN?",
        "ps": "PRONOUN?",
        "px": "PRONOUN?",
        "r-": "PREP",
        "u-": "PUNC",
        "v-": "VERB",
        "vc": "COPULA",
    }.get(pos, pos)


def deep_morphology_pos_and_parse(postag):
    # NOTE: Deep morphology assumed use of a
    # ten position tag, and split pos from parse
    if len(postag) != 10:
        postag = postag[0] + "-" + postag[1:]
    pos = deep_morphology_human_pos(postag[0:2])
    parse = deep_morphology_human_parse(postag[2:])
    return pos, parse
