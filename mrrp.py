#!/usr/bin/env python3
"""
Mrrp(.mrrp) - the cat that remembers the future.
It have the ability to never crash and travel time yay enjoy !!
Author : Coderx (yeh cuz i love cats!! (≧∇≦)ﾉ)

Usage:
    python mrrp.py program.mrrp
    python mrrp.py  (starts REPL)

Just a cat language . mrrrrpp  
"""
import re 
import sys
import difflib

def _power_stdlib_dirs():
    import os as _os
    import sys as _sys
    dirs = []
    # 1) PyInstaller bundle temp dir (when --add-data cat_pack is used)
    try:
        _bundle = getattr(_sys, "_MEIPASS", None)
        if _bundle:
            dirs.append(_os.path.join(_bundle, "cat_pack"))
            dirs.append(_os.path.join(_bundle, "lib"))
    except Exception:
        pass
    # 2) folder next to the running exe (portable zip / installed exe)
    try:
        if getattr(_sys, "frozen", False):
            _exe_dir = _os.path.dirname(_os.path.abspath(_sys.executable))
            dirs.append(_os.path.join(_exe_dir, "cat_pack"))
            dirs.append(_os.path.join(_exe_dir, "lib"))
    except Exception:
        pass
    # 3) folder next to mrrp.py source (normal `python mrrp.py` run)
    try:
        _me = _os.path.dirname(_os.path.abspath(__file__))
        dirs.append(_os.path.join(_me, "cat_pack"))
        dirs.append(_os.path.join(_me, "lib"))
    except Exception:
        pass
    # de-dupe, keep order
    _seen = set()
    _out = []
    for _d in dirs:
        if _d and _d not in _seen:
            _seen.add(_d)
            _out.append(_d)
    return _out

KEYWORDS = [
    "mrrp", "meow", "paw", "purr", "hiss", "chase", "zoomies",  # Some custom keywords for the language.
    "trick", "fetch", "sniff", "bury", "dig", "prophecy",
    "flashback", "lives", "nap", "rewind", 
    "from", "to", "step", "will", "be", "is",
    "and", "or", "not" ,"yum", "yuck",  # This is logical keywords.
    "borrow", "adopt",        
]
CAT_EXCUSES = [
    "knocked a vase off the table",
    "got distracted by the red dot",
    "fell off the couch dramatically",
    "saw a cucumber and panicked",
    "chased its own tail instead",
    "decided that was boring",
]

class CatReturn(Exception):
    def __init__(self, value):
        self.value = value

def cat_str(v):
    if v is True:
        return "yum"
    if v is False:
        return "yuck"
    if v is None:
        return ""
    if isinstance(v,float) and v.is_integer():
        return str(int(v))
    return str(v)

def to_number(v):
    if isinstance(v, bool):
        return 1 if v else 0
    if isinstance(v,(int,float)):
        return v
    if isinstance(v,str):
        try:
            if "." in v:
                return float(v)
            return int(v)
        except Exception:
            return None
    return None
def is_truthy(v):
    if v is None:
        return False
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return v!= 0
    if isinstance(v,str):
        return len(v)>0
    return bool(v)

# ------------------------- expression tokenizer , meoww--------------------------#

TOKEN_RE = re.compile(r'''
    (?P<STR>"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')
  | (?P<NUM>\d+\.\d+|\d+)
  | (?P<ID>[A-Za-z_][A-Za-z0-9_\-]*)
  | (?P<OP>==|!=|<=|>=|[+\-*/%<>=(),!.])
''', re.VERBOSE)

def tokenize_expr(s):
    toks = []
    for m in TOKEN_RE.finditer(s):
        kind = m.lastgroup
        val = m.group()
        toks.append((kind,val))
    return toks

