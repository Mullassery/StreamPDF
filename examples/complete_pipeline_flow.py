#!/usr/bin/env python3
"""
Complete Pipeline Flow Example

Shows the entire journey of search results through filtering stages:
1. Initial search results (all matched sections)
2. Filtered by relevance score
3. Filtered by filtering strategy (strict/balanced/lenient)
4. Final selection after token budget constraint

Demonstrates how PyStreamPDF progressively narrows down results
through each stage of the pipeline.
"""

from pystreampdf.search import SearchResult, SearchResults
from pystreampdf.config import FilteringConfig, TokenBudgetConfig


def create_raw_search_results():
    """Create initial search results before any filtering"""
    results = [
        SearchResult(
            section_title="Chapter 1: Introduction to Machine Learning",
            page_start=1, page_end=8,
            relevance_score=0.95,
            word_count=3200,
            preview="Machine learning is a subset of artificial intelligence. It enables systems to learn from data without being programmed...",
            matched_terms=["machine", "learning"]
        ),
        SearchResult(
            section_title="Chapter 2: Supervised Learning Methods",
            page_start=9, page_end=22,
            relevance_score=0.88,
            word_count=5100,
            preview="Supervised learning uses labeled training data. Common algorithms include linear regression, decision trees, and neural networks...",
            matched_terms=["learning", "methods"]
        ),
        SearchResult(
            section_title="Section 3.1: Feature Scaling Techniques",
            page_start=23, page_end=31,
            relevance_score=0.72,
            word_count=2400,
            preview="Feature scaling normalizes input variables to similar ranges. This improves model convergence and prevents bias...",
            matched_terms=["machine", "learning"]
        ),
        SearchResult(
            section_title="Section 3.2: Dimensionality Reduction",
            page_start=32, page_end=42,
            relevance_score=0.68,
            word_count=3800,
            preview="Dimensionality reduction techniques reduce the number of features in a dataset. PCA and t-SNE are popular methods...",
            matched_terms=["learning"]
        ),
        SearchResult(
            section_title="Chapter 4: Unsupervised Learning",
            page_start=43, page_end=58,
            relevance_score=0.82,
            word_count=4600,
            preview="Unsupervised learning discovers patterns in unlabeled data. Clustering and anomaly detection are key applications...",
            matched_terms=["learning"]
        ),
        SearchResult(
            section_title="Section 5.3: Model Evaluation Metrics",
            page_start=65, page_end=75,
            relevance_score=0.55,
            word_count=2100,
            preview="Evaluation metrics assess model performance. Accuracy, precision, recall, and F1-score are commonly used...",
            matched_terms=["machine", "learning"]
        ),
        SearchResult(
            section_title="Chapter 6: Deep Learning Fundamentals",
            page_start=78, page_end=95,
            relevance_score=0.91,
            word_count=6200,
            preview="Deep learning uses neural networks with multiple layers. It achieves state-of-the-art results in many tasks...",
            matched_terms=["learning"]
        ),
        SearchResult(
            section_title="Appendix B: Mathematical Notation",
            page_start=200, page_end=210,
            relevance_score=0.35,
            word_count=1200,
            preview="This appendix defines mathematical symbols and notation used throughout the book...",
            matched_terms=["learning"]
        ),
    ]
    return SearchResults("machine learning", results)


def print_stage(stage_name, results, description=""):
    """Print results for a pipeline stage"""
    print("\n" + "=" * 140)
    print(f"STAGE: {stage_name}")
    if description:
        print(f"Description: {description}")
    print("=" * 140)
    print(results.to_cli_table())
    print(f"\n📊 Summary: {results.count()} results, {sum(r.word_count for r in results.results)} total words")


