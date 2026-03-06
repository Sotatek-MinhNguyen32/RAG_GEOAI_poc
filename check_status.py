#!/usr/bin/env python
from shared.clients import qdrant_client, es_client

result = es_client.count(index='images_metadata')
print(f'✓ Elasticsearch: {result["count"]} documents indexed')

collection = qdrant_client.get_collection(collection_name='desc_embed')
print(f'✓ Qdrant: {collection.points_count} vectors')

result = es_client.search(index='images_metadata', size=1)
if result['hits']['hits']:
    sample = result['hits']['hits'][0]['_source']
    print(f'\nSample indexed document:')
    print(f'  image_id: {sample.get("image_id")}')
    print(f'  description: {sample.get("description")[:80] if sample.get("description") else "N/A"}...')
