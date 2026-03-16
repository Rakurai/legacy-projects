from enum import Enum
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple, Any, ClassVar, Iterator
from pydantic import RootModel, BaseModel, Field, AliasChoices
import json

PROJECT_ROOT = Path('../..').resolve()  # Adjust as needed to find the project root

OLD_DOC_DATABASE_PATH = PROJECT_ROOT / ".ai/context/internal/doc_db copy.json"
DOC_DATABASE_PATH = PROJECT_ROOT / ".ai/context/internal/doc_db.json"
GENERATED_DOCS_DIR = PROJECT_ROOT / ".ai/context/internal/generated_docs"

# Create directories if they don't exist
GENERATED_DOCS_DIR.mkdir(parents=True, exist_ok=True)

# update the persistent document database that maps unique identifiers (persistant across doxygen runs)
# to documentation.  we will use that database to create doxygen comment blocks
if not DOC_DATABASE_PATH.exists():
    DOC_DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DOC_DATABASE_PATH, 'w') as f:
        json.dump({}, f)

class DocumentState(str, Enum):
    EXTRACTED_SUMMARY = "extracted_summary"
    GENERATED_SUMMARY = "generated_summary"
    GENERATED_USAGE = "generated_usage"
    REFINED_USAGE = "refined_usage"
    REFINED_SUMMARY = "refined_summary"

class DoxygenFields(BaseModel):
    brief: Optional[str] = None
    details: Optional[str] = None
    params: Optional[Dict[str, str]] = None
    returns: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices('return', 'returns'),   # accepted on input
        serialization_alias='returns'                         # single name on output
    )
    tparams: Optional[Dict[str, str]] = None
    throws: Optional[str] = None
    notes: Optional[str] = None
    rationale: Optional[str] = None

class Document(DoxygenFields, BaseModel):
    state: Optional[str] = None
    cid: str
    mid: str
    etype: str
    kind: str
    name: str
    qualified_name: Optional[str] = None
    definition: Optional[str] = None
    argsstring: Optional[str] = None
    prompt: Optional[str] = None
    response: Optional[DoxygenFields] = None
    usages: Optional[Dict[str, str]] = None

    def to_doxygen(self) -> str:
        lines = ['/**']


        # Tag for doxygen to associate this block with the correct entity
        tag_map = {
            "function": "@fn",
            "variable": "@var",
            "enum": "@enum",
            "class": "@class",
            "struct": "@struct",
            "namespace": "@namespace",
            "define": "@def",
            "group": "@defgroup"
        }
        tag = tag_map.get(self.kind, "@fn")
        if self.kind == 'function':
            lines.append(f" * {tag} {self.definition}{self.argsstring}")
        else:
            lines.append(f" * {tag} {self.name}")

        if self.brief:
            lines.append(" *")
            lines.append(f" * @brief {self.brief}")

        if self.details:
            lines.append(" *")
            lines.append(f" * @details {self.details}")

        if self.notes:
            lines.append(" *")
            lines.append(f" * @note {self.notes}")

        if self.rationale:
            lines.append(" *")
            lines.append(f" * @rationale {self.rationale}")

        lines.append(" *")

        # Type parameters
        if self.tparams:
            for tname, desc in self.tparams.items():
                lines.append(f" * @tparam {tname} {desc}")

        # Function parameters
        if self.params:
            for pname, desc in self.params.items():
                lines.append(f" * @param {pname} {desc}")

        if self.returns:
            lines.append(f" * @return {self.returns}")

        if self.throws:
            lines.append(f" * @throws {self.throws}")

        lines.append(" */")
        return "\n".join(lines)

