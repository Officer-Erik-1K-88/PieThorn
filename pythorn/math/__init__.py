
# --- logistics ---
class LogicGates:
    def __init__(self, reverse=False):
        self.truthy = True
        self.falsy = False
        if reverse:
            self.truthy = False
            self.falsy = True

    def and_gate(self, *boolean):
        bools = list(boolean) if len(boolean) > 1 else boolean[0]
        bool_val = self.truthy
        for y in bools:
            x = y if isinstance(y,bool) else self.truthy if y==1 else self.falsy
            if not x:
                bool_val = self.falsy
                break
        return bool_val

    def or_gate(self, *boolean):
        bools = list(boolean) if len(boolean) > 1 else boolean[0]
        bool_val = self.falsy
        for y in bools:
            x = y if isinstance(y, bool) else self.truthy if y == 1 else self.falsy
            if x:
                bool_val = self.truthy
                break
        return bool_val

    def not_gate(self, *boolean):
        bools = list(boolean) if len(boolean) > 1 else boolean[0]
        bool_vals = []
        if isinstance(bools,list):
            for y in bools:
                x = y if isinstance(y, bool) else self.truthy if y == 1 else self.falsy
                if x:
                    bool_vals.append(self.falsy)
                else:
                    bool_vals.append(self.truthy)
            return bool_vals
        else:
            if bools:
                return self.falsy
            else:
                return self.truthy

    def nand_gate(self, *boolean):
        bools = list(boolean) if len(boolean) > 1 else boolean[0]
        bool_val = self.falsy
        for y in bools:
            x = y if isinstance(y, bool) else self.truthy if y == 1 else self.falsy
            if not x:
                bool_val = self.truthy
                break
        return bool_val

    def nor_gate(self, *boolean):
        bools = list(boolean) if len(boolean) > 1 else boolean[0]
        bool_val = self.truthy
        for y in bools:
            x = y if isinstance(y, bool) else self.truthy if y == 1 else self.falsy
            if x:
                bool_val = self.falsy
                break
        return bool_val

    def xor_gate(self, *boolean):
        bools = list(boolean) if len(boolean) > 1 else boolean[0]
        bool_val = self.falsy
        for y in bools:
            x = y if isinstance(y, bool) else self.truthy if y == 1 else self.falsy
            if x:
                if self.and_gate(bools):
                    bool_val = self.falsy
                    break
                else:
                    bool_val = self.truthy
                    break
        return bool_val

    def xnor_gate(self, *boolean):
        bools = list(boolean) if len(boolean) > 1 else boolean[0]
        bool_val = self.truthy
        for y in bools:
            x = y if isinstance(y, bool) else self.truthy if y == 1 else self.falsy
            if x:
                if self.and_gate(bools):
                    bool_val = self.truthy
                    break
                else:
                    bool_val = self.falsy
                    break
        return bool_val
