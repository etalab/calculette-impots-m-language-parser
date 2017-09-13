import json

def dumps(obj):
    return json.dumps(obj, sort_keys=True, indent=2)
