import streamlit as st
import re
import io
import sys

# =========================
# LEXER
# =========================
TOKEN_SPEC = [
    ('NUMBER',   r'\d+'),
    ('ASSIGN',   r'<-'),
    ('MOD',      r'%%'),
    ('LE',       r'<='),
    ('GE',       r'>='),
    ('LT',       r'<'),
    ('GT',       r'>'),
    ('NE',       r'!='),
    ('EQ',       r'=='),
    ('PLUS',     r'\+'),
    ('MINUS',    r'-'),
    ('MULT',     r'\*'),
    ('DIV',      r'/'),
    ('LPAREN',   r'\('),
    ('RPAREN',   r'\)'),
    ('LBRACE',   r'\{'),
    ('RBRACE',   r'\}'),
    ('COMMA',    r','),
    ('STRING',   r'"[^"]*"'),
    ('ID',       r'[a-zA-Z_]\w*'),
    ('SKIP',     r'[ \t]+'),
    ('NEWLINE',  r'\n'),
]

def lexer(code):
    tokens = []
    pos = 0
    while pos < len(code):
        match = None
        for tok, pat in TOKEN_SPEC:
            reg = re.compile(pat)
            m = reg.match(code, pos)
            if m:
                txt = m.group(0)
                if tok not in ("SKIP","NEWLINE"):
                    tokens.append((tok,txt))
                pos = m.end()
                match = True
                break
        if not match:
            raise SyntaxError("Illegal char: "+code[pos])
    return tokens


# =========================
# INTERPRETER
# =========================
class Interpreter:
    def __init__(self,tokens):
        self.tokens=tokens
        self.pos=0
        self.env={}

    def cur(self):
        return self.tokens[self.pos] if self.pos<len(self.tokens) else None

    def eat(self,t):
        if self.cur()[0]==t:
            self.pos+=1
        else:
            raise SyntaxError("Unexpected token")

    def run(self):
        while self.pos<len(self.tokens):
            self.stmt()

    def stmt(self):
        if self.cur()[1]=="print":
            self.print_stmt()
        elif self.cur()[1]=="cat":
            self.cat_stmt()
        elif self.cur()[1]=="if":
            self.if_stmt()
        elif self.cur()[1]=="while":
            self.while_stmt()
        else:
            self.assign()

    def assign(self):
        v=self.cur()[1]; self.eat("ID")
        self.eat("ASSIGN")
        val=self.expr()
        self.env[v]=val

    def print_stmt(self):
        self.eat("ID"); self.eat("LPAREN")
        txt=self.cur()[1][1:-1]
        self.eat("STRING"); self.eat("RPAREN")
        print(txt)

    def cat_stmt(self):
        self.eat("ID"); self.eat("LPAREN")
        out=[]
        while self.cur()[0]!="RPAREN":
            if self.cur()[0]=="STRING":
                out.append(self.cur()[1][1:-1])
                self.eat("STRING")
            else:
                out.append(str(self.env[self.cur()[1]]))
                self.eat("ID")
            if self.cur()[0]=="COMMA":
                self.eat("COMMA")
        self.eat("RPAREN")
        print("".join(out),end="")

    def if_stmt(self):
        self.eat("ID"); self.eat("LPAREN")
        cond=self.condition()
        self.eat("RPAREN")
        self.eat("LBRACE")
        if cond:
            while self.cur()[0]!="RBRACE":
                self.stmt()
        else:
            while self.cur()[0]!="RBRACE":
                self.pos+=1
        self.eat("RBRACE")
        if self.cur() and self.cur()[1]=="else":
            self.eat("ID"); self.eat("LBRACE")
            if not cond:
                while self.cur()[0]!="RBRACE":
                    self.stmt()
            else:
                while self.cur()[0]!="RBRACE":
                    self.pos+=1
            self.eat("RBRACE")

    def while_stmt(self):
        self.eat("ID"); self.eat("LPAREN")
        start=self.pos
        cond_pos=start
        cond=self.condition()
        self.eat("RPAREN"); self.eat("LBRACE")
        body_start=self.pos
        while cond:
            self.pos=body_start
            while self.cur()[0]!="RBRACE":
                self.stmt()
            self.pos=cond_pos
            cond=self.condition()
        while self.cur()[0]!="RBRACE":
            self.pos+=1
        self.eat("RBRACE")

    def condition(self):
        a=self.expr()
        op=self.cur()[0]; self.pos+=1
        b=self.expr()
        return {
            "LT":a<b,"GT":a>b,"LE":a<=b,"GE":a>=b,
            "EQ":a==b,"NE":a!=b
        }[op]

    def expr(self):
        r=self.term()
        while self.cur() and self.cur()[0] in ("PLUS","MINUS"):
            if self.cur()[0]=="PLUS":
                self.eat("PLUS"); r+=self.term()
            else:
                self.eat("MINUS"); r-=self.term()
        return r

    def term(self):
        r=self.factor()
        while self.cur() and self.cur()[0] in ("MULT","DIV","MOD"):
            if self.cur()[0]=="MULT":
                self.eat("MULT"); r*=self.factor()
            elif self.cur()[0]=="DIV":
                self.eat("DIV"); r/=self.factor()
            else:
                self.eat("MOD"); r%=self.factor()
        return r

    def factor(self):
        if self.cur()[0]=="NUMBER":
            v=int(self.cur()[1])
            self.eat("NUMBER")
            return v
    
        elif self.cur()[0]=="LPAREN":
            self.eat("LPAREN")
            v=self.expr()
            self.eat("RPAREN")
            return v
    
        elif self.cur()[0]=="ID":
            name=self.cur()[1]
            if name not in self.env:
                raise RuntimeError(f"Variable '{name}' not defined")
            v=self.env[name]
            self.eat("ID")
            return v


