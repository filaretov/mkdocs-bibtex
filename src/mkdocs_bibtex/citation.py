from dataclasses import dataclass
import re

# Here's how the correct syntax for valid citation keys was derived:
# 1. According to these StackExchange posts:
# https://tex.stackexchange.com/questions/408530/what-characters-are-allowed-to-use-as-delimiters-for-bibtex-keys
# https://tex.stackexchange.com/questions/96454/using-bibtex-keys-containing-parentheses-with-biber/96918#96918
# the following punctuation symbols are DISALLOWED:
# "#'(),={}%~\

# 2. Pandoc specifies the following rules:
# https://pandoc.org/MANUAL.html#citation-syntax
# Which imply that punctuation except for underscore can not be repeated in
# keys.
# It also defines the following set of ALLOWED punctuation characters:
# :.#$%&-+?<>~/
# However, experimentatin with pandoc suggests that the following characters
# are always DISALLOWED:
# #%<>~ ^!|
# Admittedly, the final three were not on the original list of allowed characters.
#
# Finally, pandoc also requires that the key start with an alphanumeric symbol or underscore,
# and that the allowed punctuation characters do NOT appear as the first or final symbol in a key,
# and that the allowed punctuation characters only appear in groups of one.
# This leads to the following regex for citation keys which should be accepted by all
# systems used by mkdocs-bibtex:
# r"@(?P<key>[\w0-9_]([:.$&+?/-]?[\w0-9_]+)*)"


CITATION_REGEX = re.compile(
    r"(?:(?P<prefix>[^@;]*?)\s*)?"
    r"@(?P<key>[\w0-9_]([:.$&+?/-]?[\w0-9_]+)*)"
    r"(?:,\s*(?P<suffix>[^;]+))?"
)
CITATION_BLOCK_REGEX = re.compile(r"\[(.*?)\]")
EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
INLINE_REFERENCE_REGEX = re.compile(r"(?<![\[\w])@(?P<key>[\w0-9_]([:.$&+?/-]?[\w0-9_]+)*)(?![\w\s]*\])")


@dataclass
class Citation:
    """Represents a citation in raw markdown without formatting"""

    key: str
    prefix: str = ""
    suffix: str = ""

    def __str__(self) -> str:
        """String representation of the citation"""
        parts = []
        if self.prefix:
            parts.append(self.prefix)
        parts.append(f"@{self.key}")
        if self.suffix:
            parts.append(self.suffix)
        return " ".join(parts)

    @classmethod
    def from_markdown(cls, markdown: str) -> list["Citation"]:
        """Extracts citations from a markdown string"""
        citations = []

        pos_citations = markdown.split(";")
        pos_citations = [citation for citation in pos_citations if EMAIL_REGEX.match(citation) is None]

        for citation in pos_citations:
            match = CITATION_REGEX.fullmatch(citation)

            if match:
                result = {group: (match.group(group) or "") for group in ["prefix", "key", "suffix"]}
                citations.append(Citation(prefix=result["prefix"], key=result["key"], suffix=result["suffix"]))
        return citations


@dataclass
class CitationBlock:
    citations: list[Citation]
    raw: str = ""

    def __str__(self) -> str:
        """String representation of the citation block"""
        if self.raw != "":
            return f"[{self.raw}]"
        return "[" + "; ".join(str(citation) for citation in self.citations) + "]"

    @classmethod
    def from_markdown(cls, markdown: str) -> list["CitationBlock"]:
        """Extracts citation blocks from a markdown string"""
        """
        Given a markdown string
        1. Find all cite blocks by looking for square brackets
        2. For each cite block, try to extract the citations
            - if this errors there are no citations in this block and we move on
            - if this succeeds we have a list of citations
        """
        citation_blocks = []
        for match in CITATION_BLOCK_REGEX.finditer(markdown):
            try:
                citations = Citation.from_markdown(match.group(1))
                if len(citations) > 0:
                    citation_blocks.append(CitationBlock(raw=match.group(1), citations=citations))
            except Exception as e:
                print(f"Error extracting citations from block: {e}")
        return citation_blocks


@dataclass
class InlineReference:
    key: str

    def __str__(self) -> str:
        return f"@{self.key}"

    def __hash__(self) -> int:
        return hash(self.key)

    @classmethod
    def from_markdown(cls, markdown: str) -> list["InlineReference"]:
        """Finds inline references in the markdown text. Only use this after processing all regular citations"""
        inline_references = [
            InlineReference(key=match.group("key")) for match in INLINE_REFERENCE_REGEX.finditer(markdown) if match
        ]

        return inline_references
