#!/usr/bin/env python3

import argparse
import os
import json
from sqlite3 import Cursor
import networkx as nx
from clang import cindex
from pathlib import Path
from clang.cindex import CursorKind
import sys

# Set libclang path (adjust if needed)
cindex.Config.set_library_file("/opt/local/libexec/llvm-20/lib/libclang.dylib")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
COMPILE_COMMANDS = PROJECT_ROOT / "src/compile_commands.json"
GRAPH_OUTPUT = PROJECT_ROOT / ".ai/context/internal/clang_call_graph.json"
SOURCE_DIRS = (
    PROJECT_ROOT / "src",
)

log_level = "info"

def log(indent, message, min_level="info"):
    if min_level == 'none':
        return
    if min_level == "debug" and log_level != "debug":
        return
    print(f"{min_level.upper():<5}: {'  '*indent}{message}")

# Load compilation database
with open(COMPILE_COMMANDS) as f:
    compile_commands = json.load(f)

compile_map = {}
for entry in compile_commands:
    file_path = Path(entry["file"]).resolve()
    args = entry["arguments"][1:-1]
    if "-o" in args:
        i = args.index("-o")
        del args[i:i+2]
    if "-c" in args:
        args.remove("-c")
    compile_map[file_path] = (entry["directory"], args)

call_graph = nx.DiGraph()


debug_calls_from_to = {}
macro_instantiations = {}

def get_qualified_name(cursor):
    if not cursor:
        return "<unknown>"
    parts = []
    while cursor and cursor.kind != CursorKind.TRANSLATION_UNIT:
        name = cursor.spelling or cursor.displayname or str(cursor.kind)
        if name:
            parts.append(name)
        cursor = cursor.semantic_parent
    return "::".join(reversed(parts))
def in_source_dir(file_path: Path):
    return any(file_path.is_relative_to(dir) for dir in SOURCE_DIRS)

def get_file_path(cursor):
    if cursor.location.file:
        return Path(cursor.location.file.name).resolve()
    return None

def add_node(func_name, file_path, start_line, end_line):
    call_graph.add_node(func_name, file=str(file_path), line=start_line, end_line=end_line)

def add_edge(from_func, to_func):
    call_graph.add_edge(from_func, to_func)
    debug_calls_from_to.setdefault(from_func, []).append(to_func)

def visit(cursor, current_entity=None, indent=0):
    file_path = get_file_path(cursor)

    log(indent, f"Visiting: {cursor.kind} - {cursor.spelling}", 'debug')

    if file_path and not in_source_dir(file_path):
        log(indent, f"Skipping external file: {cursor.kind} - {cursor.spelling}", 'none')
        return

    elif cursor.kind in (
        CursorKind.MACRO_DEFINITION,
        CursorKind.FUNCTION_TEMPLATE, # this is the declaration, actually more useful than the multiple definitions
    ):
        if file_path:
            log(indent, f"Found macro definition: {cursor.kind} - {cursor.spelling}", 'debug')
            add_node(
                get_qualified_name(cursor),
                file_path,
                cursor.extent.start.line,
                cursor.extent.end.line,
            )
        else:
            log(indent, f"Skipping global macro definition: {cursor.kind} - {cursor.spelling}", 'debug')
            pass

        # skip processing the body of a template function or macro
        return

#    if cursor.is_definition():
    elif cursor.kind in (
#        CursorKind.FUNCTION_DECL,
        CursorKind.CXX_METHOD,
        CursorKind.CONSTRUCTOR,
        CursorKind.DESTRUCTOR,
    ):
        log(indent, f"Found function definition: {cursor.kind} - {cursor.spelling}")
        name = get_qualified_name(cursor)
        current_entity = name
        add_node(
            name,
            file_path,
            cursor.extent.start.line,
            cursor.extent.end.line
        )

    elif cursor.kind in (
        CursorKind.CLASS_DECL,
    ):
        log(indent, f"Found class definition: {cursor.kind} - {cursor.spelling}")
        name = get_qualified_name(cursor)
        current_entity = name
        add_node(
            name,
            file_path,
            cursor.extent.start.line,
            cursor.extent.end.line
        )

    ### cursors that will have a calling_func
