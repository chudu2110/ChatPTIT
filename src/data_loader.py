"""Load and preprocess markdown files from data directory — Improved chunking for Vietnamese"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import re
from config import DATA_DIR, DATA_FILES, CHUNK_SIZE, CHUNK_OVERLAP


class DocumentLoader:
    def __init__(self):
        self.data_dir = DATA_DIR
        self.documents = []

    def load_all_documents(self) -> List[Dict[str, Any]]:
        """Load all markdown files from data directory"""
        self.documents = []

        for filename in DATA_FILES:
            md_file = self.data_dir / filename
            if not md_file.exists():
                print(f"   [WARN] File not found: {filename}, skipping.")
                continue
            print(f"   Loading {filename}...")
            content = md_file.read_text(encoding='utf-8')
            doc_type = self._classify_document(filename)
            chunks = self._chunk_by_sections(content, filename, doc_type)
            self.documents.extend(chunks)

        total_files = sum(1 for f in DATA_FILES if (self.data_dir / f).exists())
        print(f"[OK] Loaded {len(self.documents)} chunks from {total_files} files")
        return self.documents

    def _classify_document(self, filename: str) -> str:
        """Classify document type based on filename"""
        if "diem_chuan" in filename:
            return "score"
        elif "danh_muc" in filename:
            return "majors"
        elif "hoc_phi" in filename:
            return "tuition"
        elif "phuong_thuc" in filename:
            return "methods"
        elif "gioi_thieu" in filename:
            return "intro"
        elif "co_hoi" in filename:
            return "careers"
        return "general"

    def _chunk_by_sections(self, text: str, filename: str, doc_type: str) -> List[Dict[str, Any]]:
        """
        Split text into chunks by markdown section boundaries (---, ##, ###).
        Each chunk preserves semantic meaning — a score entry stays as one block.
        Falls back to word-based chunking for very long sections.
        """
        # Split on horizontal rules AND markdown level-2/3 headers
        # Keep the delimiter as part of the following section for context
        section_pattern = re.compile(r'\n(?=---|\n##\s|### )')
        raw_sections = section_pattern.split(text)

        chunks = []
        chunk_idx = 0
        current_header = ""

        for section in raw_sections:
            section = section.strip()
            if not section or len(section) < 20:
                continue

            # Track section header for metadata
            header_match = re.match(r'^#{1,3}\s+(.+)', section)
            if header_match:
                current_header = header_match.group(1).strip()

            # If section fits in one chunk, keep it whole
            words = section.split()
            if len(words) <= CHUNK_SIZE:
                if len(words) > 5:
                    chunks.append(self._make_chunk(section, filename, doc_type, chunk_idx, current_header))
                    chunk_idx += 1
            else:
                # Large section: slide window with overlap
                for start in range(0, len(words), CHUNK_SIZE - CHUNK_OVERLAP):
                    chunk_words = words[start:start + CHUNK_SIZE]
                    chunk_text = " ".join(chunk_words)
                    if len(chunk_words) > 5:
                        chunks.append(self._make_chunk(chunk_text, filename, doc_type, chunk_idx, current_header))
                        chunk_idx += 1

        return chunks

    def _make_chunk(self, text: str, filename: str, doc_type: str,
                    chunk_idx: int, section_title: str = "") -> Dict[str, Any]:
        """Build a chunk dict with rich metadata"""
        return {
            "text": text,
            "source": filename,
            "type": doc_type,
            "section": section_title,
            "chunk_id": f"{filename}_{chunk_idx}",
        }


# -------------------------------------------------------
# Knowledge Base — Parsed structured data for fast lookup
# -------------------------------------------------------
KNOWLEDGE_BASE: Dict[str, Any] = {
    "scores": {},      # {major_name: cutoff_pt5}
    "tuition": "",
    "methods": "",
    "majors": {},
    "intro": "",
    "careers": "",
    "raw_documents": {},
    "sections": {},
}


def load_markdown_content(filename: str) -> str:
    """Load raw markdown content from data directory"""
    file_path = DATA_DIR / filename
    if file_path.exists():
        return file_path.read_text(encoding='utf-8')
    return ""


def init_knowledge_base() -> None:
    """Initialize structured knowledge base from all data files"""
    global KNOWLEDGE_BASE

    # Scores — parsed from diem_chuan_chi_tiet_2025.md
    scores_content = load_markdown_content("diem_chuan_chi_tiet_2025.md")
    KNOWLEDGE_BASE["scores"] = _parse_scores(scores_content)

    # Raw text for retrieval
    KNOWLEDGE_BASE["tuition"] = load_markdown_content("hoc_phi_hoc_bong.md")
    KNOWLEDGE_BASE["methods"] = load_markdown_content("phuong_thuc.md")
    KNOWLEDGE_BASE["intro"] = load_markdown_content("gioi_thieu_ptit.md")
    KNOWLEDGE_BASE["careers"] = load_markdown_content("co_hoi_viec_lam.md")
    KNOWLEDGE_BASE["raw_documents"] = {
        filename: load_markdown_content(filename)
        for filename in DATA_FILES
    }
    KNOWLEDGE_BASE["sections"] = {
        filename: split_markdown_sections(content)
        for filename, content in KNOWLEDGE_BASE["raw_documents"].items()
        if content
    }

    majors_content = load_markdown_content("danh_muc_nganh_dao_tao.md")
    KNOWLEDGE_BASE["majors"] = _parse_majors(majors_content)

    score_count = len(KNOWLEDGE_BASE["scores"])
    print(f"   [OK] Knowledge base loaded: {score_count} majors with cutoff scores")


def _parse_scores(content: str) -> Dict[str, Any]:
    """
    Parse cutoff scores from diem_chuan_chi_tiet_2025.md.
    Returns dict: {major_name (lowercase) -> {pt5, pt1, sat, ttnv, ...}}
    """
    scores = {}
    # Block pattern: "Ngành: <name> | Mã: <code> | Loại: <type>"
    block_pattern = re.compile(
        r'Ngành:\s*(.+?)\s*\|\s*Mã:\s*(\S+).*?\n(.*?)(?=\nNgành:|\Z)',
        re.DOTALL
    )

    for match in block_pattern.finditer(content):
        name = match.group(1).strip()
        code = match.group(2).strip()
        block = match.group(3)

        entry: Dict[str, Any] = {"code": code, "name": name}

        # Extract each score type
        patterns = {
            "pt5": r'Điểm chuẩn THPT \(PT5\):\s*([\d.]+)',
            "pt1": r'Điểm Tài năng \(PT1\):\s*([\d.]+)',
            "sat": r'SAT:\s*([\d.]+)',
            "act": r'ACT:\s*([\d.]+)',
            "hsa": r'HSA:\s*([\d.]+)',
            "tsa": r'TSA:\s*([\d.]+)',
            "spt": r'SPT:\s*([\d.]+)',
            "apt": r'APT:\s*([\d.]+)',
            "pt4": r'Kết hợp \(PT4\):\s*([\d.]+)',
            "ttnv": r'TTNV.*?:\s*<=?\s*(\d+)',
        }

        for key, pat in patterns.items():
            m = re.search(pat, block, re.IGNORECASE)
            if m:
                entry[key] = float(m.group(1))

        scores[name.lower()] = entry
        if code:
            scores[code.lower()] = entry

    return scores


def _parse_majors(content: str) -> Dict[str, str]:
    """Parse major info blocks from danh_muc_nganh_dao_tao.md"""
    majors = {}
    blocks = re.split(r'\n#{2,3}\s+', content)
    for block in blocks[1:]:
        lines = block.strip().split('\n')
        if lines:
            major_name = lines[0].strip()
            majors[major_name] = '\n'.join(lines)
    return majors


def split_markdown_sections(content: str) -> List[str]:
    """Split markdown content into retrieval-friendly sections."""
    if not content:
        return []
    return [
        section.strip()
        for section in re.split(r"\n(?=---|\n##\s|### )", content)
        if section and len(section.strip()) >= 30
    ]


def get_knowledge_base() -> Dict[str, Any]:
    return KNOWLEDGE_BASE


def lookup_score(query: str) -> Optional[Dict[str, Any]]:
    """Fast lookup of cutoff score from knowledge base"""
    import cutoffs
    major = cutoffs.find_major_by_query(query)
    if major:
        return {
            "name": major.name,
            "code": major.code,
            "pt5": major.cutoff_pt5,
            "ttnv": major.ttnv,
            "pt1": major.cutoff_pt1,
            "sat": major.cutoff_sat,
            "act": major.cutoff_act,
            "hsa": major.cutoff_hsa,
            "tsa": major.cutoff_tsa,
            "spt": major.cutoff_spt,
            "apt": major.cutoff_apt,
            "type": major.program_type,
        }
    return None
