from itertools import count
from collections import namedtuple
piece = {"P": 100, "N": 280, "B": 320, "R": 479, "Q": 929, "K": 60000}
pst = {'P': (0, 0, 0, 0, 0, 0, 0, 0, 78, 83, 86, 73, 102, 82, 85, 90, 7, 29, 21, 44, 40, 31, 44, 7, -17, 16, -2, 15, 14, 0, 15, -13, -26, 3, 10, 9, 6, 1, 0, -23, -22, 9, 5, -11, -10, -2, 3, -19, -31, 8, -7, -37, -36, -14, 3, -31, 0, 0, 0, 0, 0, 0, 0, 0), 'N': (-66, -53, -75, -75, -10, -55, -58, -70, -3, -6, 100, -36, 4, 62, -4, -14, 10, 67, 1, 74, 73, 27, 62, -2, 24, 24, 45, 37, 33, 41, 25, 17, -1, 5, 31, 21, 22, 35, 2, 0, -18, 10, 13, 22, 18, 15, 11, -14, -23, -15, 2, 0, 2, 0, -23, -20, -74, -23, -26, -24, -19, -35, -22, -69), 'B': (-59, -78, -82, -76, -23, -107, -37, -50, -11, 20, 35, -42, -39, 31, 2, -22, -9, 39, -32, 41, 52, -10, 28, -14, 25, 17, 20, 34, 26, 25, 15, 10, 13, 10, 17, 23, 17, 16, 0, 7, 14, 25, 24, 15, 8, 25, 20, 15, 19, 20, 11, 6, 7, 6, 20, 16, -7, 2, -15, -12, -14, -15, -10, -10), 'R': (35, 29, 33, 4, 37, 33, 56, 50, 55, 29, 56, 67, 55, 62, 34, 60, 19, 35, 28, 33, 45, 27, 25, 15, 0, 5, 16, 13, 18, -4, -9, -6, -28, -35, -16, -21, -13, -29, -46, -30, -42, -28, -42, -25, -25, -35, -26, -46, -53, -38, -31, -26, -29, -43, -44, -53, -30, -24, -18, 5, -2, -18, -31, -32), 'Q': (0,)*64, 'K': (4, 54, 47, -99, -99, 60, 83, -62, -32, 10, 55, 56, 56, 55, 10, 3, -62, 12, -57, 44, -67, 28, 37, -31, -55, 50, 11, -4, -19, 13, 0, -49, -55, -43, -52, -28, -51, -47, -8, -50, -47, -42, -43, -79, -64, -32, -29, -32, -4, 3, -14, -50, -57, -18, 13, 4, 17, 30, -3, -14, 6, -1, 40, 18)}
for k, table in pst.items():
    pst[k] = (0,) * 20 + tuple(x + piece[k] for x in sum((table[i * 8 : i * 8 + 8] for i in range(8)), ())) + (0,) * 20
initial = '         \n' * 2 + ' rnbqkbnr\n pppppppp\n' + ' ........\n' * 4 + ' PPPPPPPP\n RNBQKBNR\n' + '         \n' * 2
N, E, S, W = -10, 1, 10, -1
Q4 = N, E, S, W, N + E, S + E, S + W, N + W
directions = {'P': (N, N + N, N + W, N + E), 'N': (N + N + E, E + N + E, E + S + E, S + S + E, S + S + W, W + S + W, W + N + W, N + N + W), 'B': Q4[4:], 'R': Q4[:4], 'Q': Q4, 'K': Q4}
class Position(namedtuple("Position", "board score ep")):
    def gen_moves(self):
        for i, p in enumerate(self.board):
            if p not in "PNBRQK": continue
            for d in directions[p]:
                for j in count(i + d, d):
                    q = self.board[j]
                    if q in " \nPNBRQK": break
                    if p == "P":
                        if d in (N, N + N) and q != ".": break
                        if d == N + N and (i < 91 + N or self.board[i + N] != "."): break
                        if d in (N + W, N + E) and q == "." and j != self.ep: break
                        if 21 <= j <= 28:
                            yield from ((i, j, prom) for prom in "NBRQ")
                            break
                    yield (i, j, "")
                    if p in "PNK" or q in "pnbrqk": break
    def rotate(self):
        return Position(self.board[::-1].swapcase(), -self.score, 119 - self.ep if self.ep else 0)
    def move(self, move):
        i, j, prom = move
        put = lambda board, i, p: board[:i] + p + board[i + 1 :]
        p, q, board, ep = self.board[i], self.board[j], self.board, 0
        score = self.score + self.value(move)
        board = put(board, j, board[i])
        board = put(board, i, ".")
        if p == "P":
            if 21 <= j <= 28:  board = put(board, j, prom)
            if j - i == 2 * N: ep = i + N
            if j == self.ep:   board = put(board, j + S, ".")
        return Position(board, score, ep).rotate()
    def value(self, move):
        i, j, prom = move
        p, q = self.board[i], self.board[j]
        score = pst[p][j] - pst[p][i]
        if q in "pnbrqk": score += pst[q.upper()][119 - j]
        return score