#    elif CursorKind.is_reference(cursor.kind):
    elif cursor.kind in (
        CursorKind.CALL_EXPR,
#        CursorKind.MACRO_INSTANTIATION,
#        CursorKind.CXX_METHOD_CALL,
#        CursorKind.MEMBER_REF_EXPR
    ):
        # Add debugging to see what's being captured
        log(indent, f"Found call: {cursor.kind} - {cursor.spelling}")
        callee = cursor.referenced
        callee_name = get_qualified_name(callee) if callee else cursor.spelling
        if current_entity and callee_name:
            if callee.kind == CursorKind.FUNCTION_TEMPLATE:
                log(indent, f"Found function template: {callee.kind} - {callee.spelling}")
            add_edge(current_entity, callee_name)

    elif cursor.kind in (
        CursorKind.MACRO_INSTANTIATION,
    ):
        # Add debugging to see what's being captured
        log(indent, f"Found macro call: {cursor.kind} - {cursor.spelling}, {get_qualified_name(cursor.referenced)}, called from {current_entity}", 'debug')
        log(indent, f"  file: {cursor.location.file}, lines: {cursor.extent.start.line}-{cursor.extent.end.line}", 'debug')
        log(indent, f"  tokens: {[str(t.spelling) for t in cursor.get_tokens()]}", 'debug')
        log(indent, f"  tokens: {[str(t.spelling) for t in cursor.referenced.get_tokens()]}", 'debug')

        # we can't figure out what function the macro call is within here, so we store the
        # calls by location and then resolve them later by searching the function line ranges
        if cursor.location.file:
            # Store macro instantiation with location info
            location_key = f"{get_file_path(cursor)}:{cursor.extent.start.line}"
            # a line of code could have multiple macro instantiations
            macro_instantiations.setdefault(cursor.spelling, []).append(location_key)
        else:
            pass # some compiler flags come up as macro instantiation but they don't have a file

    ### things that look like a forward declaration, we assume they will resolve later
    # i think this is the end of the line for these calls, no info on implementation, 
    # hopefully we have a calling_func set
    # we can maybe dedup this with macro instantiations, check later
    elif cursor.kind in (
        CursorKind.OVERLOADED_DECL_REF,
    ):
        if not current_entity:
            log(indent, f"forward declaration without current entity: cursor.kind={cursor.kind}, cursor.spelling={cursor.spelling}, cursor.location={cursor.location}")
            # probably a template method, we'll map it by location and name like a macro
            location_key = f"{get_file_path(cursor)}:{cursor.extent.start.line}"
            macro_instantiations.setdefault(cursor.spelling, []).append(location_key)
        else:
            log(indent, f"Found forward declaration: {cursor.kind} - {cursor.spelling}")
            call_graph.add_edge(current_entity, get_qualified_name(cursor))
            debug_calls_from_to.setdefault(current_entity, []).append(get_qualified_name(cursor))


    elif cursor.kind in (
        CursorKind.INCLUSION_DIRECTIVE,
        CursorKind.PARM_DECL,
        CursorKind.UNARY_OPERATOR,
#        CursorKind.DECL_REF_EXPR,
#        CursorKind.UNEXPOSED_EXPR,
#        CursorKind.COMPOUND_STMT,
        # CursorKind.CALL_EXPR - Location,
        # CursorKind.MEMBER_REF_EXPR - vnum,
        # CursorKind.MEMBER_REF_EXPR - count,

    ):
        log(indent, f"Found blacklist directive: {cursor.kind} - {cursor.spelling} - {cursor.location.file} ({cursor.extent.start.line}-{cursor.extent.end.line})", 'debug')
        pass

    else:
        log(indent, f"Found other: {cursor.kind} - {cursor.spelling} - {cursor.location.file} ({cursor.extent.start.line}-{cursor.extent.end.line})")


    # # resolve macro instantiations
    # if cursor.kind in (
    #     CursorKind.FUNCTION_DECL,
    #     CursorKind.TYPEDEF_DECL,
    #     CursorKind.VAR_DECL
    # ):
    #     if cursor.location.file:
    #         location_key = f"{get_file_path(cursor)}:{cursor.extent.start.line}"
    #         for macro_name in macro_instantiations.get(location_key, []):
    #             print(f"Found relation: {cursor.spelling} uses macro {macro_name}")
    #             # Add edge from declaration to macro
    #             add_edge(get_qualified_name(cursor), macro_name)


    for child in cursor.get_children():
        visit(child, current_entity, indent + 1)

