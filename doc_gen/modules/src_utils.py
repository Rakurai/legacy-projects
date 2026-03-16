from pathlib import Path
from functools import cache
from typing import List, Set, Dict, Tuple

@cache
def extract_lines(file_path: Path, start: int, end: int) -> str:
    code = ""
    if end == -1:
        end = start

    try:
        with open(file_path) as f:
            lines = f.readlines()
        code = "".join(lines[start - 1:end])
    except Exception as e:
        raise Exception(f"[!] Failed to extract lines from {file_path}: {e}")
    return code


def extract_comment_blocks(compounds: Dict[str, Dict[str, str]], members: Dict[str, Dict[str, str]], source_dir: Path = None):
    """Second pass: extract documentation and update node attributes for all members."""
    # Build an index mapping (filename, lineno) -> node id
    location_index = {}
    for node_id, data in g.nodes(data=True):
        for field, attr in [
            ("comment_decl", ("declfile", "declline")),
            ("comment_body", ("bodyfile", "bodystart")),
            ("comment_usage", ("file", "line")),
        ]:
            g.nodes[node_id].update({field: ""})
            filename = data.get(attr[0])
            if filename == '[generated]':
                continue
            lineno = data.get(attr[1])
            if filename and len(filename) and isinstance(lineno, int) and lineno >= 0:
                key = (filename, lineno)
                if key in location_index:
                    continue
#                    log.warning(f"Ambiguous location index for {key}: {location_index[key]} vs {(node_id, field)}")
                location_index[key] = (node_id, field)

    # For each file, collect all line numbers from nodes in the graph
    file_to_lines = {}
    for filename, lineno in location_index.keys():
        file_to_lines.setdefault(filename, set()).add(lineno)

    for filename, line_numbers in file_to_lines.items():
        path = source_dir / filename
        preceding_comments = extract_preceding_comments_from_source_file(path, sorted(line_numbers))

        # map back to nodes
        for ln, (comment, section) in preceding_comments.items():
            node_id, field = location_index.get((filename, ln))
            # print(f"{node_id} - {g.nodes[node_id].get('kind')} - {g.nodes[node_id].get('name')} - {field} in {filename}:{ln}")
            # for field, attr in [
            #     ("comment_decl", ("declfile", "declline")),
            #     ("comment_body", ("bodyfile", "bodystart")),
            #     ("comment_usage", ("file", "line")),
            # ]:
            #     print(f"{attr[0]}: {g.nodes[node_id].get(attr[0])}")
            #     print(f"{attr[1]}: {g.nodes[node_id].get(attr[1])}")

            # print(f"SECTION:\n{section}")
            # print(f"COMMENT:\n{comment}")
            # print('---------------------------------------------------------')
            g.nodes[node_id].update({
                field: comment.strip()
            })

def extract_preceding_comments_from_source_file(path: Path, line_numbers: List[int]):
    """
    For each line number in line_numbers, extract the preceding comment block from the source file.
    Uses strict rules:
      - For block comments: right-stripped line endswith '*/', keep adding lines until left-stripped line startswith '/*'.
      - For line comments: left-stripped line startswith '//', add the line.
      - Blank lines are included.
      - Stop at first code line.
    Returns a dict mapping line_number -> comment string.
    """

    def read_block_comment(text, level=1) -> int:
        index = text.rfind('*/')
        while index >= 0:
            if text[:index].endswith('*/'):
                index = read_block_comment(text[:index], level+1)
            elif text[index:].startswith('/*'):
                return index
            index -= 1
        raise Exception("Unmatched block comment")

    def extract_preceding_comment_from_section(section: str):
        comment = ""

        while section.strip() != "":
            if section.rstrip().endswith('*/'):
