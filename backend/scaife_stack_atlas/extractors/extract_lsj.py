import itertools
import json
import re
from functools import lru_cache
from pathlib import Path

import jsonlines
import regex
from betacode.conv import beta_to_uni as beta_to_uni_
from lxml import etree
from more_itertools import peekable

from scaife_viewer.atlas.backports.scaife_viewer.cts.utils import natural_keys


DICTIONARY_PATH = Path("data/annotations/dictionaries/lsj")


# e.g. Hom.</span> </span>, <span class="bibl">
PUNCTUATION_WITH_SPACES = regex.compile(r"[\p{P}]\s[\p{P}](?!\w)+")
# e.g. Pass. ,
HTML_PUNCTUATION_WITH_SPACES = regex.compile(
    r"[\p{P}](\</span>){0,}\s\</span>[\p{P}](?!\w)+"
)

LSJ_BETACODE_MACRON = "_"
LSJ_BETACODE_BREVE = "^"
BETACODE_MACRON = "&"
BETACODE_BREVE = "'"
# FIXME: betacode package has these backwards
MAPPED_BETACODE_MACRON = BETACODE_BREVE
MAPPED_BETACODE_BREVE = BETACODE_MACRON
HYPHEN = "\u2010"
HYPHEN_MINUS = "\u002d"

DEBUG = False
XSL_STYLESHEET_PATH = Path("data/raw/lsj/lsj.xsl")


def get_entry_free_elements(root, nattr=None):
    if nattr:
        return root.xpath(f"//entryFree[@id='{nattr}']")
    return root.xpath("//entryFree")


def beta_to_uni(value):
    # TODO: Upstream fixes for _ and ^ / & '
    to_macron = value.replace(LSJ_BETACODE_MACRON, MAPPED_BETACODE_MACRON)
    to_breve = to_macron.replace(LSJ_BETACODE_BREVE, MAPPED_BETACODE_BREVE)
    # TODO: Sort out hyphen / hyphen minus bits
    return beta_to_uni_(to_breve).replace(HYPHEN, HYPHEN_MINUS)


def to_unicode(element):
    if element.attrib.get("lang") == "greek":
        element.text = beta_to_uni(element.text)


def stringish(element):
    text = (
        etree.tostring(element, with_tail=True, encoding="utf-8", method="text")
        .decode("utf-8")
        .strip()
    )
    # TODO: Revisit excessive whitepace stripping; was a problem on Cunliffe and likely an issue here too
    # TODO: Compare to get_text_from_element
    return " ".join(s.strip() for s in text.split() if s.strip())


def resolvable_urn(urnish):
    """
    Returns a URN resolvable by Beyond Translation
    (e.g., Iliad or Odyssey)
    """
    # FIXME: This should be done / handled within the app at runtime; shortcut
    # for a demo
    if not urnish:
        return ""
    if not urnish.count("tlg0012"):
        return ""
    urnish = urnish.replace("perseus-grc1", "perseus-grc2")
    # TODO: Validate this in case we have other forms of URNs
    version, ref = urnish.rsplit(":", maxsplit=1)
    return f"{version}.{ref}"


def process_citation(c_element, counters):
    # TODO: multiple quotes
    assert c_element.findall("quote")
    assert c_element.findall("bibl")
    quote_parts = []
    for q_elem in c_element.findall("quote"):
        to_unicode(q_elem)
        quote_parts.append(
            etree.tostring(q_elem, with_tail=True, encoding="utf-8", method="text")
            .decode("utf-8")
            .strip()
        )

    quote = " ".join(quote_parts).strip()
    bibl_entries = []
    for b_element in c_element.findall("bibl"):
        # TODO: get creative with XSL or other transforms
        urnish = resolvable_urn(b_element.attrib.get("n", ""))
        bibl_entries.append((stringish(b_element), urnish))
    assert len(bibl_entries) == 1

    counters["citation"] += 1
    return dict(
        urn=f"urn:cite2:scaife-viewer:citations.atlas_v1:lsj-{counters['citation']}",
        data=dict(quote=quote, ref=bibl_entries[0][0], urn=urnish),
    )


