# Parameters (symbolic, not numeric)
# These parameters represent continuous variables Theta which is an Element of R(θ∈R)
# They are not values, they are symbols.


class Parameter:
    def __init__(self,name:str):
        self.name = name

    def __repr__(self):
        return f"Parameter({self.name})"    