class ExprParser:
    def __init__(self,text, interp):
        self.toks = tokenize_expr(text)
        self.pos = 0
        self.interp = interp
        self.text = text

    def peek(self):
        if self.pos < len(self.toks):
            return self.toks[self.pos]
        return(None, None)
    
    def next(self):
        t = self.peek()
        self.pos += 1
        return t
    
    def expect_op(self, ch):
        k, v = self.peek()
        if v == ch:
            self.next()
            return True
        return False

    def parse(self):
        if not self.toks:
            return 0
        v = self.parse_or()
        return v

    def parse_or(self):
        v = self.parse_and()
        while True:
            k,w = self.peek()
            if k == "ID" and w == "or":
                self.next()
                r = self.parse_and()
                v = is_truthy(v) or is_truthy(r)
                v = bool(v)
            else:
                break
        return v

    def parse_and(self):
        v = self.parse_cmp()
        while True:
            k,w = self.peek()
            if k == "ID" and w == "and":
                self.next()
                r = self.parse_cmp()
                v = (is_truthy(v) and is_truthy(r))
                v = bool(v)
            else:
                break
        return v

    def parse_cmp(self):
        v = self.parse_add()
        while True:
            k,w = self.peek()
            op = None
            if k == "OP" and w in ("==", "!=" ,"<", ">", "<=", ">="):
                op = w
                self.next()
            elif k == "ID" and w == "is":
                op = "=="
                self.next()
            elif k == "OP" and w == "=":
                # forgives single = as ==
                op = "=="
                self.next()
            elif k == "OP" and w == "!":
                # forgives ! as != when followed by =? already handled. lone ! -> not handles elsewhere. meoww mrrp.
                break
            else :
                break
            r = self.parse_add()
            v = self.apply_cmp(v,op,r)
        return v
    
    def apply_cmp(self, a, op, b):
        try:
            # numeric compare if both numbers, else string compare
            an, bn = to_number(a), to_number(b)
            if an is not None and bn is not None and not isinstance(a, str) and not isinstance(b, str):
                L, R = an, bn
            else:
                # if both look numeric, compare numeric
                if an is not None and bn is not None and isinstance(a, (int, float)) and isinstance(b, (int, float)):
                    L, R = an, bn
                else:
                    L, R = cat_str(a), cat_str(b)
            if op == "==":
                return L == R
            if op == "!=":
                return L != R
            if op == "<":
                return L < R
            if op == ">":
                return L > R
            if op == "<=":
                return L <= R
            if op == ">=":
                return L >= R
        except Exception as e:
            self.interp.lose_life(f"comparing {a!r} and {b!r} ({e})")
            return False
        return False

    def parse_add(self):
        v = self.parse_mul()
        while True:
            k, w = self.peek()
            if k == "OP" and w in ("+", "-"):
                self.next()
                r = self.parse_mul()
                v = self.apply_add(v,w,r)
            else:
                break
        return v
    def apply_add(self, a ,op ,b):
        if op == "+":
            # auto-convert: number+number=math , else concat.
            if isinstance(a,bool):
                a = 1 if a else 0
            if isinstance(b,bool):
                b = 1 if b else 0
            if isinstance(a , (int,float)) and isinstance(b ,(int,float)):
                return a + b
            an , bn = to_number(a), to_number(b)
            if an is not None and bn is not None and isinstance(a,(int,float)) and isinstance(b,str):
                # 5 + "3" -> 8 (friendly math)
                try:
                    return an + bn 
                except Exception:
                    pass
            if an is not None and bn is not None and isinstance(a, str)  and isinstance(b,str):
                # "3" + "5" ->  try maths first? No: strings concat. But if both numeric strings, do maths (easiness)
                try:
                    if "." in a or "." in b:
                        return float(a) + float(b)
                    return int(a) + int(b)
                except Exception:
                    return cat_str(a) + cat_str(b)                
            if isinstance(a, str) or isinstance(b,str):
                # one side string: if other side converts cleanly and string in numeric , do math , else concat
                if isinstance(a, str) and not isinstance(b,str):
                    an2 = to_number(a)
                    if an2 is not None:
                        try: 
                            return an2 + b
                        except Exception:
                            pass
                    return cat_str(a) + cat_str(b)
                if isinstance(b,str) and not isinstance(a,str):
                    bn2 = to_number(b)
                    if bn2 is not None:
                        try:
                            return a + bn2
                        except Exception:
                            pass
                    return cat_str(a) + cat_str(b)
                return cat_str(a) + cat_str(b)
            return cat_str(a) + cat_str(b)
        else: # - 
            an , bn = to_number(a), to_number(b)
            if an is None:
                self.interp.warn(f"cat couldn't subtract '{cat_str(a)}' using 0")
                an = 0
            if bn is None:
                self.interp.warn(f"cat couldn't subtract '{cat_str(b)}' using 0")  
                bn = 0
            return an - bn

    def parse_mul(self):
        v = self.parse_unary()
        while True:
            k, w = self.peek()
            if k == "OP" and w in ("*", "/", "%"):
                self.next()
                r = self.parse_unary()
                v = self.apply_mul(v,w,r)
            else:
                break
        return v
    
    def apply_mul(self, a, op, b):
        an, bn = to_number(a), to_number(b)
        if an is None:
            self.interp.warn(f"cat couldn't multiply '{cat_str(a)}', using 0")
            an = 0
        if bn is None:
            self.interp.warn(f"cat couldn't multiply '{cat_str(b)}', using 0")
            bn = 0
        try:
            if op == "*":
                return an * bn
            if op == "%":
                if bn == 0:
                    self.interp.lose_life("cat tried to divide cookies by zero (modulo)")
                    return 0
                return an % bn
            if op == "/":
                if bn == 0:
                    self.interp.lose_life("cat knocked over the water bowl (division by zero), using 0 instead of infinity")
                    return 0
                res = an / bn
                if isinstance(res, float) and res.is_integer():
                    return int(res)
                return res
        except Exception as e:
            self.interp.lose_life(f"math went wrong ({e})")
            return 0
        return 0
    
    def parse_unary(self):
        k, w = self.peek()
        if k == "ID" and w == "not":
            self.next()
            v = self.parse_unary()
            return not is_truthy(v)
        if k == "OP" and w == "!":
            self.next()
            v = self.parse_unary()
            return not is_truthy(v)
        if k == "OP" and w == "-":
            self.next()
            v = self.parse_unary()
            n = to_number(v)
            if n is None:
                return 0
            return -n
        if k == "OP" and w == "+":
            self.next()
            return self.parse_unary()
        if k == "ID" and w in ("dig", "prophecy"):
            self.next()
            # expect a name next
            k2 , w2 = self.peek()
            if k2 == "ID":
                self.next()
                return self.interp.read_future(w2)
            else:
                self.interp.warn(f"cat expected a toy name after '{w}'")
                return 0 
        return self.parse_primary()

    def parse_primary(self):
        k, w = self.peek()
        if k is None:
            return 0
        if k == "NUM":
            self.next()
            return float(w) if "." in w else int(w)
        if k == "STR":
            self.next()
            # strip quotes, unescape
            q = w[0]
            inner = w[1:-1]
            inner = inner.replace("\\n", "\n").replace("\\t", "\t")
            if q == '"':
                inner = inner.replace('\\"', '"')
            else:
                inner = inner.replace("\\'", "'")
            return inner
        if k == "ID":
            self.next()
            low = w.lower() if w.startswith(("Y", "N")) is False else w
            if w == "yum" or w == "true":
                return True
            if w == "yuck" or w == "false":
                return False
            if w in ("and", "or", "not", "is", "will", "be", "from", "to", "step"):
                self.interp.warn(f"cat found stray word '{w}' in math, using 0")
                return 0
            _attrs = []
            while True:
                _Kdot , _Vdot = self.peek()
                if _Kdot == "OP" and _Vdot == ".":
                    self.next() # consume
                    _ka, _va = self.peek()
                    if _ka == "ID":
                        self.next()
                        _attrs.append(_va)
                    else:
                        self.interp.warn(f"cat expected a name after '.' after '{w}', ignoring '.'")
                        break
                else:
                    break
            if _attrs:
                _k3, _w3 = self.peek()
                if _k3 == "OP" and _w3 == "(":
                    self.next()
                    _pargs = []
                    _kk, _ww = self.peek()
                    if _kk == "OP" and _ww == ")":
                        self.next()
                    else:
                        while True:
                            _a = self.parse_or()
                            _pargs.append(_a)
                            _kk, _ww = self.peek()
                            if _kk == "OP" and _ww == ",":
                                self.next()
                                continue
                            if _kk == "OP" and _ww == ")":
                                self.next()
                                break
                            self.interp.warn(f"cat closed missing ')' for python call '{w}." + ".".join(_attrs) + "' with its tail")
                            break
                        return self.interp.call_python_dotted(w, _attrs, _pargs)
                else:
                    return self.interp.get_python_dotted(w, _attrs)            
            # function call?
            k2, w2 = self.peek()
            if k2 == "OP" and w2 == "(":
                self.next()  # (
                args = []
                # empty args?
                kk, ww = self.peek()
                if kk == "OP" and ww == ")":
                    self.next()
                    return self.interp.call_func(w, args)
                while True:
                    # parse one arg as or-level (no comma crossing)
                    arg = self.parse_or()
                    args.append(arg)
                    kk, ww = self.peek()
                    if kk == "OP" and ww == ",":
                        self.next()
                        continue
                    if kk == "OP" and ww == ")":
                        self.next()
                        break
                    # missing ) -> forgive
                    self.interp.warn(f"cat closed missing ')' for trick '{w}' with its tail")
                    break
                return self.interp.call_func(w, args)
            # plain variable
            return self.interp.get_var(w)
        if k == "OP" and w == "(":
            self.next()
            v = self.parse_or()
            kk, ww = self.peek()
            if kk == "OP" and ww == ")":
                self.next()
            else:
                self.interp.warn("cat closed missing ')' with its tail")
            return v
        # stray operator -> forgive
        self.next()
        self.interp.warn(f"cat ignored stray '{w}' in math")
        return 0

#---------------------------- interpreter ------------------------#

