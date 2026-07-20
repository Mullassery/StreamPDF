"""
Search results and filtering for PyStreamPDF

Provides rich search result metadata (page numbers, relevance scores, previews)
and filtering options (by page range, relevance threshold, content length, etc.)
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import json


@dataclass
class SearchResult:
    """Individual search result with full metadata"""

    section_title: str          # Section/heading title
    page_start: int             # Starting page number
    page_end: int               # Ending page number
    relevance_score: float      # Relevance score (0.0-1.0)
    word_count: int             # Words in this section
    preview: str                # Text preview/snippet
    matched_terms: List[str]    # Query terms that matched

    def pages_range(self) -> str:
        """Get human-readable page range"""
        if self.page_start == self.page_end:
            return f"p.{self.page_start}"
        return f"p.{self.page_start}-{self.page_end}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "section_title": self.section_title,
            "pages": self.pages_range(),
            "page_start": self.page_start,
            "page_end": self.page_end,
            "relevance_score": round(self.relevance_score, 2),
            "word_count": self.word_count,
            "preview": self.preview[:200] + "..." if len(self.preview) > 200 else self.preview,
            "matched_terms": self.matched_terms,
        }

    def to_table_row(self) -> List[str]:
        """Convert to table row for CLI display"""
        score_pct = f"{self.relevance_score * 100:.0f}%"
        return [
            self.section_title[:40],
            self.pages_range(),
            score_pct,
            f"{self.word_count}w",
            self.preview[:50] + "..." if len(self.preview) > 50 else self.preview,
        ]


class SearchFilter:
    """Parameters for filtering search results"""

    def __init__(
        self,
        min_page: Optional[int] = None,
        max_page: Optional[int] = None,
        min_relevance_score: float = 0.0,
        min_word_count: int = 0,
        max_word_count: Optional[int] = None,
        section_title_contains: Optional[str] = None,
    ):
        """
        Initialize search filter

        Args:
            min_page: Minimum page number to include
            max_page: Maximum page number to include
            min_relevance_score: Minimum relevance score (0.0-1.0)
            min_word_count: Minimum section word count
            max_word_count: Maximum section word count
            section_title_contains: Filter by section title substring (case-insensitive)
        """
        self.min_page = min_page
        self.max_page = max_page
        self.min_relevance_score = max(0.0, min(1.0, min_relevance_score))
        self.min_word_count = max(0, min_word_count)
        self.max_word_count = max_word_count
        self.section_title_contains = section_title_contains.lower() if section_title_contains else None

    def matches(self, result: SearchResult) -> bool:
        """Check if a result matches all filter criteria"""
        # Page range filter
        if self.min_page is not None and result.page_start < self.min_page:
            return False
        if self.max_page is not None and result.page_end > self.max_page:
            return False

        # Relevance score filter
        if result.relevance_score < self.min_relevance_score:
            return False

        # Word count filters
        if result.word_count < self.min_word_count:
            return False
        if self.max_word_count is not None and result.word_count > self.max_word_count:
            return False

        # Section title filter
        if self.section_title_contains:
            if self.section_title_contains not in result.section_title.lower():
                return False

        return True

    @staticmethod
    def by_page_range(min_page: int, max_page: int) -> "SearchFilter":
        """Create filter for specific page range"""
        return SearchFilter(min_page=min_page, max_page=max_page)

    @staticmethod
    def by_relevance(min_score: float) -> "SearchFilter":
        """Create filter for minimum relevance score"""
        return SearchFilter(min_relevance_score=min_score)

    @staticmethod
    def by_section(title_contains: str) -> "SearchFilter":
        """Create filter for section title"""
        return SearchFilter(section_title_contains=title_contains)

    @staticmethod
    def by_length(min_words: int, max_words: Optional[int] = None) -> "SearchFilter":
        """Create filter for content length"""
        return SearchFilter(min_word_count=min_words, max_word_count=max_words)


class SearchResults:
    """Collection of search results with filtering and display"""

    def __init__(self, query: str, results: List[SearchResult]):
        """
        Initialize search results

        Args:
            query: The search query
            results: List of SearchResult objects
        """
        self.query = query
        self.results = results

    def filter(self, filter_spec: SearchFilter) -> "SearchResults":
        """
        Filter results using SearchFilter

        Args:
            filter_spec: Filter criteria

        Returns:
            New SearchResults with filtered results
        """
        filtered = [r for r in self.results if filter_spec.matches(r)]
        return SearchResults(self.query, filtered)

    def by_page_range(self, min_page: int, max_page: int) -> "SearchResults":
        """Filter to specific page range"""
        return self.filter(SearchFilter.by_page_range(min_page, max_page))

    def by_relevance(self, min_score: float) -> "SearchResults":
        """Filter by minimum relevance score"""
        return self.filter(SearchFilter.by_relevance(min_score))

    def by_section(self, title_contains: str) -> "SearchResults":
        """Filter by section title substring"""
        return self.filter(SearchFilter.by_section(title_contains))

    def by_length(self, min_words: int, max_words: Optional[int] = None) -> "SearchResults":
        """Filter by content length"""
        return self.filter(SearchFilter.by_length(min_words, max_words))

    def sorted_by_relevance(self, descending: bool = True) -> "SearchResults":
        """Sort results by relevance score"""
        sorted_results = sorted(
            self.results,
            key=lambda r: r.relevance_score,
            reverse=descending
        )
        return SearchResults(self.query, sorted_results)

    def sorted_by_pages(self, ascending: bool = True) -> "SearchResults":
        """Sort results by page number"""
        sorted_results = sorted(
            self.results,
            key=lambda r: r.page_start,
            reverse=not ascending
        )
        return SearchResults(self.query, sorted_results)

    def top(self, n: int) -> "SearchResults":
        """Get top N results"""
        return SearchResults(self.query, self.results[:n])

    def count(self) -> int:
        """Total number of results"""
        return len(self.results)

    def to_cli_table(self) -> str:
        """Format results as CLI table"""
        if not self.results:
            return f"No results found for: {self.query}"

        # Header
        lines = [
            f"SEARCH RESULTS: \"{self.query}\"",
            "=" * 140,
            ""
        ]

        # Column headers
        headers = ["Section", "Pages", "Score", "Length", "Preview"]
        col_widths = [40, 12, 8, 8, 70]

        header_line = " | ".join(
            h.ljust(w) for h, w in zip(headers, col_widths)
        )
        lines.append(header_line)
        lines.append("-" * len(header_line))

        # Results
        for result in self.results:
            row = result.to_table_row()
            line = " | ".join(
                cell.ljust(w) for cell, w in zip(row, col_widths)
            )
            lines.append(line)

        # Summary
        lines.append("")
        lines.append(f"Results: {self.count()} found")

        return "\n".join(lines)

    def to_json(self, pretty: bool = True) -> str:
        """Format results as JSON"""
        data = {
            "query": self.query,
            "total_results": self.count(),
            "results": [r.to_dict() for r in self.results]
        }

        if pretty:
            return json.dumps(data, indent=2)
        return json.dumps(data)

    def summary(self) -> str:
        """Get summary statistics"""
        if not self.results:
            return f"No results for: {self.query}"

        total_words = sum(r.word_count for r in self.results)
        avg_score = sum(r.relevance_score for r in self.results) / len(self.results)
        top_result = self.results[0]

        return f"""Search Summary
