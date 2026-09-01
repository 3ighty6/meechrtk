from meechrtk.capacity import CapacityManager

def test_capacity_routes():
    c=CapacityManager()
    r=c.route('summarize this short note', required_tokens=100)
    assert r['ok'] and r['provider']

def test_unknown_quota_is_not_fabricated():
    c=CapacityManager(); s=c.snapshot()
    assert all(v['tokens_remaining'] is None for v in s.values())

def test_usage_decrements_known_quota():
    c=CapacityManager(); c.configure('openai',tokens_remaining=1000)
    c.record_usage('openai',250)
    assert c.states['openai'].tokens_remaining==750
