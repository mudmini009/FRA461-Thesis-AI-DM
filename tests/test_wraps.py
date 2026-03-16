from unittest.mock import patch

def foo(): return {"a":1}
class A:
   def b(self): return foo()

with patch.object(A, 'b', wraps=A().b) as mock_b:
    A().b()
    print("MOCK RETURN:", mock_b.return_value)
