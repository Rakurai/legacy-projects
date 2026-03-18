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
import re
from loguru import logger as log

# Set libclang path (adjust if needed)
cindex.Config.set_library_file("/opt/local/libexec/llvm-20/lib/libclang.dylib")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
COMPILE_COMMANDS = PROJECT_ROOT / "src/compile_commands.json"
GRAPH_OUTPUT = PROJECT_ROOT / "projects/doc_gen/internal/clang_call_graph.json"
SOURCE_DIR = PROJECT_ROOT / "src"

log_level = "info"
log_file = None  # Will be set from command line arguments

# Define cursor kinds that should change the outer entity
ENTITY_CHANGING_CURSORS = {
    CursorKind.CXX_METHOD,
    CursorKind.CONSTRUCTOR,
    CursorKind.DESTRUCTOR,
    CursorKind.CLASS_DECL,
    CursorKind.STRUCT_DECL,  # Add struct declarations as entities
    CursorKind.FUNCTION_DECL,
    CursorKind.NAMESPACE,
    CursorKind.ENUM_DECL,     # Add enum declarations as entities
    CursorKind.TYPEDEF_DECL,   # Add typedef declarations as entities
    CursorKind.CLASS_TEMPLATE, # Add class templates
    CursorKind.UNION_DECL,     # Add union declarations
    CursorKind.CONVERSION_FUNCTION, # Add conversion functions
    CursorKind.NAMESPACE_ALIAS # Add namespace aliases
}

# Define cursor kinds that we should not descend into (skip traversal)
LEAF_CURSORS = {
    # Expressions that won't contain function calls we care about
    CursorKind.INTEGER_LITERAL,
    CursorKind.FLOATING_LITERAL,
    CursorKind.STRING_LITERAL,
    CursorKind.CHARACTER_LITERAL, 
    CursorKind.CXX_BOOL_LITERAL_EXPR,
    CursorKind.CXX_NULL_PTR_LITERAL_EXPR,
    
    # Types and references we don't need to explore
    CursorKind.TYPE_REF,
    CursorKind.TEMPLATE_REF,
    CursorKind.NAMESPACE_REF,
    
    # Simple operators that don't contain calls
    CursorKind.UNARY_OPERATOR,
    CursorKind.BINARY_OPERATOR,  # Basic binary ops (+, -, etc) without calls
    
    # Declarations we've already processed elsewhere
    CursorKind.USING_DECLARATION,
    CursorKind.USING_DIRECTIVE,
    
    # Preprocessor directives without useful call info
    CursorKind.INCLUSION_DIRECTIVE,
    
    # Template parameter lists (we care about template bodies, not parameters)
    CursorKind.TEMPLATE_TYPE_PARAMETER,
    CursorKind.TEMPLATE_NON_TYPE_PARAMETER,
    
    # Comments
    CursorKind.UNEXPOSED_ATTR,

    # Additional leaf cursors that don't need traversal
    CursorKind.PAREN_EXPR,            # Parenthesized expressions are wrappers
    CursorKind.CXX_FUNCTIONAL_CAST_EXPR,  # Cast expressions without calls
    CursorKind.CSTYLE_CAST_EXPR,      # C-style casts
    CursorKind.COMPOUND_ASSIGNMENT_OPERATOR,  # +=, -=, etc.
    CursorKind.ENUM_CONSTANT_DECL,    # Individual enum values
}