================
Query: {self.query}
Results: {self.count()}
Total words: {total_words}
Average relevance: {avg_score:.1%}
Top result: "{top_result.section_title}" ({top_result.pages_range()}) - {top_result.relevance_score:.1%}"""


def combine_filters(*filters: SearchFilter) -> SearchFilter:
    """Combine multiple filters (AND logic)"""
    # Start with the most restrictive values
    combined = SearchFilter()

    for f in filters:
        # Page range: take the intersection
        if f.min_page is not None:
            if combined.min_page is None:
                combined.min_page = f.min_page
            else:
                combined.min_page = max(combined.min_page, f.min_page)

        if f.max_page is not None:
            if combined.max_page is None:
                combined.max_page = f.max_page
            else:
                combined.max_page = min(combined.max_page, f.max_page)

        # Relevance: take the maximum
        combined.min_relevance_score = max(combined.min_relevance_score, f.min_relevance_score)

        # Word count: take the intersection
        combined.min_word_count = max(combined.min_word_count, f.min_word_count)

        if f.max_word_count is not None:
            if combined.max_word_count is None:
                combined.max_word_count = f.max_word_count
            else:
                combined.max_word_count = min(combined.max_word_count, f.max_word_count)

        # Section title: can't combine easily, use first non-None
        if f.section_title_contains and not combined.section_title_contains:
            combined.section_title_contains = f.section_title_contains

    return combined