class DocumentDB(BaseModel):
    """
    A class that manages the document database and provides methods for accessing and manipulating documents.
    
    This class maintains a two-level dictionary of documents, indexed first by compound_id and then by entity_signature.
    It provides methods for loading, saving, retrieving, and adding documents.
    """
    docs: Dict[str, Dict[str, Document]] = {}
    
    def __init__(self, **data):
        super().__init__(**data)
        if not self.docs:
            self.load()
    
    def load(self) -> Dict[str, Dict[str, Document]]:
        """Load documents from disk into the database."""
        doc_map = {}
        for doc_path in GENERATED_DOCS_DIR.glob("*.json"):
            cid = doc_path.stem
            with open(doc_path, "r") as f:
                try:
                    doc_data = json.load(f)
                    doc_map[cid] = {k: Document(**v) for k, v in doc_data.items()}
                    for k, v in doc_map[cid].items():
                        if v.state is None:
                            v.state = DocumentState.EXTRACTED_SUMMARY
                except json.JSONDecodeError:
                    print(f"Error loading {doc_path}, skipping")
                except Exception as e:
                    print(f"Error processing {doc_path}: {e}, skipping")
        self.docs = doc_map
        return doc_map
    
    def save(self, cid: str = None):
        """Save documents from the database to disk."""
        cids = [cid] if cid else list(self.docs.keys())
        for cid in cids:
            doc_path = GENERATED_DOCS_DIR / f"{cid}.json"
            with open(doc_path, "w") as f:
                json.dump({k: v.model_dump() for k, v in self.docs[cid].items()}, f, indent=2)
    
    def get_doc(self, compound_id: str, entity_signature: str) -> Optional[Document]:
        """Get a document by compound_id and entity_signature."""
        if compound_id in self.docs and entity_signature in self.docs[compound_id]:
            return self.docs[compound_id][entity_signature]
        return None
    
    def add_doc(self, compound_id: str, entity_signature: str, doc: Document):
        """Add a document to the database and save it to disk."""
        self.docs.setdefault(compound_id, {})[entity_signature] = doc
        self.save(compound_id)
    
    def items(self) -> Iterator[Tuple[str, Document]]:
        """Iterate over all documents as (entity_signature, document) pairs."""
        for compound_id, entities in self.docs.items():
            for entity_signature, doc in entities.items():
                yield f"{compound_id}:{entity_signature}", doc
    
    def __getitem__(self, key: str) -> Dict[str, Document]:
        """Allow dictionary-like access to compounds."""
        return self.docs[key]
    
    def __iter__(self) -> Iterator[str]:
        """Iterate over compound IDs."""
        return iter(self.docs)
    
    def __len__(self) -> int:
        """Get the number of compounds."""
        return len(self.docs)
    
    def __contains__(self, key: str) -> bool:
        """Check if a compound ID exists in the database."""
        return key in self.docs


def is_doc_complete(doc: Document) -> bool:
    """Check if a document is complete."""
    return doc and (doc.response or (doc.brief and doc.details))


def best_doc(docs: List[str]) -> Optional[str]:
    """Return the best documentation from a set of documentation strings."""
    if not docs:
        return None
    # Prefer the longest documentation string
    docs = [d for d in docs if d and len(d) > 0]
    return max(docs, key=lambda d: len(d), default=None)


def validate_doc(doc: Document) -> bool:
    """Validate the structure of a documentation dictionary."""
    if not doc:
        return False
    # Check for required fields
    required_fields = ['brief', 'details', 'returns']
    return all(hasattr(doc, field) for field in required_fields)


# Create a singleton instance of DocumentDatabase
docs_db = DocumentDB()
docs = docs_db.docs  # For backwards compatibility

# Compatibility functions that mirror the old API but use the DocumentDatabase class
def load_docs() -> Dict[str, Dict[str, Document]]:
    """Load documents from disk. Uses the singleton database instance."""
    return docs_db.load()

def save_docs(cid: str = None):
    """Save documents to disk. Uses the singleton database instance."""
    docs_db.save(cid)

def get_doc(compound_id: str, entity_signature: str) -> Optional[Document]:
    """Get a document by compound_id and entity_signature. Uses the singleton database instance."""
    return docs_db.get_doc(compound_id, entity_signature)

def add_doc(compound_id: str, entity_signature: str, doc: Document):
    """Add a document to the database and save it to disk. Uses the singleton database instance."""
    docs_db.add_doc(compound_id, entity_signature, doc)