class Interp:
    def __init__(self):
        self.env = [{}]
        self.funcs = {}
        self.history = {}
        self.future_table = {}
        self.future_expr = {}
        self.time_hole = {}
        self.lives = 9
        self.lost = 0
        self.loop_guard = 10000
        self.call_depth = 0
        self.current_file = None
        self.adopted = set()
        self.borrowed_modules = {}

    def warn(self, msg):
        print(f"*mrrp* {msg}" , file=sys.stderr)

    def lose_life(self, reason):
        import random
        excuse = random.choice(CAT_EXCUSES)
        self.lives -= 1
        self.lost += 1
        if self.lives > 0:
            self.warn(f"cat lost a life ({self.lives} left) because it {excuse} [{reason}] - purr-ceeding anyway")
        else:
            self.warn(f"cat is out of lives but immortal for this demo [{reason}] - purr-ceeding anyway (it {excuse})")
            self.lives = 0

    def known_names(self):
        names = set()
        for scope in self.env:
            names.update(scope.keys())
        names.update(self.future_table.keys())
        names.update(self.future_expr.keys())
        names.update(self.time_hole.keys())
        return names
    def get_var(self, name):
        # exact
        for scope in reversed(self.env):
            if name in scope:
                return scope[name]
        # fuzzy varibale mind-readm(hehe)
        known = list(self.known_names())
        if known:            
            m = difflib.get_close_matches(name , known, n=1, cutoff=0.78)
            if m and m[0] != name:
                self.warn(f"cat tilted head... hooman wrote '{name}', cat understood '{m[0]}'")
                return self.get_var(m[0])
        # future fallback (yay)
        if name in self.time_hole:
            self.warn(f"cat dug up '{name}' = {cat_str(self.time_hole[name])} from the time-hole")
            return self.time_hole[name]
        if name in self.future_table:
            self.warn(f"cat stole '{name}' = {cat_str(self.future_table[name])} from the FUTURE (defined later)")
            return self.future_table[name]
        if name in self.future_expr:
            try:
                v = ExprParser(self.future_expr[name], self).parse()
                self.warn(f"cat prophesied '{name}' = {cat_str(v)} from the FUTURE")
                return v
            except Exception:
                pass
        # auto-create (idk if i want this but yeh)
        self.warn(f"cat never saw toy '{name}' before, giving it 0 (new toy)")
        self.env[-1][name] = 0
        self.history.setdefault(name, []).append(0)
        return 0 

    def set_var(self, name, value):
        for scope in reversed(self.env):
            if name in scope:
                scope[name] = value
                self.history.setdefault(name, []).append(value)
                return
        self.env[-1][name] = value
        self.history.setdefault(name, []).append(value)

    def read_future(self, name):
        # dig / prophecy as expression: time_hole > future > current
        for scope in reversed(self.env):
            if name in scope and name in self.time_hole:
                self.warn(f"cat dug up '{name}' from time-hole")
                return self.time_hole[name]
        if name in self.time_hole:
            self.warn(f"cat dug up '{name}' = {cat_str(self.time_hole[name])} from the time-hole")
            return self.time_hole[name]
        # check current first? For prophecy we want future priority to show time travel.
        if name in self.future_table:
            self.warn(f"cat saw '{name}' = {cat_str(self.future_table[name])} in the FUTURE")
            return self.future_table[name]
        if name in self.future_expr:
            try:
                v = ExprParser(self.future_expr[name], self).parse()
                self.warn(f"cat prophesied '{name}' = {cat_str(v)}")
                return v
            except Exception:
                pass
        # fallback to current
        return self.get_var(name)
    
    def eval_expr(self, text):
        text = text.strip()
        if text == "":
            return 0
        try:
            return ExprParser(text, self).parse()
        except RecursionError:
            self.lose_life("cat chased its tail too deep (recursion limit)")
            return 0
        except Exception as e:
            self.lose_life(f"math got tangled ({e})")
            return 0
        
    def call_func(self, name, args):
        # fuzzy trick name?
        if name not in self.funcs:
            known = list(self.funcs.keys())
            m = difflib.get_close_matches(name, known, n=1, cutoff=0.6) if known else []
            if m:
                self.warn(f"cat tilted head... hooman called trick '{name}', cat knows '{m[0]}'")
                name = m[0]
            else:
# -----------------------------------------------------------------                            
                try:
                    _py = None
                    _found = False
                    for _scope in reversed(self.env):
                        if name in _scope:
                            _py = _scope[name]
                            _found = True
                            break
                    if not _found and name in self.borrowed_modules:
                        _py = self.borrowed_modules[name]
                        _found= True
                    if _found and callable(_py):
                        try:
                            return _py(*args)
                        except Exception as _e:
                            self.lose_life(f"python hairball in '{name}(...)' ({_e})")
                            return 0   
                    # also try fuzzy python name
                    if not _found:
                        try:
                            _all_py = set()
                            for _s in self.env:
                                _all_py.update(_s.keys())
                            _all_py.update(self.borrowed_modules.keys())
                            _pm = difflib.get_close_matches(name, list(_all_py), n=1, cutoff=0.78) if _all_py else []
                            if _pm:
                                self.warn(f"cat tilted head... hooman called '{name}', cat knows python '{_pm[0]}'")
                                for _s in reversed(self.env):
                                    try:
                                        return _s[_pm[0]](*args)
                                    except Exception:
                                        pass
                        except Exception:
                            pass
                except Exception:
                    pass                 