class Stop(Exception): pass
Entry = namedtuple("Entry", "lower upper")
class Searcher:
    def __init__(self):
        self.tp_score, self.tp_move = {}, {}
        self.nodes, self.budget = 0, 0
    def bound(self, pos, gamma, depth, root=False):
        depth = max(depth, 0)
        self.nodes += 1
        if self.nodes % 2048 == 0 and self.nodes >= self.budget: raise IndexError
        if pos.score <= -47923: return -69290
        if not root:
            entry = self.tp_score.get((pos, depth), (-69290, 69290))
            if entry[0] >= gamma: return entry[0]
            if entry[1] < gamma: return entry[1]
        killer = self.tp_move.get(pos)
        def moves():
            if depth == 0: yield None, None
            if killer and ((val := pos.value(killer)) >= 36 or depth): yield val, killer
            yield from sorted(((v, m) for m in pos.gen_moves() if (v := pos.value(m)) >= 36 or depth), reverse=True)
        best = -69290
        for val, move in moves():
            if move is None: score = pos.score
            elif val >= 47923: score = 69290
            else: score = -self.bound(pos.move(move), 1 - gamma, depth - 1)
            best = max(best, score)
            if best >= gamma:
                if move is not None and depth: self.tp_move[pos] = move
                break
        if not root: self.tp_score[pos, depth] = (best, entry[1]) if best >= gamma else (entry[0], best)
        return best
    def search(self, history):
        self.nodes, self.tp_score = 0, {}
        pos = history[-1]
        gamma = 0
        for depth in range(1, 1000):
            lower, upper = 1 - 69290, 69290
            while lower < upper:
                score = self.bound(pos, gamma, depth, root=True)
                if score >= gamma: lower = score
                else: upper = score
                yield depth, gamma, score, self.tp_move.get(pos)
                gamma = (lower + upper + 1) // 2
            if self.nodes >= self.budget: return
def parse(c): return 91 + ord(c[0]) - ord("a") - 10 * (int(c[1]) - 1)
def render(i): return chr((i - 91) % 10 + ord("a")) + str(1 - (i - 91) // 10)
hist = [Position(initial, 0, 0)]
import json as J, os, urllib.request as R
B={}
for e in lzma.decompress(q.b85decode("000010RR90|NsC0{{T6fX4f^|@|_MGY-TOB$hujU)95#(p<hf8s^>-X+rSw1V~wgQ*xOpsJshz1m*UMfEMe)dj1D<P4sF7nMK|d35@F%yNw^;^{+=;jcB7^;abtH5&_X}#pLGqb<MVS~#nUm2Oue3%&QlbS^s`o3V_MJ<z(Y78-O7$R?QfyHELarztVbEi_m!d_LfD*<JqA|5$1%E&R3RiPZaC?vpXa#D+@c>s)|RQl?39H$RSBxXj=_NrFIS){;T>iXlUJBqa@%v3sLLSM7UXfNtt@Qp!Dr&a>GHKfrM6N)KZ_9mB;}U|gk-XTWMkvGBk%emcv);x%7uNRy`#jbwOq+zK}8`VZU`Mcz&U{I8~;WLC{sR}l6gFl*mf0HHRvRe1aqdHPk!Wb*kynXR~JyU29ea|CO6`@R?I#zyziB1np-U@RnJtft1KP$v8o>ura3(6sxP`SQLVOERYT#e+)76qPRSh%tiGRdWW(j@%1~uHHshF?0YEhj+O%4tB#PU$$|YZy?+UTXj3g7g6r2~a>(hm__e$`86aM$y-4g")).decode().split(";"):
 k,v=e.split(":"); B[k]=v
V=os.environ["MAKEFUN_ENV_URL"]
def post(p,b):
 r=R.Request(V+p,data=J.dumps(b).encode())
 return J.load(R.urlopen(r))
while 1:
 g=post("/game",{})
 if g["status"]=="done": break
 while g["status"]=="your_move":
  e=B.get(g["opening"]["id"])
  n=len(g["moves"])//2
  bk=e[4*n:4*n+4] if e else None
  if bk in g["legal_moves"]: mv=bk
  else:
   del hist[1:]
   for ply,mv0 in enumerate(g["moves"]):
    i,j,prom=parse(mv0[:2]),parse(mv0[2:4]),mv0[4:].upper()
    if ply%2==1: i,j=119-i,119-j
    hist.append(hist[-1].move((i,j,prom)))
   s2=Searcher(); s2.budget=int(os.environ.get("CHESS_NODES","60000"))
   cand=None
   try:
    for depth,gamma,score,move in s2.search(hist):
     if score>=gamma:
      if move is None: break
      i,j,prom=move
      if len(hist)%2==0: i,j=119-i,119-j
      cand=render(i)+render(j)+prom.lower()
   except IndexError: pass
   mv=cand or g["legal_moves"][0]
  g=post("/move",{"game":g["game"],"move":mv})
