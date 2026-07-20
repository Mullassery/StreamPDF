# Search Results and Filtering Guide

PyStreamPDF provides rich search result metadata and flexible filtering options to help you find exactly what you need in your documents.

## Quick Start

### Basic Search with Results Display

```python
import pystreampdf
from pystreampdf.search import SearchFilter, SearchResults

# Open document and build index
doc = pystreampdf.open("document.pdf")
index = doc.build_index("/tmp/index.db")
navigator = doc.navigator_with_index(index)

# Search and get results with metadata
results = navigator.search("neural networks", max_results=20)

# Display all results in table format
print(results.to_cli_table())

# Display as JSON
print(results.to_json())

# Get summary
print(results.summary())
```

### Filtering Results

```python
# Filter by page range (pages 10-20)
results_filtered = results.by_page_range(10, 20)

# Filter by relevance score
results_filtered = results.by_relevance(0.6)  # Min 60% relevance

# Filter by section title
results_filtered = results.by_section("chapter")

# Filter by content length
results_filtered = results.by_length(min_words=100, max_words=500)

# Chain filters
results_filtered = (results
    .by_page_range(10, 50)
    .by_relevance(0.5)
    .by_length(min_words=50)
    .sorted_by_relevance())

print(results_filtered.to_cli_table())
```

## Search Result Metadata

Each search result includes comprehensive information:

```python
result = results.results[0]  # Get first result

# Access metadata
print(f"Section: {result.section_title}")
print(f"Pages: {result.pages_range()}")           # "p.5-8"
print(f"Relevance: {result.relevance_score}")     # 0.95
print(f"Word count: {result.word_count}")         # 350 words
print(f"Preview: {result.preview}")               # First 200 chars of text
print(f"Matched terms: {result.matched_terms}")   # ["neural", "networks"]

# Convert to dictionary
data = result.to_dict()
```

### Result Fields

| Field | Type | Description |
|-------|------|-------------|
| `section_title` | str | Section or heading name |
| `page_start` | int | Starting page number |
| `page_end` | int | Ending page number |
| `relevance_score` | float | 0.0-1.0 relevance to query |
| `word_count` | int | Words in section |
| `preview` | str | Text snippet (first 200 chars) |
| `matched_terms` | list | Query terms found in section |

## Search Filters

### Preset Filters

Create filters using static helper methods:

```python
from pystreampdf.search import SearchFilter

# Filter by page range
f1 = SearchFilter.by_page_range(min_page=10, max_page=50)

# Filter by minimum relevance
f2 = SearchFilter.by_relevance(min_score=0.6)

# Filter by section title
f3 = SearchFilter.by_section(title_contains="Chapter 3")

# Filter by content length
f4 = SearchFilter.by_length(min_words=100, max_words=500)
```

### Custom Filters

For fine-grained control:

```python
from pystreampdf.search import SearchFilter

# Create with multiple criteria
filter_spec = SearchFilter(
    min_page=10,                    # Pages 10+
    max_page=50,                    # Through page 50
    min_relevance_score=0.6,        # 60% relevance or better
    min_word_count=50,              # At least 50 words
    max_word_count=1000,            # No more than 1000 words
    section_title_contains="Chapter"  # Title must contain "Chapter"
)

# Apply filter
results_filtered = results.filter(filter_spec)
```

### Combining Filters

Use AND logic to combine multiple filters:

```python
from pystreampdf.search import SearchFilter, combine_filters

# Create individual filters
by_pages = SearchFilter.by_page_range(10, 50)
by_score = SearchFilter.by_relevance(0.6)
by_section = SearchFilter.by_section("neural")

# Combine them
combined = combine_filters(by_pages, by_score, by_section)
results_filtered = results.filter(combined)
```

## Search Results Object

The `SearchResults` object contains all search results and provides methods for filtering and display.

### Filtering Methods