# Define cursor kinds that we silently process (no logging, but still traverse)
IGNORED_CURSORS = {
    # Common structural elements
    CursorKind.COMPOUND_STMT,      # Function/block bodies
    CursorKind.DECL_STMT,          # Declaration statements
    CursorKind.NULL_STMT,          # Empty statements (;)
    CursorKind.INCLUSION_DIRECTIVE,  # Include directives

    # Control flow
    CursorKind.IF_STMT,
    CursorKind.FOR_STMT,
    CursorKind.WHILE_STMT,
    CursorKind.DO_STMT,
    CursorKind.SWITCH_STMT,
    CursorKind.CASE_STMT,
    CursorKind.DEFAULT_STMT,
    CursorKind.BREAK_STMT,
    CursorKind.CONTINUE_STMT,
    CursorKind.RETURN_STMT,
    
    # Common expressions
    CursorKind.DECL_REF_EXPR,      # References to declarations
    CursorKind.MEMBER_REF_EXPR,    # Member references (obj.member)
    CursorKind.ARRAY_SUBSCRIPT_EXPR,
    CursorKind.CONDITIONAL_OPERATOR,  # Ternary operator
    CursorKind.UNEXPOSED_EXPR,     # Generic expressions
    CursorKind.CXX_THIS_EXPR,      # 'this' pointer
    
    # Variable declarations
    CursorKind.VAR_DECL,
    CursorKind.PARM_DECL,          # Function parameters
    
    # Type declarations that aren't entity changes
    # Remove TYPEDEF_DECL since we moved it to ENTITY_CHANGING_CURSORS
    CursorKind.TYPE_ALIAS_DECL,
    CursorKind.TYPE_REF,
    CursorKind.FIELD_DECL,         # Class/struct field declarations
    
    # C++ specific
    CursorKind.CXX_ACCESS_SPEC_DECL,  # public/private/protected
    CursorKind.CXX_BASE_SPECIFIER,    # Base class specifications
    CursorKind.NAMESPACE_REF,         # References to namespaces

    # Additional ignored cursors - process silently but check children
    CursorKind.INIT_LIST_EXPR,        # Initializer lists
    CursorKind.MEMBER_REF,            # Direct member references (not method calls)
    CursorKind.LINKAGE_SPEC,          # External linkage specifications
    CursorKind.FRIEND_DECL,           # Friend declarations
}

def write(indent, message, min_level="info"):
    if min_level == 'none':
        return
    if min_level == "debug" and log_level != "debug":
        return
    
    log_message = f"{min_level.upper():<5}: {'  '*indent}{message}"
    
    # Write to log file if specified, otherwise print to console
    if log_file:
        log_file.write(log_message + "\n")
        log_file.flush()  # Ensure output is written immediately
    else:
        print(log_message)

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
    return file_path.is_relative_to(SOURCE_DIR)

def get_file_path(cursor):
    if cursor.location.file:
        return Path(cursor.location.file.name).resolve()
    return None

def add_node(func_name, file_path, start_line, end_line, entity_type=None, entity_subtype=None, comment=None):
    call_graph.add_node(func_name, 
                        file=str(file_path), 
                        line=start_line, 
                        end_line=end_line, 
                        entity_type=str(entity_type) if entity_type else '?',
                        entity_subtype=str(entity_subtype) if entity_subtype else '?',
                        doc_comment=comment or '')  # Add the comment as a node attribute
    return func_name  # Return node identifier

def add_edge(from_func, to_func):
    call_graph.add_edge(from_func, to_func)
    debug_calls_from_to.setdefault(from_func, []).append(to_func)

def get_comment_for_cursor(cursor):
    """Extract documentation comment for a cursor if available."""
    raw_comment = cursor.raw_comment
    if raw_comment:
        # Clean up the comment by removing comment markers and normalizing whitespace
        lines = raw_comment.split('\n')
        cleaned_lines = []
        for line in lines:
            # Remove common comment markers
            line = re.sub(r'^\s*\/\*+\s*|\s*\*+\/\s*$', '', line)  # Remove /* and */
            line = re.sub(r'^\s*\*\s*', '', line)  # Remove leading * in multiline comments
            line = re.sub(r'^\s*\/\/+\s*', '', line)  # Remove // 
            line = re.sub(r'^\s*\/\/\/\s*', '', line)  # Remove ///
            cleaned_lines.append(line.strip())
        
        return '\n'.join(cleaned_lines).strip()
    return None