# ------------------------------------------------------------------------
                self.lose_life(f"cat never learned trick '{name}', doing nothing")
                return 0
        params, body = self.funcs[name]
        if len(args) < len(params):
            self.warn(f"cat filled {len(params)-len(args)} missing snack(s) with 0 for trick '{name}'")
            args = list(args) + [0] * (len(params) - len(args))
        if len(args) > len(params):
            self.warn(f"cat ignored {len(args)-len(params)} extra snack(s) for trick '{name}'")
            args = args[:len(params)]
        self.call_depth += 1
        if self.call_depth > 400:
            self.call_depth -= 1
            self.lose_life("cat stack overflow (too many zoomies deep)")
            return 0
        self.env.append({})
        for p, a in zip(params, args):
            self.env[-1][p] = a
            self.history.setdefault(p, []).append(a)
        try:
            self.exec_block(body)
        except CatReturn as r:
            self.env.pop()
            self.call_depth -= 1
            return r.value
        except RecursionError:
            self.lose_life("cat chased tail too deep inside trick")
            try:
                self.env.pop()
            except Exception:
                pass
            self.call_depth -= 1
            return 0
        self.env.pop()
        self.call_depth -= 1
        return 0

    # ------- execution --------- 
    def exec_block(self, stmts):
        for st in stmts:
            try:
                self.exec_stmt(st)
            except CatReturn:
                raise
            except RecursionError:
                self.lose_life("cat got dizzy (recursion)")
                continue
            except Exception as e:
                self.lose_life(f"unexpected hairball ({e})")
                continue

    def exec_stmt(self, st):
        t = st["type"]
        if t == "noop":
            return
        if t == "print":
            v = self.eval_expr(st["expr"]) if st["expr"] else ""
            print(cat_str(v))
            return
        if t == "assign":
            v = self.eval_expr(st["expr"])
            self.set_var(st["name"], v)
            return
        if t == "input":
            try:
                raw = input("sniff > ")
            except EOFError:
                self.lose_life("hooman gave no sniff (EOF)")
                raw = ""
            raw = raw.strip()
            if raw == "yum" or raw == "true":
                v = True
            elif raw == "yuck" or raw == "false":
                v = False
            else:
                try:
                    v = int(raw)
                except Exception:
                    try:
                        v = float(raw)
                    except Exception:
                        v = raw
            self.set_var(st["name"], v)
            return
        if t == "if":
            v = self.eval_expr(st["cond"])
            if is_truthy(v):
                self.exec_block(st["then"])
            else:
                done = False
                for (c, b) in st.get("elifs", []):
                    vv = self.eval_expr(c)
                    if is_truthy(vv):
                        self.exec_block(b)
                        done = True
                        break
                if not done and "else" in st and st["else"] is not None:
                    self.exec_block(st["else"])
            return
        if t == "while":
            n = 0
            while is_truthy(self.eval_expr(st["cond"])):
                self.exec_block(st["body"])
                n += 1
                if n > self.loop_guard:
                    self.lose_life("cat got bored chasing tail forever (loop guard), taking a nap")
                    break
            return
        if t == "for":
            a = self.eval_expr(st["start"])
            b = self.eval_expr(st["end"])
            s = self.eval_expr(st["step"]) if st.get("step") else 1
            an, bn, sn = to_number(a), to_number(b), to_number(s)
            if an is None:
                an = 0
            if bn is None:
                bn = 0
            if sn is None or sn == 0:
                self.warn("cat didn't like step 0, using 1")
                sn = 1
            an, bn, sn = int(an), int(bn), int(sn)
            n = 0
            if sn > 0:
                cur = an
                while cur <= bn:
                    self.set_var(st["var"], cur)
                    self.exec_block(st["body"])
                    cur += sn
                    n += 1
                    if n > self.loop_guard:
                        self.lose_life("cat got bored of zoomies (loop guard)")
                        break
            else:
                cur = an
                while cur >= bn:
                    self.set_var(st["var"], cur)
                    self.exec_block(st["body"])
                    cur += sn
                    n += 1
                    if n > self.loop_guard:
                        self.lose_life("cat got bored of zoomies (loop guard)")
                        break
            return
        if t == "funcdef":
            self.funcs[st["name"]] = (st["params"], st["body"])
            return
        if t == "return":
            v = self.eval_expr(st["expr"]) if st["expr"] else 0
            raise CatReturn(v)
        if t == "bury":
            v = self.get_var(st["name"])
            self.time_hole[st["name"]] = v
            self.warn(f"cat buried '{st['name']}' = {cat_str(v)} in the time-hole")
            return
        if t == "dig_stmt":
            v = self.read_future(st["name"])
            self.set_var(st["name"], v)
            self.warn(f"cat dug up '{st['name']}' = {cat_str(v)}")
            return
        if t == "flashback":
            h = self.history.get(st["name"], [])
            if len(h) >= 2:
                prev = h[-2]
                # pop last, set to prev
                self.history[st["name"]].pop()
                self.set_var_direct(st["name"], prev)
                self.warn(f"cat flashbacked '{st['name']}' to {cat_str(prev)}")
            else:
                self.warn(f"cat has no past for '{st['name']}' yet")
            return
        if t == "prophecy_set":
            v = self.eval_expr(st["expr"])
            self.set_var(st["name"], v)
            self.future_table[st["name"]] = v
            self.warn(f"cat prophesied '{st['name']}' will be {cat_str(v)} (sees the future)")
            return
        if t == "prophecy_print":
            v = self.read_future(st["name"])
            print(cat_str(v))
            return
        if t == "lives":
            print(f"cat has {self.lives} lives left. buried: {self.time_hole} future: {self.future_table}")
            return
        if t == "rewind":
            for name, hist in list(self.history.items()):
                if hist:
                    self.set_var_direct(name, hist[0])
            self.warn("cat rewound time to the very first nap (all toys reset to first value)")
            return
        if t == "borrow":
            self.execute_borrow(st.get("modules",[]), st.get("alias", {}))
            return
        if t == "adopt":
            for _mod in st.get("modules",[]):
                self.execute_adopt(_mod)
            return
        if t == "expr":
            self.eval_expr(st["expr"])
            return
        self.warn(f"cat napped through confusing line of type {t}")        

    def set_var_direct(self, name, value):
        for scope in reversed(self.env):
            if name in scope:
                scope[name] = value
                return
        self.env[-1][name] = value

    def execute_borrow(self, modules, alias=None):
        """borrow <python_module>"""
        import importlib
        alias = alias or {}
        for raw in modules:
            mod_name = (raw or "").strip().strip("\"'").strip()
            if not mod_name:
                continue
        # alias support: caller many pass "random as rnd" already split? handle there too
            eff_name = mod_name
            eff_alias = alias.get(mod_name) if isinstance(alias, dict) else None
            if " as " in mod_name:
                try:
                    left, right = [p.strip() for p in mod_name.split(" as ", 1) ]
                    if left and right:
                        eff_name, eff_alias = left, right
                except Exception:
                    pass
            if not eff_alias:
                # default alias = top-level name: "os.path" -> "os"
                eff_alias = eff_name.split(".")[0] if "." in eff_name else eff_name
            # validate: python dotted module name
            import re as _re
            if not _re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*", eff_name):
                self.warn(f"cat didn't understand borrow name '{mod_name}', napping it")
                continue
            # already borrowed? refresh alias anyway
            try:
                mod = importlib.import_module(eff_name)
            except Exception as e:
                self.lose_life(f"cat couldn't borrow python '{eff_name}' ({e})")
                continue
            # attach module object in Mrrp symbole table (for random.randint)
            try:
                self.set_var(eff_alias, mod)
            except Exception:
                try:
                    self.env[-1][eff_alias] = mod
                except Exception:
                    pass
            self.borrowed_modules[eff_alias] = mod
            # also remember full name if different (os.path -> os.path too)
            if eff_name != eff_alias:
                try:
                    self.env[-1][eff_name.split(".")[0]] = importlib.import_module(eff_name.split(".")[0])
                except Exception:
                    pass
                self.borrowed_modules[eff_name] = mod

            try:
                known = self.known_names()
                for attr in dir(mod):
                    if attr.startswith("_"):
                        continue
                    if attr in self.funcs:
                        continue
                    if attr in known:
                        continue
                    try:
                        val = getattr(mod, attr)
                    except Exception:
                        continue
                    # only exposes simple value/callable, skips modules to aboid noise
                    try:
                        self.env[-1].setdefault(attr, val)
                    except Exception:
                        pass        
            except Exception:
                pass
            self.warn(f"cat borrowed python '{eff_name}' as '{eff_alias}' *purr*")
    def _resolve_python_base(self, base_name):
        """Return (found_bool, value). Uses get_var but without auto-creating 0 for module"""
        for scope in reversed(self.env):
            if base_name in scope:
                return True, scope[base_name]
            if base_name in self.borrowed_modules:
                return True, self.borrowed_modules[base_name]
            # fall back to normal get_var (has fuzzy + future + auto-create.) It never raises.
            try:
                v = self.get_var(base_name)
                return True,v
            except Exception:
                return False, 0

    def get_python_dotted(self, base_name, attrs):
        """Implements 'math.pi', 's.upper'(no call). never crashes"""
        try:
            _, cur = self._resolve_python_base(base_name)
        except Exception as e:
            self.lose_life(f"cat couldn't find '{base_name}' for '.{'.'.join(attrs)}' ({e})")
            return 0 
        dotted = base_name
        try:
            for a in attrs:
                dotted += "." + a
                try:
                    cur = getattr(cur, a)
                except Exception:
                    # supports dict-style: cur[a] (for borrowed dicts/json etc. )
                    try:
                        cur = cur[a]
                    except Exception as e2:
                        self.lose_life(f"cat couldn't reach '{dotted}' ({e2})")
                        return 0
            return cur
        except Exception as e:
            self.lose_life(f"cat tripped reaching '{dotted}' ({e})")
            return 0
        
    def call_python_dotted(self, base_name, attrs, args):
        """Implements `random.randint(1,6)`, `s.upper()`, `builtins.str.join(...)`."""
        try:
            _, cur = self._resolve_python_base(base_name)
        except Exception as e:
            self.lose_life(f"cat couldn't find '{base_name}' for call ({e})")
            return 0
        dotted = base_name
        try:
            for a in attrs[:-1]:
                dotted += "." + a
                try:
                    cur = getattr(cur, a)
                except Exception:
                    try:
                        cur = cur[a]
                    except Exception as e2:
                        self.lose_life(f"cat couldn't reach '{dotted}' ({e2})")
                        return 0
            last = attrs[-1] if attrs else ""
            if last:
                dotted += "." + last
                try:
                    fn = getattr(cur, last)
                except Exception:
                    try:
                        fn = cur[last]
                    except Exception as e2:
                        self.lose_life(f"cat couldn't find trick '{dotted}' ({e2})")
                        return 0
            else:
                fn = cur
            # if fn is not callable but args were given like `x(...)` where x is int? oracle forgive
            if not callable(fn):
                # allow `paw x = 5` then `x()`? -> just return value, warn
                if len(args) == 0:
                    return fn
                self.lose_life(f"cat tried to call non-trick '{dotted}' (it's {type(fn).__name__})")
                return 0
            try:
                res = fn(*args)
            except Exception as e:
                self.lose_life(f"python hairball in '{dotted}({', '.join([cat_str(a) for a in args])})' ({e})")
                return 0
            return res
        except Exception as e:
            self.lose_life(f"cat tripped calling '{base_name}.{'.'.join(attrs)}' ({e})")
            return 0

    def execute_adopt(self, raw_name):
        """adopt <name> — import-like for .mrrp files. Never crashes (oracle).

        search_paths = [
            dirname(current_file),  # local folder
            cwd,
            dirname(mrrp.py)/cat_pack,  # stdlib folder
            dirname(mrrp.py)/lib,       # alias stdlib folder
        ]
        Executes file with CURRENT interpreter so tricks/paws land in scope.
        visited set prevents double-import / infinite loops.
        """
        import os as _os
        name = (raw_name or "").strip().strip("\"'").strip()
        if not name:
            return
        # allow `adopt foo.mrrp` or `adopt foo`
        if name.lower().endswith(".mrrp"):
            name = name[:-5]
        # strip any directory bits? keep subpaths: adopt sub/foo allowed
        if "/" in name or "\\" in name:
            # path-like adopt: resolve relative to current_file/cwd
            candidates = []
            if self.current_file:
                candidates.append(_os.path.join(_os.path.dirname(_os.path.abspath(self.current_file)), name + ".mrrp"))
                candidates.append(_os.path.join(_os.path.dirname(_os.path.abspath(self.current_file)), name))
            candidates.append(_os.path.join(_os.getcwd(), name + ".mrrp"))
            candidates.append(_os.path.join(_os.getcwd(), name))
            found = None
            for c in candidates:
                if _os.path.isfile(c):
                    found = c
                    break
            if not found:
                self.lose_life(f"cat couldn't find friend '{raw_name}.mrrp' to adopt")
                return
            self._adopt_file(found)
            return
        # simple module name
        import re as _re
        if not _re.fullmatch(r"[A-Za-z_][A-Za-z0-9_\-]*", name):
            self.warn(f"cat didn't understand adopt name '{raw_name}', napping it")
            return
        search_dirs = []
        if self.current_file:
            try:
                search_dirs.append(_os.path.dirname(_os.path.abspath(self.current_file)))
            except Exception:
                pass
        try:
            search_dirs.append(_os.getcwd())
        except Exception:
            pass
        
        # also: cat_pack next to current_file (project-local stdlib)
        if self.current_file:
            try:
                search_dirs.insert(1, _os.path.join(_os.path.dirname(_os.path.abspath(self.current_file)), "cat_pack"))
                search_dirs.insert(2, _os.path.join(_os.path.dirname(_os.path.abspath(self.current_file)), "lib"))
            except Exception:
                pass
        try:
            search_dirs.extend(_power_stdlib_dirs())
        except Exception:
            try:
                me_dir = _os.path.dirname(_os.path.abspath(__file__))
            except Exception:
                me_dir = _os.getcwd()
            search_dirs.append(_os.path.join(me_dir, "cat_pack"))
            search_dirs.append(_os.path.join(me_dir, "lib"))    


        found = None
        for d in search_dirs:
            for cand in (_os.path.join(d, name + ".mrrp"), _os.path.join(d, name)):
                try:
                    if _os.path.isfile(cand):
                        found = cand
                        break
                except Exception:
                    continue
            if found:
                break
        if not found:
            self.lose_life(f"cat couldn't find friend '{name}.mrrp' to adopt (looked in {search_dirs})")
            return
        self._adopt_file(found)

    def _adopt_file(self, abspath):
        import os as _os
        try:
            key = _os.path.abspath(abspath)
        except Exception:
            key = abspath
        if key in self.adopted:
            self.warn(f"cat already adopted '{_os.path.basename(key)}', skipping (no infinite zoomies)")
            return
        self.adopted.add(key)
        try:
            with open(key, "r", encoding="utf-8") as f:
                src = f.read()
        except Exception as e:
            self.lose_life(f"cat couldn't read adopted file '{key}' ({e})")
            return
        old_file = self.current_file
        self.current_file = key
        self.warn(f"cat adopted '{_os.path.basename(key)}' *happy purr*")
        try:
            lines = preprocess(src, self)
            prescan(lines, self)
            parser = StmtParser(lines, self)
            prog = parser.parse_program()
            try:
                opens = sum(1 for L in lines if L.strip().endswith("{"))
                closes = sum(1 for L in lines if L.strip() == "}")
                if opens > closes:
                    self.warn(f"cat closed {opens-closes} missing '}}' with its tail (in {key})")
            except Exception:
                pass
            self.exec_block(prog)
        except CatReturn:
            # fetch as top -level of adopted file? just ignore , restore file
            pass
        except Exception as e:
            self.lose_life(f"adopted file '{key}' had a hairball ({e})")
        finally:
            self.current_file = old_file               


