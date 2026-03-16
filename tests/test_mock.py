from unittest.mock import patch

class LLM:
    def get_creative_judgment(self):
        return {"a": 1}

llm = LLM()
orig = llm.get_creative_judgment

def side_effect(*args, **kwargs):
    res = orig(*args, **kwargs)
    side_effect.return_value = res
    return res

with patch.object(llm, 'get_creative_judgment', side_effect=side_effect) as mock:
    llm.get_creative_judgment()
    print(getattr(side_effect, 'return_value', None))