```python
results = navigator.search("query")

# By page range
results.by_page_range(10, 30)

# By relevance score
results.by_relevance(0.7)

# By section title
results.by_section("introduction")

# By content length
results.by_length(min_words=100)

# Combine multiple filters
results.by_page_range(10, 50).by_relevance(0.6).by_length(min_words=100)
```

### Sorting Methods

```python
# Sort by relevance (highest first)
sorted_by_score = results.sorted_by_relevance(descending=True)

# Sort by page number (ascending)
sorted_by_page = results.sorted_by_pages(ascending=True)

# Chain with filtering
results.by_relevance(0.5).sorted_by_pages()
```

### Sampling Methods

```python
# Get top N results
top_3 = results.top(3)

# Count total results
total = results.count()
```

### Display Methods

```python
# CLI table (interactive terminal)
print(results.to_cli_table())
# Output:
# SEARCH RESULTS: "neural networks"
# ============================================================================...
# Section                    | Pages    | Score | Length | Preview
# Introduction               | p.1-2    |  95%  | 320w   | Deep learning is a...
# Chapter 3: Neural Networks | p.9-12   |  87%  | 2100w  | In this chapter...

# JSON (programmatic)
json_str = results.to_json(pretty=True)

# Summary statistics
print(results.summary())
# Output:
# Search Summary
# ================
# Query: neural networks
# Results: 5
# Total words: 8500
# Average relevance: 84.2%
# Top result: "Chapter 3: Neural Networks" (p.9-12) - 92.0%
```

## Usage Examples

### Example 1: Find High-Confidence Sections

```python
import pystreampdf

doc = pystreampdf.open("document.pdf")
index = doc.build_index("/tmp/index.db")
nav = doc.navigator_with_index(index)

# Search and filter for only high-confidence matches
results = (nav.search("machine learning")
    .by_relevance(0.75)           # 75%+ confidence
    .sorted_by_relevance()
    .top(5))                       # Top 5 results

print(f"Found {results.count()} high-confidence results")
print(results.to_cli_table())
```

### Example 2: Search Specific Chapter

```python
# Search but only in Chapter 3 (pages 45-80)
results = (nav.search("optimization algorithm")
    .by_page_range(45, 80)
    .sorted_by_pages())

print(f"{results.count()} results in Chapter 3")
for result in results.results:
    print(f"  {result.section_title} ({result.pages_range()})")
```

### Example 3: Find Medium-Length Sections

```python
# Find sections that are "just right" length
results = (nav.search("training process")
    .by_length(min_words=200, max_words=800)  # 200-800 words
    .by_relevance(0.5)                         # 50%+ relevant
    .sorted_by_relevance())

print(f"Found {results.count()} medium-length sections")
for result in results.results[:10]:  # Show top 10
    print(f"  {result.section_title}: {result.word_count} words")
```

### Example 4: Progressive Refinement

```python
# Start with broad search
results = nav.search("machine learning")
print(f"Initial: {results.count()} results")

# Progressively narrow down
results = results.by_relevance(0.5)
print(f"High relevance: {results.count()} results")

results = results.by_page_range(1, 100)
print(f"Early chapters: {results.count()} results")

results = results.by_length(min_words=100)
print(f"Substantial sections: {results.count()} results")

# Display final refined results
print(results.to_cli_table())
```

### Example 5: Export Results

```python
# Get search results
results = nav.search("neural networks")

# Save as JSON
with open("search_results.json", "w") as f:
    f.write(results.to_json(pretty=True))

# Get individual results for processing
for result in results.sorted_by_relevance().results:
    page_ref = result.pages_range()
    score = f"{result.relevance_score:.0%}"
    print(f"{score} | {page_ref} | {result.section_title}")
```

## Filter Strategy Guide

### By Use Case