# ---------------------------- source preprocessing ----------------------------- #

def strip_inline_comment(line):
    # strip # or // comments outside strings
    out = []
    i = 0
    in_s = None
    while i < len(line):
        c = line[i]
        if in_s:
            out.append(c)
            if c == "\\" and i + 1 < len(line):
                out.append(line[i + 1])
                i += 2
                continue
            if c == in_s:
                in_s = None
            i += 1
            continue
        if c in ('"', "'"):
            in_s = c
            out.append(c)
            i += 1
            continue
        if c == "#" :
            break
        if c == "/" and i + 1 < len(line) and line[i + 1] == "/":
            break
        # ~ full-line handled elsewhere; inline ~ as comment too
        out.append(c)
        i += 1
    return "".join(out)
def fuzzy_first_word(line, interp_warn):
    m = re.match(r"\s*([A-Za-z_][A-Za-z0-9_\-]*)(.*)$", line)
    if not m:
        return line
    first, rest = m.group(1), m.group(2)
    low = first
    if first in KEYWORDS:
        return line
    # don't fuzzy variable assignments like "x = 5" (x not keyword, that's fine)
    # only fuzzy if close to a keyword AND line looks like a keyword-led statement
    cand = difflib.get_close_matches(first, KEYWORDS, n=1, cutoff=0.62)
    if cand:
        # avoid correcting legit variable names that happen to be close:
        # if rest starts with = or is <expr> and first is short var, be careful.
        # Heuristic: if first is <=3 chars and rest looks like assignment, keep it.
        rst = rest.strip()
        looks_assign = rst.startswith("=") or rst.startswith("is ") or rst.startswith("is\t")
        if looks_assign and len(first) <= 4 and first not in ("meow", "paw"):
            # Could still be "paw" typo? paw is 3 chars. Check: if cand is paw/purr etc and first close, correct anyway if very close?
            m2 = difflib.get_close_matches(first, KEYWORDS, n=1, cutoff=0.8)
            if not m2:
                return line
            # fall through to correct with high confidence
        new_first = cand[0]
        interp_warn(f"cat tilted head... hooman wrote '{first}', cat understood '{new_first}'")
        return new_first + rest
    return line
