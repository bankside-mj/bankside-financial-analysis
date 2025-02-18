class ConditionContainer:
    def __init__(self, div=0, capex=0, eps=0, gm=0):
        self.div: float = div
        self.capex: float = capex
        self.eps: float = eps
        self.gm: float = gm

    def to_float(self):
        self.div = float(self.div)
        self.capex = float(self.capex)
        self.eps = float(self.eps)
        self.gm = float(self.gm)