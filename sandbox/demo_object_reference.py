#%%
import copy

#%%
class Test:
    def __init__(self, a):
        self._vals = [a]
        self.nothing = "hello"
    
    def append(self, val):
        self._vals = [*self._vals, val]
    
    def evans(self, x, y, z):
        self.append(x)
        self.append(y)
        self.append(z)
        
    def __repr__(self) -> str:
        return str(self._vals)
    
    def __eq__(self, other):
        if not isinstance(other, Test):
            return NotImplemented
        return self._vals == other._vals

#%%
a = Test(1)
a.append(2)
a

#%%
b = a

#%%
a = "a new thing"

#%%
b is a

#%%
print(id(a))
print(id(b))

#%%
b == a

#%%
b = Test(1)
b.append(2)
b

#%%
b is a

#%%
b == a