def preprocess(source, interp):
    lines = source.splitlines()
    out = []
    for idx, raw in enumerate(lines):
        line = raw.rstrip("\n")
        s = line.strip()
        if s == "" or s.startswith("~") or s.startswith("#"):
            continue
        # full-line // comment
        if s.startswith("//"):
            continue
        # auto-close quotes (): count unescaped quotes
        tmp = strip_inline_comment(line)
        # count " and '
        def odd_quotes(q):
            c = 0
            esc = False
            in_o = None
            for ch in tmp:
                if in_o is not None and in_o != q:
                    if ch == "\\":
                        esc = not esc
                    else:
                        esc = False
                    if ch == in_o and not esc:
                        in_o = None
                    continue
                if ch == "\\":
                    continue
                if ch == q:
                    if in_o == q:
                        in_o = None
                    else:
                        # only count if not inside other string - simplified: toggle
                        c += 1
            return c % 2 == 1
        # simpler: count occurrences outside opposite string? use quick heuristic
        n_dq = tmp.count('"') - tmp.count('\\"')
        n_sq = tmp.count("'") - tmp.count("\\'")
        fixed = tmp
        if n_dq % 2 == 1:
            interp.warn(f"line {idx+1}: cat closed missing \" with its tail")
            fixed += '"'
        elif n_sq % 2 == 1:
            interp.warn(f"line {idx+1}: cat closed missing ' with its tail")
            fixed += "'"
        line2 = fixed
        # fuzzy first word
        line2 = fuzzy_first_word(line2, interp.warn)
        # second word fuzzy for "hiss purr" (elif): "hiss pur" etc.
        m = re.match(r"\s*hiss\s+([A-Za-z_][A-Za-z0-9_\-]*)(.*)$", line2)
        if m:
            second, rest2 = m.group(1), m.group(2)
            if second != "purr":
                cand = difflib.get_close_matches(second, ["purr"], n=1, cutoff=0.6)
                if cand and second.lower() not in ("{", "", "purr"):
                    # only if rest looks like condition (not empty and not just { )
                    if rest2.strip() != "" and rest2.strip() != "{":
                        interp.warn(f"cat tilted head... hooman wrote 'hiss {second}', cat understood 'hiss purr'")
                        line2 = re.sub(r"\s*hiss\s+[A-Za-z_][A-Za-z0-9_\-]*",
                                       "hiss purr", line2, count=1)
        out.append(line2)
    # split braces into own lines (protect strings)
    joined = "\n".join(out)
    # protect strings with placeholders
    strs = []
    def repl(m):
        strs.append(m.group(0))
        return f"\x00{len(strs)-1}\x00"
    prot = re.sub(r'"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'', repl, joined)
    prot = prot.replace("{", "\n{\n").replace("}", "\n}\n")
    parts = [p.strip() for p in prot.splitlines()]
    # restore strings
    final = []
    for p in parts:
        if p == "":
            continue
        def back(m):
            return strs[int(m.group(1))]
        p2 = re.sub("\x00(\\d+)\x00", back, p)
        final.append(p2)
    # re-join attached block openers: e.g. "purr x" + "{" -> "purr x {"
    merged = []
    i = 0
    while i < len(final):
        cur = final[i]
        if i + 1 < len(final) and final[i + 1] == "{" and not cur.endswith("{") and cur != "}" and cur != "{":
            # block opener without brace -> merge
            merged.append(cur + " {")
            i += 2
        else:
            merged.append(cur)
            i += 1
    # auto-add missing { for block openers
    block_open = re.compile(r"^\s*(purr|hiss|chase|zoomies|trick)\b", re.IGNORECASE)
    # after fuzzy, keywords are lowercase-correct; keep case-insensitive anyway
    res = []
    for ln in merged:
        if ln in ("{", "}"):
            res.append(ln)
            continue
        if block_open.match(ln) and not ln.rstrip().endswith("{"):
            interp.warn(f"cat added missing '{{' with its tail: {ln.strip()}")
            res.append(ln + " {")
        else:
            res.append(ln)
    # warn about hiss without purr later at parse; auto-close } handled at parse
    return res

def prescan(lines, interp):
    for line in lines:
        s = line.strip()
        if s in ("{", "}"):
            continue
        # paw NAME = literal / is literal
        m = re.match(r"""paw\s+([A-Za-z_][A-Za-z0-9_\-]*)\s*(?:=|is)\s*(.+?)\s*\{?\s*$""", s)
        if m:
            name, rhs = m.group(1), m.group(2).strip().rstrip("{").strip()
            if re.fullmatch(r'-?\d+(\.\d+)?', rhs):
                interp.future_table.setdefault(name, float(rhs) if "." in rhs else int(rhs))
                interp.future_expr.setdefault(name, rhs)
            elif re.fullmatch(r'"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'', rhs):
                q = rhs[0]
                inner = rhs[1:-1]
                interp.future_table.setdefault(name, inner)
                interp.future_expr.setdefault(name, rhs)
            elif rhs in ("yum", "true"):
                interp.future_table.setdefault(name, True)
                interp.future_expr.setdefault(name, rhs)
            elif rhs in ("yuck", "false"):
                interp.future_table.setdefault(name, False)
                interp.future_expr.setdefault(name, rhs)
            else:
                # general future expr (last wins for dig-from-future)(hehe)
                interp.future_expr[name] = rhs
            continue
        # bare assign NAME = rhs (for future fallback)
        m2 = re.match(r"""([A-Za-z_][A-Za-z0-9_\-]*)\s*=\s*(.+?)\s*\{?\s*$""", s)
        if m2:
            name, rhs = m2.group(1), m2.group(2).strip().rstrip("{").strip()
            if name not in ("==", "=", "!=") and name not in KEYWORDS:
                if name not in interp.future_expr:
                    interp.future_expr[name] = rhs
                else:
                    interp.future_expr[name] = rhs
            continue
        m3 = re.match(r"""prophecy\s+([A-Za-z_][A-Za-z0-9_\-]*)\s+will\s+be\s*(.+?)\s*$""", s)
        if m3:
            name, rhs = m3.group(1), m3.group(2).strip()
            interp.future_expr[name] = rhs
            # literal -> table too
            if re.fullmatch(r'-?\d+(\.\d+)?', rhs):
                interp.future_table.setdefault(name, float(rhs) if "." in rhs else int(rhs))
            elif re.fullmatch(r'"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'', rhs):
                interp.future_table.setdefault(name, rhs[1:-1])
            continue

# ------------------------- statement parser -------------------------- # (hehe now this is my fav part in making a programming language meow mrrp)
class StmtParser:
    def __init__(self, lines, interp):
        self.lines = lines
        self.pos = 0
        self.interp = interp

    def peek(self):
        if self.pos < len(self.lines):
            return self.lines[self.pos]
        return None

    def next(self):
        v = self.peek()
        self.pos += 1
        return v
    
    def parse_program(self):
        stmts, _ = self.parse_block(top=True)
        if self.pos < len(self.lines):
            self.interp.warn("cat ignored extra '}' (too many)")
        return stmts

    def parse_block(self, top=False):
        stmts = []
        while self.pos < len(self.lines):
            line = self.peek().strip()
            if line == "":
                self.next()
                continue
            if line == "}":
                if top:
                    self.interp.warn("cat ignored stray '}'")
                    self.next()
                    continue
                self.next()  # consume close
                # check for hiss-chaining: "} hiss {" was split into "}", "hiss {", so caller handles hiss after return.
                return stmts, True
            if line == "{":
                self.interp.warn("cat ignored stray '{'")
                self.next()
                continue
            # hiss at block start without parent if -> warn as stray else
            if re.match(r"^hiss\b", line) and not stmts:
                # stray hiss at top of this block; treat as its own if? Better: parse as else-less -> warn + parse body anyway
                self.interp.warn("cat found lonely 'hiss' with no 'purr', napping it into a 'purr yum'")
                # convert to purr yum
                line = re.sub(r"^hiss\b", "purr yum", line, count=1)
                self.lines[self.pos] = line
            st = self.parse_stmt()
            if st is None:
                continue
            # attach hiss / hiss purr chains to preceding purr
            if st["type"] in ("hiss_alone", "elif_alone"):
                prev = None
                for s in reversed(stmts):
                    if s["type"] == "if":
                        prev = s
                        break
                if prev is None:
                    self.interp.warn("cat found lonely 'hiss' with no 'purr', ignoring")
                    # execute its body anyway as plain block to not lose code
                    stmts.extend(st["body"])
                else:
                    if st["type"] == "hiss_alone":
                        if prev.get("else") is not None:
                            self.interp.warn("cat found double 'hiss', keeping first")
                        else:
                            prev["else"] = st["body"]
                    else:
                        prev.setdefault("elifs", []).append((st["cond"], st["body"]))
                continue
            stmts.append(st)
        if not top:
            pass
        return stmts, False
    
    def parse_stmt(self):
        raw = self.next()
        line = raw.strip()
        low = line
        # mrrp header / nap
        if re.match(r"^mrrp\b", line):
            return {"type": "noop"}
        if re.match(r"^nap\b", line):
            return {"type": "noop"}
        if line == "lives":
            return {"type": "lives"}
        if line == "rewind":
            return {"type": "rewind"}
## --------------------------------------------------------------------
        _m = re.match(r"^borrow\s+(.+?)\s*\{?\s*$", line)
        if _m or line.strip() == "borrow":
            _rest = _m.group(1).strip() if _m else ""
            _rest = _rest.rstrip("{").strip()
            _mods = []
            if _rest == "":
                self.interp.warn("cat didn't see what to borrow, napping")
            else:
                # split by comma, keep `X as Y` together, else split spaces
                for _chunk in _rest.split(","):
                    _chunk = _chunk.strip()
                    if not _chunk:
                        continue
                    if " as " in _chunk:
                        _mods.append(_chunk)
                    else:
                        for _p in _chunk.split():
                            _p = _p.strip().strip("\"'").strip()
                            if _p and _p not in ("{", "}"):
                                _mods.append(_p)
            return {"type": "borrow", "modules": _mods, "alias": {}}
        # adopt <name> [, more]  e.g. adopt math_cat / adopt math, strings
        _m2 = re.match(r"^adopt\s+(.+?)\s*\{?\s*$", line)
        if _m2 or line.strip() == "adopt":
            _rest2 = _m2.group(1).strip() if _m2 else ""
            _rest2 = _rest2.rstrip("{").strip()
            _mods2 = []
            if _rest2 == "":
                self.interp.warn("cat didn't see who to adopt, napping")
            else:
                for _chunk in _rest2.split(","):
                    _chunk = _chunk.strip()
                    if not _chunk:
                        continue
                    for _p in _chunk.split():
                        _p = _p.strip().strip("\"'").strip()
                        if _p and _p not in ("{", "}"):
                            # allow `adopt foo.mrrp`
                            _mods2.append(_p)
            return {"type": "adopt", "modules": _mods2}
## ----------------------------------------------------------------------------------------        
        # prophecy set: prophecy NAME will be EXPR
        m = re.match(r"^prophecy\s+([A-Za-z_][A-Za-z0-9_\-]*)\s+will\s+be\s*(.*)$", line)
        if m:
            name, expr = m.group(1), m.group(2).strip()
            expr = expr.rstrip("{").strip()
            if expr == "":
                expr = "0"
                self.interp.warn(f"cat guessed prophecy for '{name}' is 0")
            return {"type": "prophecy_set", "name": name, "expr": expr}
        # prophecy print: prophecy NAME
        m = re.match(r"^prophecy\s+([A-Za-z_][A-Za-z0-9_\-]*)\s*$", line)
        if m:
            return {"type": "prophecy_print", "name": m.group(1)}
        # bury
        m = re.match(r"^bury\s+([A-Za-z_][A-Za-z0-9_\-]*)\s*$", line)
        if m:
            return {"type": "bury", "name": m.group(1)}
        # dig stmt: dig NAME (also usable in expr, but bare line = restore)
        m = re.match(r"^dig\s+([A-Za-z_][A-Za-z0-9_\-]*)\s*$", line)
        if m:
            return {"type": "dig_stmt", "name": m.group(1)}
        # flashback
        m = re.match(r"^flashback\s+([A-Za-z_][A-Za-z0-9_\-]*)\s*$", line)
        if m:
            return {"type": "flashback", "name": m.group(1)}
        # meow
        m = re.match(r"^meow\b(.*)$", line)
        if m:
            expr = m.group(1).strip()
            # meow { -> stray brace already split, so expr may be "" -> print blank
            return {"type": "print", "expr": expr}
        # sniff
        m = re.match(r"^sniff\s+([A-Za-z_][A-Za-z0-9_\-]*)\s*$", line)
        if m:
            return {"type": "input", "name": m.group(1)}
        # fetch
        m = re.match(r"^fetch\b(.*)$", line)
        if m:
            return {"type": "return", "expr": m.group(1).strip()}
        # trick NAME(params) {
        m = re.match(r"^trick\s+([A-Za-z_][A-Za-z0-9_\-]*)\s*\((.*)\)\s*\{\s*$", line)
        if m:
            name, params_s = m.group(1), m.group(2).strip()
            params = []
            if params_s != "":
                params = [p.strip() for p in params_s.split(",") if p.strip() != ""]
            body, _ = self.parse_block(top=False)
            # unclosed blocks are auto-closed later with a warning
            return {"type": "funcdef", "name": name, "params": params, "body": body}
        # trick without parens: trick NAME {
        m = re.match(r"^trick\s+([A-Za-z_][A-Za-z0-9_\-]*)\s*\{\s*$", line)
        if m:
            name = m.group(1)
            body, _ = self.parse_block(top=False)
            return {"type": "funcdef", "name": name, "params": [], "body": body}
        # purr COND {
        m = re.match(r"^purr\b(.*)\{\s*$", line)
        if m:
            cond = m.group(1).strip()
            if cond == "":
                cond = "yum"
                self.interp.warn("cat guessed empty 'purr' means 'purr yum'")
            body, _ = self.parse_block(top=False)
            return {"type": "if", "cond": cond, "then": body, "elifs": [], "else": None}
        # hiss purr COND {
        m = re.match(r"^hiss\s+purr\b(.*)\{\s*$", line)
        if m:
            cond = m.group(1).strip() or "yum"
            body, _ = self.parse_block(top=False)
            return {"type": "elif_alone", "cond": cond, "body": body}
        # hiss {
        m = re.match(r"^hiss\s*\{\s*$", line)
        if m:
            body, _ = self.parse_block(top=False)
            return {"type": "hiss_alone", "body": body}
        # chase COND {
        m = re.match(r"^chase\b(.*)\{\s*$", line)
        if m:
            cond = m.group(1).strip() or "yuck"
            body, _ = self.parse_block(top=False)
            return {"type": "while", "cond": cond, "body": body}
        # zoomies VAR from A to B [step C] {
        m = re.match(r"^zoomies\s+([A-Za-z_][A-Za-z0-9_\-]*)\s+from\b(.*)\{\s*$", line)
        if m:
            var, rest = m.group(1), m.group(2).strip()
            # rest like "1 to 10" or "1 to 10 step 2" or exprs
            mm = re.match(r"(.+?)\s+to\s+(.+)", rest)
            if not mm:
                self.interp.warn(f"cat didn't get zoomies range '{rest}', using 1 to 3")
                body, _ = self.parse_block(top=False)
                return {"type": "for", "var": var, "start": "1", "end": "3", "step": "1", "body": body}
            s_expr, e_rest = mm.group(1).strip(), mm.group(2).strip()
            step = "1"
            mstep = re.match(r"(.+?)\s+step\s+(.+)", e_rest)
            if mstep:
                e_expr, step = mstep.group(1).strip(), mstep.group(2).strip()
            else:
                e_expr = e_rest
            body, _ = self.parse_block(top=False)
            return {"type": "for", "var": var, "start": s_expr, "end": e_expr, "step": step, "body": body}
        # paw NAME = EXPR / paw NAME is EXPR / paw NAME EXPR (forgive) / paw NAME
        m = re.match(r"^paw\s+([A-Za-z_][A-Za-z0-9_\-]*)\s*(?:=|is)\s*(.*)$", line)
        if m:
            name, expr = m.group(1), m.group(2).strip()
            expr = expr.rstrip("{").strip()
            if expr == "":
                expr = "0"
            return {"type": "assign", "name": name, "expr": expr}
        m = re.match(r"^paw\s+([A-Za-z_][A-Za-z0-9_\-]*)\s*$", line)
        if m:
            return {"type": "assign", "name": m.group(1), "expr": "0"}
        m = re.match(r"^paw\s+([A-Za-z_][A-Za-z0-9_\-]*)\s+(.+)$", line)
        if m:
            # missing = : paw x 5
            self.interp.warn(f"cat added missing '=' with its tail: paw {m.group(1)} = {m.group(2).strip()}")
            return {"type": "assign", "name": m.group(1), "expr": m.group(2).strip()}
        # bare assign: NAME = EXPR / NAME is EXPR
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_\-]*)\s*=\s*(.*)$", line)
        if m and m.group(2) != "" or (m and "=" in line):
            name, expr = m.group(1), m.group(2).strip()
            if name in KEYWORDS:
                pass
            else:
                if expr == "":
                    expr = "0"
                return {"type": "assign", "name": name, "expr": expr}
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_\-]*)\s+is\s+(.*)$", line)
        if m:
            name, expr = m.group(1), m.group(2).strip()
            if name not in KEYWORDS:
                return {"type": "assign", "name": name, "expr": expr}
        # fallback: expression statement (func call etc.) or nap
        # if it looks like gibberish with spaces and no known structure, nap it
        if re.match(r"^[A-Za-z_]", line) and "(" not in line and "=" not in line and len(line.split()) > 4:
            self.interp.warn(f"cat napped through confusing line: {line.strip()} (treated as nap)")
            return {"type": "noop"}
        return {"type": "expr", "expr": line}


