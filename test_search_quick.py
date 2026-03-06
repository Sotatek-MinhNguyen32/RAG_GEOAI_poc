#!/usr/bin/env python
"""Quick test of search functionality."""
from shared.clients import qdrant_client, es_client

# Test ES search
print("=" * 60)
print("Elasticsearch Search")
print("=" * 60)
result = es_client.search(
    index='images_metadata',
    body={"query": {"match_all": {}}, "size": 3}
)
print(f"Found {result['hits']['total']['value']} documents")
for hit in result['hits']['hits'][:3]:
    doc = hit['_source']
    print(f"  {doc.get('id', 'N/A')}: {doc.get('desc_text', 'N/A')[:60]}...")

# Test Qdrant search
print()
print("=" * 60)
print("Qdrant Vector Search")  
print("=" * 60)
info = qdrant_client.get_collection('desc_embed')
print(f"Collection has {info.points_count} vectors")

# Search for a random vector
try:
    results = qdrant_client.search(
        collection_name="desc_embed",
        query_vector=[0.1] * 2048,
        limit=3
    )
    print(f"Search results: {len(results)} items")
    for r in results[:3]:
        print(f"  id={r.id}, score={r.score:.4f}, payload={r.payload}")
except Exception as e:
    print(f"Search error: {e}")

print()
print("✓ Pipeline working!")
