#!/usr/bin/env python
from shared.clients import qdrant_client
from qdrant_client.models import PointStruct

# Test if we can list collections
collections = qdrant_client.get_collections()
print(f"Collections: {[c.name for c in collections.collections]}")

# Test if we can access the collection
try:
    info = qdrant_client.get_collection('desc_embed')
    print(f"desc_embed collection: {info.points_count} points")
except Exception as e:
    print(f"Error accessing collection: {e}")

# Try a direct upsert
try:
    test_point = PointStruct(
        id=1,
        vector=[0.1] * 2048,
        payload={"test": "value"}
    )
    qdrant_client.upsert(collection_name='desc_embed', points=[test_point])
    print("Test upsert successful")
    
    # Check again
    info = qdrant_client.get_collection('desc_embed')
    print(f"After test upsert: {info.points_count} points")
except Exception as e:
    print(f"Error during test upsert: {e}")
    import traceback
    traceback.print_exc()