def run_source(source, interp=None, filename=None):
    if interp is None:
        interp = Interp()
    # ---------- [POWER PACK] track current file ----------
    import os as _os
    _old_file = interp.current_file
    if filename:
        try:
            interp.current_file = _os.path.abspath(filename)
            # prevent `adopt self` infinite loop: mark main file as adopted
            interp.adopted.add(_os.path.abspath(filename))
        except Exception:
            interp.current_file = filename
    # --------------------
    lines = preprocess(source, interp)
    prescan(lines, interp)
    parser = StmtParser(lines, interp)
    prog = parser.parse_program()
    # auto-close check: parser consumes all; if lines had unclosed blocks, parse_block(top=True) would just end.
    # Detect unbalanced by counting: if original had more opens than closes, warn.
    opens = sum(1 for L in lines if L.strip().endswith("{"))
    # closes consumed; rough check via parser pos? parse_program consumes all, so if opens>0 and no '}' lines, it auto-closed.
    closes = sum(1 for L in lines if L.strip() == "}")
    if opens > closes:
        interp.warn(f"cat closed {opens-closes} missing '}}' with its tail")
    interp.exec_block(prog)
    # restore (for REPL snippets filename=None keeps old file)
    if filename:
        interp.current_file = _old_file
    return interp

# yay ! we are to main yeh mrrrrp