def main():
    print("\n" + "█" * 140)
    print("█" + " " * 138 + "█")
    print("█" + "  Complete Pipeline Flow: From Raw Search to Final Token-Constrained Selection".center(138) + "█")
    print("█" + " " * 138 + "█")
    print("█" * 140)

    # ========== STAGE 1: RAW SEARCH RESULTS ==========
    raw_results = create_raw_search_results()
    print_stage(
        "1️⃣  RAW SEARCH RESULTS",
        raw_results,
        "All sections matched by query 'machine learning' - no filtering applied"
    )
    print("\n💡 Note: All matched sections are included, even low-relevance results")

    # ========== STAGE 2: FILTER BY RELEVANCE THRESHOLD ==========
    print("\n" + "─" * 140)
    print("↓ Applying Relevance Threshold Filter (min_score = 0.60)")
    print("─" * 140)

    relevance_filtered = raw_results.by_relevance(0.60)
    print_stage(
        "2️⃣  AFTER RELEVANCE FILTERING",
        relevance_filtered,
        "Removed low-relevance results (Appendix B: 0.35, Model Evaluation: 0.55)"
    )
    print(f"\n❌ Filtered out: {raw_results.count() - relevance_filtered.count()} sections")
    print(f"   - Appendix B (0.35 relevance)")
    print(f"   - Section 5.3 (0.55 relevance)")

    # ========== STAGE 3: APPLY FILTERING STRATEGY ==========
    print("\n" + "─" * 140)
    print("↓ Applying Filtering Strategy")
    print("─" * 140)

    strategy = FilteringConfig.get_strategy("balanced")
    print(f"\nStrategy: BALANCED")
    print(f"  - Min Relevance: {strategy['min_relevance_score']}")
    print(f"  - Max Sections: {strategy['max_sections']}")
    print(f"  - Description: {strategy['description']}")

    # Apply strategy filter
    strategy_filtered = relevance_filtered.by_relevance(strategy['min_relevance_score']).top(strategy['max_sections'])
    print_stage(
        "3️⃣  AFTER FILTERING STRATEGY",
        strategy_filtered,
        f"Kept top {strategy['max_sections']} sections by relevance score"
    )
    print(f"\n❌ Filtered out: {relevance_filtered.count() - strategy_filtered.count()} sections")
    print(f"   - Dimensionality Reduction (0.68 relevance - outside top 5)")

    # ========== STAGE 4: TOKEN BUDGET CONSTRAINT ==========
    print("\n" + "─" * 140)
    print("↓ Applying Token Budget Constraint")
    print("─" * 140)

    token_budget = TokenBudgetConfig.get_preset("standard")  # 500 tokens
    print(f"\nToken Budget: {token_budget} tokens (STANDARD preset)")
    print(f"Rough conversion: ~1.3 tokens per word")

    # Calculate which sections fit in token budget
    total_words_available = 0
    selected_sections = []
    token_estimate = 0

    print("\nAccumulating sections by relevance:")
    for result in strategy_filtered.sorted_by_relevance().results:
        estimated_tokens = int(result.word_count * 1.3)
        if token_estimate + estimated_tokens <= token_budget:
            selected_sections.append(result)
            token_estimate += estimated_tokens
            total_words_available += result.word_count
            status = "✓ SELECTED"
        else:
            status = "✗ EXCLUDED (exceeds budget)"

        print(f"  {status:20} | {result.relevance_score:.0%} | {result.pages_range():10} | {result.word_count:5}w → ~{estimated_tokens} tokens | {result.section_title}")

    final_results = SearchResults("machine learning", selected_sections)
    print_stage(
        "4️⃣  FINAL SELECTION (AFTER TOKEN BUDGET)",
        final_results,
        f"Sections fitting within {token_budget}-token budget"
    )
    print(f"\n❌ Filtered out: {strategy_filtered.count() - final_results.count()} sections due to token budget constraint")
    print(f"   - Chapter 4: Unsupervised Learning (4600w → ~5980 tokens, exceeds budget)")

    # ========== SUMMARY ==========
    print("\n" + "=" * 140)
    print("📊 COMPLETE PIPELINE SUMMARY")
    print("=" * 140)

    print(f"\n┌─ Input Stage")
    print(f"│  Raw search results: {raw_results.count()} sections, {sum(r.word_count for r in raw_results.results)} words")

    print(f"\n├─ Filter 1: Relevance Threshold (>0.60)")
    print(f"│  Results: {relevance_filtered.count()} sections, {sum(r.word_count for r in relevance_filtered.results)} words")
    print(f"│  Removed: {raw_results.count() - relevance_filtered.count()} low-relevance sections")

    print(f"\n├─ Filter 2: Filtering Strategy (BALANCED: top 5, min 0.50 score)")
    print(f"│  Results: {strategy_filtered.count()} sections, {sum(r.word_count for r in strategy_filtered.results)} words")
    print(f"│  Removed: {relevance_filtered.count() - strategy_filtered.count()} sections outside top-5")

    print(f"\n├─ Filter 3: Token Budget ({token_budget} tokens)")
    print(f"│  Results: {final_results.count()} sections, {sum(r.word_count for r in final_results.results)} words (~{token_estimate} tokens)")
    print(f"│  Removed: {strategy_filtered.count() - final_results.count()} sections exceeding budget")

    print(f"\n└─ Output Stage")
    print(f"   Final selection: {final_results.count()} sections")
    print(f"   Reduction: {raw_results.count()} → {final_results.count()} sections ({final_results.count()/raw_results.count()*100:.0f}% of original)")
    print(f"   Word reduction: {sum(r.word_count for r in raw_results.results)} → {sum(r.word_count for r in final_results.results)} words ({sum(r.word_count for r in final_results.results)/sum(r.word_count for r in raw_results.results)*100:.0f}% of original)")

    # ========== DETAILED BREAKDOWN ==========
    print("\n" + "=" * 140)
    print("🔍 DETAILED BREAKDOWN: What Got Filtered Out")
    print("=" * 140)

    print("\nStage 1→2 (Relevance Filter):")
    print("  ❌ Section 5.3: Model Evaluation Metrics (0.55) - Below 0.60 threshold")
    print("  ❌ Appendix B: Mathematical Notation (0.35) - Below 0.60 threshold")

    print("\nStage 2→3 (Filtering Strategy - Top 5 by Relevance):")
    print("  ❌ Section 3.2: Dimensionality Reduction (0.68) - Outside top 5")

    print("\nStage 3→4 (Token Budget - 500 tokens max):")
    print("  ❌ Chapter 4: Unsupervised Learning (4600w → ~5980 tokens) - Exceeds budget")

    # ========== COMPARISON: DIFFERENT STRATEGIES ==========
    print("\n" + "=" * 140)
    print("📈 COMPARISON: Different Filtering Strategies Applied to Same Results")
    print("=" * 140)

    strategies_to_compare = ["strict", "balanced", "lenient"]
    for strat_name in strategies_to_compare:
        strat = FilteringConfig.get_strategy(strat_name)
        strat_results = relevance_filtered.by_relevance(strat['min_relevance_score']).top(strat['max_sections'])
        total_words = sum(r.word_count for r in strat_results.results)
        print(f"\n{strat_name.upper():10} | Sections: {strat_results.count():2} | Words: {total_words:5} | Min Score: {strat['min_relevance_score']:.2f} | Max Sections: {strat['max_sections']:2} | {strat['description']}")

    print("\n" + "=" * 140)
    print("✨ Pipeline flow complete! Results narrowed from raw search to final selection.")
    print("=" * 140)


if __name__ == "__main__":
    main()