def main(args):
    print("[+] Parsing source files and building call graph...")

    # extra_includes = [
    #     "-isysroot", "/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX.sdk",
    #     "-isystem", "/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/lib/clang/15.0.0/include",
    #     "-isystem", "/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX.sdk/usr/include",
    #     "-isystem", "/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/include",
    #     "-stdlib=libc++"
    # ]
    extra_includes = [
        "-isysroot", "/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX.sdk",
        "-isystem", "/opt/local/libexec/llvm-20/include/c++/v1",
        "-isystem", "/opt/local/libexec/llvm-20/lib/clang/20/include",
        "-I", str(PROJECT_ROOT / "src/include"),  # Add your project's include directory
        "-stdlib=libc++"
    ]

    index = cindex.Index.create()
    # for file_path, (working_dir, args) in compile_map.items():
    #     try:
    #         options = cindex.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD | cindex.TranslationUnit.PARSE_INCOMPLETE
    #         tu = index.parse(str(file_path), args=args + extra_includes, options=options)
    #         print(f"Parsed: {file_path.name}")
    #         for child in tu.cursor.get_children():
    #             visit(child)
    #         break # breaking early to just test parsing the first file - Room.cc
    #     except Exception as e:
    #         print(f"[!] Failed to parse {file_path.name}: {e}")
    for file_path, (working_dir, args) in compile_map.items():
        options = cindex.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD | cindex.TranslationUnit.PARSE_INCOMPLETE
        tu = index.parse(str(file_path), args=args + extra_includes, options=options)
        print(f"Parsed: {file_path.name}")
        
        # Print diagnostics to help debug parsing issues
        # if tu.diagnostics:
        #     print(f"Diagnostics for {file_path.name}:")
        #     for diag in tu.diagnostics:  # Show first 5 diagnostics
        #         print(f"  {diag.spelling}")

        visit(tu.cursor)

        # Use walk_preorder instead of get_children
        # for cursor in tu.cursor.walk_preorder():
        #     if cursor.location.file and str(file_path) in str(cursor.location.file.name):
        #         # Only process cursors from this file
        #         visit(cursor)

        # Get N from sys.argv, default to None (process all files)
        if not hasattr(visit, "_file_counter"):
            try:
                N = int(sys.argv[1])
            except (IndexError, ValueError):
                N = None
            visit._file_counter = 0
            visit._max_files = N

        visit._file_counter += 1
        if visit._max_files and visit._file_counter >= visit._max_files:
            break

    function_ranges = {}
    for label, attrs in call_graph.nodes(data=True):
        if 'line' in attrs and 'end_line' in attrs and 'file' in attrs:
            function_ranges.setdefault(attrs['file'], []).append((attrs['line'], attrs['end_line'], label))

    function_ranges = {file: sorted(ranges, key=lambda x: (x[0], x[1])) for file, ranges in function_ranges.items()}

    with open(PROJECT_ROOT / '.ai/context/internal/function_ranges.json', 'w') as f:
        json.dump(function_ranges, f, indent=2)


    for macro_name, loc_keys in macro_instantiations.items():
        for loc_key in loc_keys:
            file_path, line_num = loc_key.rsplit(':', 1)
            line_num = int(line_num)

            # Find which function contains this line.  there could be overlapping ranges
            # if we have namespaces, modules, classes with their line numbers (not yet),
            # and we don't want to create extra edges, so find the smallest range that fits
            for start_line, end_line, func_name in function_ranges[file_path]:
                if start_line <= line_num <= end_line:
                    # This macro is used inside this function
                    print(f"Macro {macro_name} at {loc_key} used in function {func_name}")
                    add_edge(func_name, macro_name)
                    # since we sorted function_ranges by (start_line, end_line), the first matching function is the innermost one
                    break
            else:
                print(f"no enclosing function for macro {macro_name} at {loc_key}, remove this later")
    #            raise Exception(f"no function found for macro call {macro_name} at {loc_key}")

    with open(PROJECT_ROOT / '.ai/context/internal/debug_entities.json', 'w') as f:
        json.dump(debug_calls_from_to, f, indent=2)
    with open(PROJECT_ROOT / '.ai/context/internal/macro_instantiations.json', 'w') as f:
        json.dump(macro_instantiations, f, indent=2)

    nx.write_gml(call_graph, GRAPH_OUTPUT)
    print(f"[✓] Graph written to {GRAPH_OUTPUT}")

def parse_args():
    parser = argparse.ArgumentParser(description="Build call graph from C++ source files")
    parser.add_argument("log_level", type=str, help="Logging level")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    main(args)