def main():
    if len(sys.argv) == 1:
        print("mrrp 0.1.9 - the cat that remembers the future. type nap to rest, lives to check lives.")  # idk why i used the version number just idk, leave it does not matters.
        interp = Interp()
        buf = ""
        depth = 0
        while True:
            try:
                prompt = "mrrp> " if depth == 0 else "....> "
                line = input(prompt)
            except EOFError:
                print("\ncat naps. bye. *mrrp*")
                break
            except KeyboardInterrupt:
                print("\ncat naps. bye. *mrrp*")
                break
            if line.strip() == "":
                continue
            buf += line + "\n"
            depth += buf.count("{") - buf.count("}")
            if depth > 0:
                continue
            try:
                run_source(buf, interp)
            except CatReturn:
                pass
            except Exception as e:
                interp.lose_life(f"repl hairball ({e})")
            buf = ""
            depth = 0
        return
    path = sys.argv[1]
    try:
        with open(path, "r", encoding="utf-8") as f:
            src = f.read()
    except Exception as e:
        print(f"cat couldn't find file '{path}' ({e})", file=sys.stderr)
        sys.exit(1)
    interp = Interp()
    try:        
        run_source(src, interp, filename=path) # for new features ... yay!
    except CatReturn:
        pass
    except RecursionError:
        interp.lose_life("cat chased tail too deep at top level")
    except Exception as e:
        interp.lose_life(f"top-level hairball ({e})")
    
if __name__ == "__main__":
    main()     # yay completed !!