| Goal | Filter Strategy | Example |
|------|-----------------|---------|
| Find key sections | High relevance | `.by_relevance(0.75)` |
| Search specific chapter | Page range | `.by_page_range(45, 80)` |
| Avoid empty sections | Min length | `.by_length(min_words=50)` |
| Focus on key content | Max length | `.by_length(max_words=1000)` |
| Quick answers | Top results | `.top(3)` |
| Comprehensive review | Low relevance threshold | `.by_relevance(0.3)` |

### By Data Type

| Data | Filter | Logic |
|------|--------|-------|
| Narrow/specific | High score, small results | relevance>0.7, top(3) |
| Medium/moderate | Balanced score, filtered length | relevance>0.5, 100-1000w |
| Broad/overview | Low score, large results | relevance>0.3, lenient |

## Performance Implications

### Filter Impact

| Filter | Performance |
|--------|-------------|
| Relevance score | Minimal (instant) |
| Page range | Minimal (instant) |
| Section title | Minimal (substring match) |
| Content length | Minimal (instant) |
| Chain multiple | Negligible overhead |

Most filters apply instantly (<1ms) since results are already retrieved.

## Troubleshooting

### Problem: Too Many Results

```python
# Solution 1: Increase relevance threshold
results = results.by_relevance(0.7)  # Higher threshold

# Solution 2: Limit to top results
results = results.top(10)

# Solution 3: Restrict page range
results = results.by_page_range(1, 50)
```

### Problem: No Results After Filtering

```python
# Check what was filtered out
original = nav.search("query")
print(f"Original: {original.count()} results")

filtered = original.by_relevance(0.8)
print(f"After relevance filter: {filtered.count()}")

# Adjust filter criteria
filtered = original.by_relevance(0.5)  # Lower threshold
print(f"After adjustment: {filtered.count()}")
```

### Problem: Filter Criteria Seem Wrong

```python
# Debug by checking individual results
results = nav.search("query")

for result in results.results[:5]:
    print(f"Section: {result.section_title}")
    print(f"  Pages: {result.page_start}-{result.page_end}")
    print(f"  Score: {result.relevance_score:.2f}")
    print(f"  Words: {result.word_count}")
    print()
```

## Advanced Patterns

### Custom Result Processing

```python
# Get results and process programmatically
results = nav.search("optimization").sorted_by_relevance()

# Extract data
high_confidence = [r for r in results.results if r.relevance_score > 0.8]
sections_by_page = {}
for result in results.results:
    page = result.page_start
    if page not in sections_by_page:
        sections_by_page[page] = []
    sections_by_page[page].append(result)

# Process by page
for page, page_results in sorted(sections_by_page.items()):
    print(f"\nPage {page}:")
    for result in page_results:
        print(f"  - {result.section_title} ({result.relevance_score:.0%})")
```

### Batch Processing

```python
# Search multiple queries
queries = ["optimization", "training", "validation"]

for query in queries:
    results = (nav.search(query)
        .by_relevance(0.6)
        .sorted_by_relevance()
        .top(5))

    print(f"\n{query}: {results.count()} results")
    for result in results.results:
        print(f"  {result.section_title}")
```

### Result Comparison

```python
# Search for related terms
results_ml = nav.search("machine learning").by_relevance(0.6)
results_dl = nav.search("deep learning").by_relevance(0.6)

print(f"Machine Learning: {results_ml.count()} results")
print(f"Deep Learning: {results_dl.count()} results")

# Find overlap (sections matching both)
ml_pages = {r.page_start for r in results_ml.results}
dl_pages = {r.page_start for r in results_dl.results}
overlap = ml_pages & dl_pages

print(f"Overlap: {len(overlap)} pages discuss both")
```

## Implementation Details

The search results and filtering is implemented in:
- **Python**: `pystreampdf/search.py` — SearchResult, SearchFilter, SearchResults classes
- **Integration**: Connected to navigator's search method for unified interface
- **Display**: CLI tables, JSON export, and summary statistics

See PIPELINE_VISUALIZATION.md for related information on understanding retrieval results.