def visit(cursor, outer_entity=None, indent=0):
    file_path = get_file_path(cursor)

    write(indent, f"Visiting: {cursor.kind} - {cursor.spelling}", 'debug')

    if file_path and not in_source_dir(file_path):
        write(indent, f"Skipping external file: {cursor.kind} - {cursor.spelling}", 'none')
        return


    # Check if this cursor should change the outer entity
    elif cursor.kind in ENTITY_CHANGING_CURSORS:
        write(indent, f"Found entity definition: {cursor.kind} - {cursor.spelling}")
        name = get_qualified_name(cursor)
        
        # Get documentation comment if available
        comment = get_comment_for_cursor(cursor)
        if comment:
            write(indent + 1, f"Found documentation comment: {comment[:50]}...", 'debug')
        
        node_id = add_node(
            name,
            file_path,
            cursor.extent.start.line,
            cursor.extent.end.line,
            entity_type=cursor.kind,
            entity_subtype="DEFN" if cursor.is_definition() else "decl",
            comment=comment  # Pass the comment to add_node
        )

        if outer_entity:
            add_edge(outer_entity, node_id)

        outer_entity = node_id  # Store node identifier
        
        # Special handling for table definitions
        if cursor.kind == CursorKind.TYPEDEF_DECL and "_type" in cursor.spelling:
            write(indent, f"Found table type definition: {cursor.spelling}", 'debug')
            # Table types are important structural elements

    # # Add more detailed logging for class declarations
    # if cursor.kind == CursorKind.CLASS_DECL:
    #     write(indent, f"Found class declaration: {cursor.spelling} at {file_path}:{cursor.extent.start.line}")
    #     write(indent, f"  Qualified name: {get_qualified_name(cursor)}")
    #     write(indent, f"  Is definition: {cursor.is_definition()}")
    #     write(indent, f"  Semantic parent: {cursor.semantic_parent.spelling} ({cursor.semantic_parent.kind})")
        
    #     # Make sure we're capturing the actual class definition, not just a forward declaration
    #     if cursor.is_definition():
    #         name = get_qualified_name(cursor)
    #         comment = get_comment_for_cursor(cursor)
            
    #         # Create a node specifically for the class itself
    #         class_node_id = add_node(
    #             name,
    #             file_path,
    #             cursor.extent.start.line,
    #             cursor.extent.end.line,
    #             entity_type="CLASS_DEFINITION",  # Special entity type for class definitions
    #             comment=comment
    #         )
            
    #         # Debug: print methods that are directly children of this class
    #         for child in cursor.get_children():
    #             if child.kind == CursorKind.CXX_METHOD:
    #                 method_name = get_qualified_name(child)
    #                 write(indent + 1, f"Found method {method_name} in class {name}", 'debug')
            
    #         # Continue with normal processing
    #         outer_entity = class_node_id
    #     else:
    #         write(indent, f"  Skipping forward declaration of class {cursor.spelling}")
    
    # Add handling for class templates
    # elif cursor.kind == CursorKind.CLASS_TEMPLATE:
    #     write(indent, f"Found class template: {cursor.spelling} at {file_path}:{cursor.extent.start.line}")
    #     write(indent, f"  Qualified name: {get_qualified_name(cursor)}")
    #     write(indent, f"  Is definition: {cursor.is_definition()}")
        
    #     if cursor.is_definition():
    #         name = get_qualified_name(cursor)
    #         comment = get_comment_for_cursor(cursor)
            
    #         # Create a node specifically for the class template
    #         template_node_id = add_node(
    #             name,
    #             file_path,
    #             cursor.extent.start.line,
    #             cursor.extent.end.line,
    #             entity_type="CLASS_TEMPLATE",
    #             comment=comment
    #         )
            
    #         # Continue with normal processing
    #         outer_entity = template_node_id
    #     else:
    #         write(indent, f"  Skipping forward declaration of class template {cursor.spelling}")
    
    # # Add handling for union declarations
    # elif cursor.kind == CursorKind.UNION_DECL:
    #     write(indent, f"Found union declaration: {cursor.spelling} at {file_path}:{cursor.extent.start.line}")
        
    #     if cursor.is_definition():
    #         name = get_qualified_name(cursor)
    #         comment = get_comment_for_cursor(cursor)
            
    #         union_node_id = add_node(
    #             name,
    #             file_path,
    #             cursor.extent.start.line,
    #             cursor.extent.end.line,
    #             entity_type="UNION_DEFINITION",
    #             comment=comment
    #         )
            
    #         outer_entity = union_node_id
    #     else:
    #         write(indent, f"  Skipping forward declaration of union {cursor.spelling}")
    
    # Original entity changing cursors handling
    elif cursor.kind in (
        CursorKind.MACRO_DEFINITION,
        CursorKind.FUNCTION_TEMPLATE, # this is the declaration, actually more useful than the multiple definitions
    ):
        if file_path:
            write(indent, f"Found macro definition: {cursor.kind} - {cursor.spelling}", 'debug')
            node_id = add_node(
                get_qualified_name(cursor),
                file_path,
                cursor.extent.start.line,
                cursor.extent.end.line,
                entity_type=cursor.kind
            )
        else:
            write(indent, f"Skipping global macro definition: {cursor.kind} - {cursor.spelling}", 'debug')
            pass

        # skip processing the body of a template function or macro
        return

    ### cursors that will have a calling_func