# =========================
# STREAMLIT UI
# =========================
st.title("📘 Mini R Interpreter - 4 Soal")

tab1,tab2,tab3,tab4=st.tabs(["Soal 1","Soal 2","Soal 3","Soal 4"])

def run(code):
    buf=io.StringIO()
    sys.stdout=buf
    t=lexer(code)
    Interpreter(t).run()
    sys.stdout=sys.__stdout__
    return buf.getvalue()

# -------------------------
# SOAL 1
with tab1:
    st.header("Print & Cat")
    code=st.text_area("",'''print("Hello, world!")
cat("Thanks")''',200)
    if st.button("Run Soal 1"):
        st.code(run(code))

# -------------------------
# SOAL 2
with tab2:
    st.header("Arithmetic")
    code=st.text_area("",'''num1 <- 10
num2 <- 20
num3 <- 30
sum <- num1+num2+num3
avg <- sum / 3
cat("num1 is ", num1, "\\n")
cat("num2 is ", num2, "\\n")
cat("num3 is ", num3, "\\n")
cat("Sum 3 numbers is ", sum, "\\n")
cat("Average is ", avg, "\\n")''',300)
    if st.button("Run Soal 2"):
        st.code(run(code))

# -------------------------
# SOAL 3
with tab3:
    st.header("IF ELSE")
    code=st.text_area("",'''num1 <- 10
num2 <- 20
if (num1>num2) {
 bignum <- num1
 cat("Big Number is ", bignum, "\\n")
} else {
 bignum <- num2
 cat("Big Number is ", bignum, "\\n")
}''',300)
    if st.button("Run Soal 3"):
        st.code(run(code))

# -------------------------
# SOAL 4
with tab4:
    st.header("Loop + IF")
    code=st.text_area("",'''cat("List of Odd Number 1-100:\\n")
num<-1
while (num <= 100) {
 sisa <- (num %% 2)
 if (sisa != 0) {
  oddnum <- num
  cat(oddnum," ")
 }
 num <- num + 1
}''',350)
    if st.button("Run Soal 4"):
        st.code(run(code))
