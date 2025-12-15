# A qubit is just an index into Hilbert space.
# Hilbert space is a space that helps us to represent body in many states or dimensions.
# We do NOT store state here.

class Qubit:
    def __init__(self , index:int):
        self.index = index
  
    
   
    def __repr__(self):
        return f"q[{self.index}]"
    
# this depend on the hardware and it is stateless for now