#    elif CursorKind.is_reference(cursor.kind):
    elif cursor.kind in (
        CursorKind.CALL_EXPR,
#        CursorKind.MACRO_INSTANTIATION,
#        CursorKind.CXX_METHOD_CALL,
#        CursorKind.MEMBER_REF_EXPR
    ):
        # Add debugging to see what's being captured
        write(indent, f"Found call: {cursor.kind} - {cursor.spelling}")
        callee = cursor.referenced
        callee_name = get_qualified_name(callee) if callee else cursor.spelling
        if outer_entity and callee_name:
            if callee and callee.kind == CursorKind.FUNCTION_TEMPLATE:
                write(indent, f"Found function template: {callee.kind} - {callee.spelling}", 'debug')
            add_edge(outer_entity, callee_name)

    elif cursor.kind in (
        CursorKind.MACRO_INSTANTIATION,
    ):
        # Add debugging to see what's being captured
        write(indent, f"Found macro call: {cursor.kind} - {cursor.spelling}", 'debug')

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
        if not outer_entity:
            write(indent, f"forward declaration without current entity: cursor.kind={cursor.kind}, cursor.spelling={cursor.spelling}, cursor.location={cursor.location}")
            # probably a template method, we'll map it by location and name like a macro
            location_key = f"{get_file_path(cursor)}:{cursor.extent.start.line}"
            macro_instantiations.setdefault(cursor.spelling, []).append(location_key)
        else:
            write(indent, f"Found forward declaration: {cursor.kind} - {cursor.spelling}")
            call_graph.add_edge(outer_entity, get_qualified_name(cursor))
            debug_calls_from_to.setdefault(outer_entity, []).append(get_qualified_name(cursor))

    elif cursor.kind in IGNORED_CURSORS:
        # Silently process these cursors - no logging needed
        pass
        
    else:
        write(indent, f"Found other: {cursor.kind} - {cursor.spelling} - {cursor.location.file} ({cursor.extent.start.line}-{cursor.extent.end.line})")

    # Skip traversal for leaf nodes
    if cursor.kind in LEAF_CURSORS:
        return

    # Otherwise, continue traversal
    for child in cursor.get_children():
        visit(child, outer_entity, indent + 1)