def process_sense(s_element, counters):
    label = s_element.attrib.get("n", "")
    definition = []
    citations = []

    for pos, child in enumerate(s_element.getchildren()):
        # TODO: "*[@lang = 'greek']"
        if child.tag in ["orth", "gen", "bibl"]:
            to_unicode(child)
            # TODO: review whitespace here; gets a little tricky
            definition.append(stringish(child))
        if child.tag == "cit":
            citations.append(process_citation(child, counters))

    counters["sense"] += 1
    return dict(
        label=label,
        urn=f"urn:cite2:scaife-viewer:senses.atlas_v1:lsj-{counters['sense']}",
        definition=" ".join(definition),
        citations=citations,
    )


def verbose_append(iterable, element):
    iterable.append(element)
    # print(element)


def get_entries():
    paths_and_nattrs = [
        (
            # ἀείδω
            Path("data/raw/lsj/grc.lsj.perseus-eng1.xml"),
            "n1587",
        ),
        (
            # μῆνις
            Path("data/raw/lsj/grc.lsj.perseus-eng13.xml"),
            "n67485",
        ),
    ]
    entries = []
    counters = dict(
        sense=0,
        entry=0,
        citation=0,
    )
    for path, nattr in paths_and_nattrs:
        root = etree.parse(path.open("rb"))
        elements = get_entry_free_elements(root, nattr)
        processed = []
        senses = []
        for entry in elements:
            for pos, child in enumerate(entry.getchildren()):
                print(pos, child.tag)
                if child.attrib.get("lang") == "greek":
                    to_unicode(child)
                    verbose_append(processed, stringish(child))
                elif child.tag == "gramGrp":
                    for gchild in child.getchildren():
                        verbose_append(processed, stringish(gchild))
                    if child.tail:
                        verbose_append(processed, child.tail.strip())
                elif child.tag == "sense":
                    sense = child
                    senses.append(process_sense(sense, counters))
                else:
                    verbose_append(processed, stringish(child))
        plain_content = " ".join(processed)
        headword = beta_to_uni(entry.attrib.get("key"))

        counters["entry"] += 1
        entries.append(
            dict(
                headword=headword,
                data=dict(content=f"<p>{plain_content}</p>"),
                senses=senses,
                urn=f"urn:cite2:scafife-viewer:dictionary-entries.atlas_v1:lsj-{counters['entry']}",
            )
        )
    return entries