#                print(f"section:\n{section}")
#                print(f"comment:\n{comment}")
                index = read_block_comment(section)
                section, block = section[:index], section[index:]
                # make sure we didn't find a comment on the same line as code
                test_line = section.rsplit('\n', 1)[1] if '\n' in section else section
                if test_line.strip() != '':
                    break
                comment = block + comment # prepend
                continue

            if '\n' in section:
                section, line = section.rsplit('\n', 1)
            else:
                line = section
                section = ""
            # only line comments and blank lines
            if line.lstrip().startswith('//') or line.strip() == '':
                comment = line + '\n' + comment
                continue

            # Found a code line, stop searching
            break

        return comment

    results = {}
    with open(path, encoding="utf-8") as f:
        lines = [line.rstrip() for line in f.readlines()]

    # break the file text into len(line_numbers)+1 chunks so we can parse without breaks

    section_spans = list(zip([1] + line_numbers[:-1], line_numbers)) # 1-indexed spans including the reference line
#    print('line nubmers:', line_numbers)
#    print('section_spans:', section_spans)
    sections = {ln: lines[start-1:ln-1] for (start, ln) in section_spans} # 0-indexed spans excluding reference line
#    print('sections:', sections)
    sections = {ln: '\n'.join(sec) for ln, sec in sections.items() if len(sec) > 0}
#    print('sections 2:', sections)

    for ln, section in sections.items():
        # Extract comments from the section
#        print(f"{ln}: SECTION:\n{section}")
        try:
            comment = extract_preceding_comment_from_section(section)
        except Exception as e:
            print(f"Error extracting comment from {path}:{ln}: {e}")
        results[ln] = (comment, section)

    return results

def generate_doxygen_docs():
    import xml.etree.ElementTree as ET

    DOCS_DIR = OUTPUT_DIR
    DOX_DIR.mkdir(parents=True, exist_ok=True)

    def extract_signature(member, compound=False):
        kind = member.attrib.get("kind")
        name = member.findtext("compoundname" if compound else "name", "").strip()
        definition = member.findtext("definition", "").strip()
        argsstring = member.findtext("argsstring", "").strip()
        return kind, name, definition, argsstring

    for json_file in DOCS_DIR.glob("*.json"):
        compound_id = json_file.stem

        with open(json_file) as f:
            docdata = json.load(f)

        xml_path = XML_DIR / f"{compound_id}.xml"
        if not xml_path.exists():
            raise FileNotFoundError(f"XML file not found: {xml_path}")
        tree = ET.parse(xml_path)
        root = tree.getroot()

        lines = []
        signatures = {
            compound_id: extract_signature(root.find(".//compounddef"), compound=True)
        }
        for member in root.findall(".//memberdef"):
            member_id = member.attrib.get("id")
            signatures[member_id] = extract_signature(member)

        for member_id, entry in docdata.items():
            if member_id not in signatures:
                print(f"[!] member_id not found in signatures: {member_id}")
                continue

            kind, name, definition, argsstring = signatures[member_id]

            response = entry.get("response", {})
            brief = response.get("brief", "").strip()
            details = response.get("details", "").strip()
            params = response.get("params", {})
            returns = response.get("return", "")
            throws = response.get("throws", "")

            lines.append("/**")
            if kind == "function":
                lines.append(f" * @fn {definition}{argsstring}")
            elif kind == "variable":
                lines.append(f" * @var {name}")
            elif kind == "enum":
                lines.append(f" * @enum {name}")
            elif kind == "typedef":
                lines.append(f" * @typedef {name}")
            elif kind == "define":
                lines.append(f" * @def {name}")
            elif kind == "friend":
                lines.append(f" * @fn {definition}{argsstring} // friend")
            elif kind == "group":
                lines.append(f" * @defgroup {name} {name.title()} Group")
            elif kind == "namespace":
                lines.append(f" * @namespace {name}")
            elif kind in ("class", "struct"):
                lines.append(f" * @{kind} {name}")
            else:
                lines.append(f" * @note Unhandled kind: {kind}")

            if brief:
                lines.append(f" * @brief {brief}")
            if details:
                lines.append(f" * @details {details}")
            for p, desc in params.items():
                lines.append(f" * @param {p} {desc}")
            if returns and returns.lower() != "void":
                lines.append(f" * @return {returns}")
            if throws and throws != "null":
                lines.append(f" * @throws {throws}")
            lines.append(" */\n")

        dox_path = DOX_DIR / (json_file.stem + ".dox")
        dox_path.write_text("\n".join(lines))

    print(f"[✓] Generated .dox files in {DOX_DIR}")
