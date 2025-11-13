"""Knowledge Base Manager for handling JSON-based knowledge bases."""

import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from datetime import datetime


class KnowledgeBaseManager:
    """Manages knowledge base operations with JSON storage."""

    def __init__(self, knowledge_base_dir: str = "knowledge_base"):
        """Initialize the knowledge base manager.

        Args:
            knowledge_base_dir: Path to the knowledge base directory
        """
        self.kb_dir = Path(knowledge_base_dir)
        self.kb_dir.mkdir(exist_ok=True)
        self.metadata_file = self.kb_dir / ".import_metadata.json"
        self._ensure_metadata_exists()

    def load_knowledge_base(self, category: str) -> List[Dict[str, Any]]:
        """Load a knowledge base from JSON file.

        Args:
            category: Category name (e.g., 'fall', 'electrical', 'general')

        Returns:
            List of knowledge base entries

        Raises:
            FileNotFoundError: If knowledge base file doesn't exist
        """
        kb_file = self.kb_dir / f"{category}_base.json"

        if not kb_file.exists():
            raise FileNotFoundError(f"Knowledge base not found: {kb_file}")

        with open(kb_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_knowledge_base(self, category: str, entries: List[Dict[str, Any]]):
        """Save a knowledge base to JSON file.

        Args:
            category: Category name (e.g., 'fall', 'electrical', 'general')
            entries: List of knowledge base entries to save
        """
        kb_file = self.kb_dir / f"{category}_base.json"

        with open(kb_file, 'w', encoding='utf-8') as f:
            json.dump(entries, f, indent=2, ensure_ascii=False)

        print(f"💾 Saved {len(entries)} entries to {kb_file.name}")

    def _ensure_metadata_exists(self):
        """Ensure the metadata file exists."""
        if not self.metadata_file.exists():
            initial_metadata = {
                "imported_documents": {},
                "content_hashes": {}
            }
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(initial_metadata, f, indent=2)

    def _load_metadata(self) -> Dict[str, Any]:
        """Load import metadata."""
        with open(self.metadata_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_metadata(self, metadata: Dict[str, Any]):
        """Save import metadata."""
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)

    def is_document_imported(self, filename: str) -> bool:
        """Check if a document has been imported before.

        Args:
            filename: Name of the document file

        Returns:
            True if document was already imported
        """
        metadata = self._load_metadata()
        return filename in metadata.get("imported_documents", {})

    def record_document_import(self, filename: str, category: str, chunks_added: int):
        """Record that a document has been imported.

        Args:
            filename: Name of the document file
            category: Category it was imported to
            chunks_added: Number of chunks added
        """
        metadata = self._load_metadata()
        metadata["imported_documents"][filename] = {
            "category": category,
            "chunks_added": chunks_added,
            "imported_at": datetime.now().isoformat()
        }
        self._save_metadata(metadata)
        print(f"📝 Recorded import: {filename} ({chunks_added} chunks)")

    def _compute_content_hash(self, content: str) -> str:
        """Compute a hash of content for deduplication.

        Args:
            content: Text content to hash

        Returns:
            SHA256 hash of the content
        """
        # Normalize: lowercase, strip whitespace, remove extra spaces
        normalized = ' '.join(content.lower().strip().split())
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

    def _compute_similarity(self, text1: str, text2: str) -> float:
        """Compute similarity between two texts using Jaccard similarity.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score between 0.0 and 1.0
        """
        # Normalize texts
        words1 = set(text1.lower().strip().split())
        words2 = set(text2.lower().strip().split())

        # Compute Jaccard similarity (intersection / union)
        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def is_content_duplicate(self, content: str, category: str, similarity_threshold: float = 0.50) -> bool:
        """Check if similar content already exists in the knowledge base.

        This checks both:
        1. Exact match (via hash)
        2. High similarity (via Jaccard similarity)

        Args:
            content: Text content to check
            category: Category to check in
            similarity_threshold: Minimum similarity to consider duplicate (default: 0.50 = 50%)

        Returns:
            True if duplicate or highly similar content exists
        """
        content_hash = self._compute_content_hash(content)
        metadata = self._load_metadata()

        # Check for exact match first (fast)
        category_hashes = metadata.get("content_hashes", {}).get(category, [])
        if content_hash in category_hashes:
            return True

        # Check for high similarity (slower, but catches near-duplicates)
        try:
            kb_entries = self.load_knowledge_base(category)

            for entry in kb_entries:
                existing_content = entry.get("content", "")
                similarity = self._compute_similarity(content, existing_content)

                if similarity >= similarity_threshold:
                    print(f"⚠️  Found {similarity*100:.1f}% similar content (threshold: {similarity_threshold*100:.0f}%)")
                    return True

        except FileNotFoundError:
            # Knowledge base doesn't exist yet, no duplicates
            pass

        return False

    def _record_content_hash(self, content: str, category: str):
        """Record a content hash to prevent future duplicates.

        Args:
            content: Text content
            category: Category
        """
        content_hash = self._compute_content_hash(content)
        metadata = self._load_metadata()

        if "content_hashes" not in metadata:
            metadata["content_hashes"] = {}

        if category not in metadata["content_hashes"]:
            metadata["content_hashes"][category] = []

        if content_hash not in metadata["content_hashes"][category]:
            metadata["content_hashes"][category].append(content_hash)
            self._save_metadata(metadata)

    def append_to_knowledge_base(
        self,
        category: str,
        new_entries: List[Dict[str, Any]],
        skip_duplicates: bool = True
    ):
        """Append new entries to an existing knowledge base with duplicate detection.

        Args:
            category: Category name (e.g., 'fall', 'electrical', 'general')
            new_entries: List of new entries to append
            skip_duplicates: If True, skip entries with duplicate content (default: True)
        """
        kb_file = self.kb_dir / f"{category}_base.json"

        # Load existing entries
        if kb_file.exists():
            with open(kb_file, 'r', encoding='utf-8') as f:
                existing_entries = json.load(f)
        else:
            existing_entries = []

        # Filter out duplicates if requested
        entries_to_add = []
        skipped_duplicates = 0

        for entry in new_entries:
            content = entry.get("content", "")

            # Check against existing KB
            if skip_duplicates and self.is_content_duplicate(content, category):
                skipped_duplicates += 1
                continue

            # Also check against entries we've already decided to add from this batch
            is_duplicate_in_batch = False
            if skip_duplicates:
                for already_added in entries_to_add:
                    similarity = self._compute_similarity(content, already_added.get("content", ""))
                    if similarity >= 0.50:  # Use same threshold
                        skipped_duplicates += 1
                        is_duplicate_in_batch = True
                        break

            if is_duplicate_in_batch:
                continue

            entries_to_add.append(entry)
            # Record the content hash
            self._record_content_hash(content, category)

        # Append filtered entries
        existing_entries.extend(entries_to_add)

        # Save back
        self.save_knowledge_base(category, existing_entries)

        if skipped_duplicates > 0:
            print(f"⏭️  Skipped {skipped_duplicates} duplicate entries")
        print(f"✅ Appended {len(entries_to_add)} new entries to {category}_base.json")

    def get_all_categories(self) -> List[str]:
        """Get list of all available knowledge base categories.

        Returns:
            List of category names
        """
        categories = []
        for kb_file in self.kb_dir.glob("*_base.json"):
            # Extract category name from filename (e.g., 'fall_base.json' -> 'fall')
            category = kb_file.stem.replace("_base", "")
            categories.append(category)

        return sorted(categories)

    def search_knowledge_base(
        self,
        category: str,
        query: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Search knowledge base entries by keyword.

        Args:
            category: Category name to search in
            query: Search query (case-insensitive)
            limit: Maximum number of results to return

        Returns:
            List of matching entries
        """
        entries = self.load_knowledge_base(category)
        query_lower = query.lower()

        results = []
        for entry in entries:
            # Search in title and content
            if (query_lower in entry.get("title", "").lower() or
                query_lower in entry.get("content", "").lower()):
                results.append(entry)

                if limit and len(results) >= limit:
                    break

        return results

    def get_entries_by_category_tag(
        self,
        knowledge_base_category: str,
        tag: str
    ) -> List[Dict[str, Any]]:
        """Get entries filtered by their internal category tag.

        Args:
            knowledge_base_category: Knowledge base category (e.g., 'fall', 'electrical')
            tag: Internal category tag to filter by (e.g., 'equipment', 'procedures')

        Returns:
            List of matching entries
        """
        entries = self.load_knowledge_base(knowledge_base_category)

        return [
            entry for entry in entries
            if entry.get("category") == tag
        ]

    def get_stats(self, category: str) -> Dict[str, Any]:
        """Get statistics about a knowledge base.

        Args:
            category: Category name

        Returns:
            Dictionary with statistics
        """
        entries = self.load_knowledge_base(category)

        # Count entries by internal category tag
        category_counts = {}
        total_content_length = 0

        for entry in entries:
            tag = entry.get("category", "unknown")
            category_counts[tag] = category_counts.get(tag, 0) + 1
            total_content_length += len(entry.get("content", ""))

        return {
            "total_entries": len(entries),
            "categories": category_counts,
            "avg_content_length": total_content_length // len(entries) if entries else 0,
            "total_content_length": total_content_length
        }

    def validate_entry(self, entry: Dict[str, Any]) -> bool:
        """Validate that an entry has required fields.

        Args:
            entry: Entry dictionary to validate

        Returns:
            True if valid, False otherwise
        """
        required_fields = ["title", "content", "category"]

        for field in required_fields:
            if field not in entry:
                print(f"⚠️ Warning: Entry missing required field '{field}'")
                return False

            if not entry[field] or not str(entry[field]).strip():
                print(f"⚠️ Warning: Entry has empty '{field}' field")
                return False

        return True

    def clean_and_deduplicate(self, category: str):
        """Clean and remove duplicate entries from a knowledge base.

        Args:
            category: Category name to clean
        """
        entries = self.load_knowledge_base(category)

        # Remove invalid entries
        valid_entries = [e for e in entries if self.validate_entry(e)]

        # Remove duplicates (based on title and content)
        seen = set()
        unique_entries = []

        for entry in valid_entries:
            # Create a hash of title + content
            entry_hash = (
                entry["title"].strip().lower(),
                entry["content"].strip().lower()
            )

            if entry_hash not in seen:
                seen.add(entry_hash)
                unique_entries.append(entry)

        removed_count = len(entries) - len(unique_entries)
        if removed_count > 0:
            print(f"🧹 Removed {removed_count} duplicate/invalid entries")
            self.save_knowledge_base(category, unique_entries)
        else:
            print(f"✅ No duplicates found in {category}_base.json")

        return len(unique_entries)
