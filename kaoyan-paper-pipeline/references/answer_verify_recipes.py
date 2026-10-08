# -*- coding: utf-8 -*-
"""考研数学答案核验配方：改题面即可跑。
环境：D:\pyenv\kaoyan\Scripts\python.exe（已装 sympy / mpmath）
跑法：D:/pyenv/kaoyan/Scripts/python.exe answer_verify_recipes.py
原则：卷子上每一个数字，都必须有这一行输出撑着。
"""
import sympy as sp
import mpmath as mp

x, y, t, n, lam = sp.symbols('x y t n lambda')
th = sp.symbols('theta', positive=True)   # 概率参数声明为正，否则 sympy 返回 Piecewise
OK = lambda tag, got, want: print(('OK  ' if sp.simplify(sp.sympify(got) - sp.sympify(want)) == 0 else 'BAD '),
                                   tag, '得到', got, '应为', want)

# ---- 极限（洛必达/泰勒类）
OK('极限 1/x² - 1/(x tan x)', sp.limit(1/x**2 - 1/(x*sp.tan(x)), x, 0), sp.Rational(1, 3))
OK('幂指函数极限 ((1+x)^(1/x)-e)/x', sp.limit(((1+x)**(1/x) - sp.E)/x, x, 0), -sp.E/2)

# ---- 定积分；对称代换型 sympy 不化就用数值
I = sp.integrate(x*sp.sin(x)/(1 + sp.cos(x)**2), (x, 0, sp.pi))
print('积分 ∫0^π x sinx/(1+cos²x):', I, '| 数值', mp.quad(lambda z: z*mp.sin(z)/(1+mp.cos(z)**2), [0, mp.pi]), '| 应为 π²/4 =', mp.pi**2/4)

# ---- 二重积分：两种次序互相验证
r1 = sp.integrate(sp.integrate(y, (y, x**2, 2 - x**2)), (x, -1, 1))
OK('二重积分 ∬y dσ', r1, sp.Rational(8, 3))

# ---- 多元极值：驻点 + 二阶判别
f = x**3 - y**3 + 3*x**2 + 3*y**2 - 9*x
for p in sp.solve([sp.diff(f, x), sp.diff(f, y)], [x, y], dict=True):
    fxx, fyy, fxy = (sp.diff(f, *a).subs(p) for a in [(x, 2), (y, 2), (x, y)])
    D = fxx*fyy - fxy**2
    kind = '极小' if D > 0 and fxx > 0 else '极大' if D > 0 and fxx < 0 else '非极值'
    print('  驻点', p, 'Δ=', D, 'f=', f.subs(p), '→', kind)

# ---- 格林公式：∂Q/∂x − ∂P/∂y 转二重积分（圆域用极坐标最稳）
P = 2*x*y - 2*y
Q = x**2 - 4*x
r_, phi = sp.symbols('r phi', positive=True)
integrand = (sp.diff(Q, x) - sp.diff(P, y)).subs({x: r_*sp.cos(phi), y: r_*sp.sin(phi)}) * r_
OK('格林公式 ∮ (x²+y²=9)', sp.integrate(sp.integrate(integrand, (r_, 0, 3)), (phi, 0, 2*sp.pi)), -18*sp.pi)

# ---- 线性代数：特征值 / 可对角化 / P⁻¹AP
A = sp.Matrix([[2, 0, 1], [3, 1, 3], [4, 0, 5]])
print('特征值', A.eigenvals(), '| A-E 的秩', (A - sp.eye(3)).rank(), '（秩 1 才可对角化）')
Pm = sp.Matrix([[1, 0, 1], [0, 1, 3], [-1, 0, 4]])
print('|P| =', Pm.det(), '| P⁻¹AP =', (Pm.inv()*A*Pm).tolist())
# 伴随矩阵题：A* = |A|A⁻¹，|kA| = kⁿ|A|
print('|-A⁻¹| (3阶,|A|=2) =', (-1)**3/sp.Integer(2), '应为 -1/2')

# ---- 概率：期望 / 矩估计 / 最大似然
OK('E(X) (θx^{θ-1})', sp.integrate(x*th*x**(th - 1), (x, 0, 1)), th/(th + 1))
S = sp.Symbol('S')  # S = Σ ln xᵢ（<0）
print('MLE 解 θ̂ =', sp.solve(sp.diff(n*sp.log(th) + (th - 1)*S, th), th), '（应为 -n/S）')

# ---- 级数求和
OK('Σ n/2ⁿ', sp.summation(n/2**n, (n, 1, sp.oo)), 2)