def main(args):
    global log_file

    # Determine which source files to process
    if args.files:
        source_files = [SOURCE_DIR / f for f in args.files]
    else:
        source_files = []
        for ext in (".cpp", ".cc", ".c", ".cxx"):
            source_files.extend(SOURCE_DIR.rglob(f"*{ext}"))

    source_files = [f.resolve() for f in source_files if f.is_file()]

    # Ensure all source files are in compile_map
    missing_files = [str(f) for f in source_files if f not in compile_map]
    if missing_files:
        log.warning(f"The following source files are not in compile_commands.json: {missing_files}")
        source_files = [f for f in source_files if f not in missing_files]


    # Open log file if specified
    if args.output_file:
        try:
            log_file = open(args.output_file, 'w', encoding='utf-8')
            log.info(f"Logging to file: {args.output_file}")
        except Exception as e:
            log.warning(f"Error opening log file {args.output_file}: {e}")
            log.info("Falling back to console output")
            log_file = None
    
    log.info("[+] Parsing source files and building call graph...")

    extra_includes = [
        "-isysroot", "/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX.sdk",
        "-isystem", "/opt/local/libexec/llvm-20/include/c++/v1",
        "-isystem", "/opt/local/libexec/llvm-20/lib/clang/20/include",
        "-I", str(PROJECT_ROOT / "src/include"),  # Add your project's include directory
        "-stdlib=libc++"
    ]

    index = cindex.Index.create()
    # for file_path, (working_dir, compile_args) in compile_map.items():
    #     try:
    #         options = cindex.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD | cindex.TranslationUnit.PARSE_INCOMPLETE
    #         tu = index.parse(str(file_path), args=compile_args + extra_includes, options=options)
    #         print(f"Parsed: {file_path.name}")
    #         for child in tu.cursor.get_children():
    #             visit(child)
    #         break # breaking early to just test parsing the first file - Room.cc
    #     except Exception as e:
    #         print(f"[!] Failed to parse {file_path.name}: {e}")
    for file_path in source_files:
        (working_dir, compile_args) = compile_map[file_path]
        options = cindex.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD | cindex.TranslationUnit.PARSE_INCOMPLETE
        tu = index.parse(str(file_path), args=compile_args + extra_includes, options=options)
        log.info(f"Parsed: {file_path.name}")
        
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

    function_ranges = {}
    for label, attrs in call_graph.nodes(data=True):
        if 'line' in attrs and 'end_line' in attrs and 'file' in attrs:
            function_ranges.setdefault(attrs['file'], []).append((attrs['line'], attrs['end_line'], label))

    function_ranges = {file: sorted(ranges, key=lambda x: (x[0], x[1])) for file, ranges in function_ranges.items()}

    with open(PROJECT_ROOT / 'projects/doc_gen/internal/function_ranges.json', 'w') as f:
        json.dump(function_ranges, f, indent=2)

    # Enhance debug output to include entity types
    entity_types = {}
    for node, attrs in call_graph.nodes(data=True):
        if 'entity_type' in attrs:
            entity_types[node] = attrs['entity_type']

    with open(PROJECT_ROOT / 'projects/doc_gen/internal/entity_types.json', 'w') as f:
        json.dump(entity_types, f, indent=2)

    for macro_name, loc_keys in macro_instantiations.items():
        for loc_key in loc_keys:
            file_path, line_num = loc_key.rsplit(':', 1)
            line_num = int(line_num)

            if file_path not in function_ranges:
                log.warning(f"no function ranges found for {file_path}")
                continue

            # Find which function contains this line.  there could be overlapping ranges
            # if we have namespaces, modules, classes with their line numbers (not yet),
            # and we don't want to create extra edges, so find the smallest range that fits
            for start_line, end_line, func_name in function_ranges[file_path]:
                if start_line <= line_num <= end_line:
                    # This macro is used inside this function
                    write(0, f"Macro {macro_name} at {loc_key} used in function {func_name}")
                    add_edge(func_name, macro_name)
                    # since we sorted function_ranges by (start_line, end_line), the first matching function is the innermost one
                    break
            else:
                log.warning(f"no enclosing function for macro {macro_name} at {loc_key}, remove this later")
    #            raise Exception(f"no function found for macro call {macro_name} at {loc_key}")

    with open(PROJECT_ROOT / 'projects/doc_gen/internal/debug_entities.json', 'w') as f:
        json.dump(debug_calls_from_to, f, indent=2)
    with open(PROJECT_ROOT / 'projects/doc_gen/internal/macro_instantiations.json', 'w') as f:
        json.dump(macro_instantiations, f, indent=2)

    # Add functionality to export comments as part of our JSON output
    doc_comments = {}
    for node, attrs in call_graph.nodes(data=True):
        if 'doc_comment' in attrs and attrs['doc_comment']:
            doc_comments[node] = attrs['doc_comment']
    
    with open(PROJECT_ROOT / 'projects/doc_gen/internal/doc_comments.json', 'w') as f:
        json.dump(doc_comments, f, indent=2)
    
    log.info(f"Extracted {len(doc_comments)} documentation comments")
    
    nx.write_gml(call_graph, GRAPH_OUTPUT)
    log.info(f"Graph written to {GRAPH_OUTPUT}")

    # Close log file if it was opened
    if log_file:
        log_file.close()
        log_file = None

def parse_args():
    parser = argparse.ArgumentParser(description="Build call graph from C++ source files")
    parser.add_argument("--log_level", type=str, default="info", help="Logging level (debug, info)")
    parser.add_argument("--output_file", type=str, help="Output file for logs (default: console)")
    parser.add_argument("--files", type=str, nargs='+', help="Process only the specified source file(s)")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    log_level = args.log_level
    main(args)