def structural_entries():
    entries = get_entries()

    data = {
        "label": "A Greek-English Lexicon (LSJ)",
        "urn": "urn:cite2:scaife-viewer:dictionaries.v1:lsj",
        "kind": "Dictionary",
        "entries": entries,
    }
    output_path = Path("data/annotations/dictionaries/lsj-sample.json")
    with output_path.open("w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_text_from_element(element):
    element_text = " ".join(element.itertext()).strip()
    # Collapse whitespace
    return re.sub(r"\s+", " ", element_text)


def extract_citations_from_element(element, counters):
    """
    Extracts citations by looking for bibl elements.

    If the bibl has a quote, extracts the quoted text
    as unicode.

    Return type is a list of ATLAS Citations
    - urn
    - data
      - quote
      - ref
      - urn
    """
    citations = []
    for bibl in element.xpath(".//bibl[starts-with(@n, 'urn')]"):
        urn = resolvable_urn(bibl.attrib.get("n"))
        if not urn:
            continue
        citation_text = get_text_from_element(bibl)
        quote = None
        quotes = bibl.xpath("preceding-sibling::quote")
        if quotes:
            quote = quotes[0]
            to_unicode(quote)
            quote = stringish(quote)
        counters["citation"] += 1
        citations.append(
            dict(
                urn=f"urn:cite2:scaife-viewer:citations.atlas_v1:lsj-{counters['citation']}",
                data=dict(quote=quote, ref=citation_text, urn=urn),
            )
        )
    return citations


def extract_atlas_entry(entry, content, counters):
    headword = beta_to_uni(entry.attrib.get("key"))
    counters["entry"] += 1
    senses = []
    return dict(
        headword=headword,
        data=dict(content=content),
        senses=senses,
        citations=extract_citations_from_element(entry, counters),
        urn=f"urn:cite2:scafife-viewer:dictionary-entries.atlas_v1:lsj-{counters['entry']}",
    )


def get_lsj_paths():
    # FIXME: vendor data
    lsj_xml_dir = Path(
        "/Users/jwegner/Data/development/repos/PerseusDL/lexica/CTS_XML_TEI/perseus/pdllex/grc/lsj/"
    )
    return sorted(lsj_xml_dir.glob("*.xml"), key=lambda x: natural_keys(x.name))


def get_lsj_entry_free_elements():
    if DEBUG:
        paths_and_nattrs = [
            (
                # ἀείδω
                Path("data/raw/lsj/grc.lsj.perseus-eng1.xml"),
                "n1587",
            ),
            (
                # μῆνις
                Path("data/raw/lsj/grc.lsj.perseus-eng13.xml"),
                "n67485",
            ),
        ]
    else:
        paths_and_nattrs = [(path, None) for path in get_lsj_paths()]

    for path, nattr in paths_and_nattrs:
        with path.open("rb") as f:
            root = etree.parse(f)
            for element in get_entry_free_elements(root, nattr):
                yield element


class XSLTransformer:
    def __init__(self, xml):
        self.xml = xml

    def beta_to_uni(self, ctx, text_selector):
        # NOTE: compare with https://stackoverflow.com/questions/16031673/get-the-non-empty-element-using-xpath
        if text_selector:
        value = text_selector[0]
        return beta_to_uni(value)

    def catalog_link(self, ctx, value):
        # TODO: Point this to something within Beyond Translation
        node = value[0]
        urn = node.attrib["n"]
        version_urn = urn.rsplit(":", maxsplit=1)[0]
        work_urn = version_urn.rsplit(".", maxsplit=1)[0]
        return f"https://catalog.perseus.org/catalog/{work_urn}/"

    # TODO: Backported from scaife_viewer_core TEIRenderer
    @lru_cache
    def render(self):
        with XSL_STYLESHEET_PATH.open("rb") as f:
            func_ns = "urn:python-funcs"
            transform = etree.XSLT(
                etree.XML(f.read()),
                extensions={
                    (func_ns, "beta_to_uni"): self.beta_to_uni,
                    (func_ns, "catalog_link"): self.catalog_link,
                },
            )
            try:
                return str(transform(self.xml))
            except Exception:
                for error in transform.error_log:
                    print(error.message, error.line)
                raise


def remove_spaces(match_obj):
    return match_obj.group().replace(" ", "")


def fix_whitespace(content):
    return PUNCTUATION_WITH_SPACES.sub(
        remove_spaces, HTML_PUNCTUATION_WITH_SPACES.sub(remove_spaces, content)
    )


def extract_content(entry, debug=False):
    # TODO: Revisit transformer instantiation
    transformer = XSLTransformer(entry)
    content = transformer.render().strip()
    content = " ".join(content.split())
    content = fix_whitespace(content)
    if debug:
        output = Path("data/raw/lsj/output.html")
        with output.open("w") as f:
            f.write(content)
    return content


def extract_entries():
    counters = dict(
        sense=0,
        entry=0,
        citation=0,
    )
    for pos, entry in enumerate(get_lsj_entry_free_elements()):
        debug = DEBUG and pos == 0
        content = extract_content(entry, debug=debug)
        atlas_entry = extract_atlas_entry(entry, content, counters)
        yield atlas_entry


def blob_entries():
    counter = 1
    entries = extract_entries()
    CHUNK_SIZE = 10000
    chunk = peekable(itertools.islice(entries, CHUNK_SIZE))
    entry_paths = []
    while chunk:
        entries_path = Path(DICTIONARY_PATH, f"entries-{str(counter).zfill(3)}.jsonl")
    with entries_path.open("w") as f:
        writer = jsonlines.Writer(f)
            for entry in chunk:
            writer.write(entry)
        entry_paths.append(entries_path.name)
        counter += 1
        chunk = peekable(itertools.islice(entries, CHUNK_SIZE))
        if not chunk:
            break

    data = {
        "label": "A Greek-English Lexicon (LSJ)",
        "urn": "urn:cite2:scaife-viewer:dictionaries.v1:lsj",
        "kind": "Dictionary",
        "entries": entry_paths,
    }
    metadata_path = Path(DICTIONARY_PATH, "metadata.json")
    with metadata_path.open("w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    DICTIONARY_PATH.mkdir(exist_ok=True, parents=True)
    blob_entries()


if __name__ == "__main__":
    main()
