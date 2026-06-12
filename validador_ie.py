#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validador de Inscricao Estadual (IE) por estado.

Cada funcao foi implementada a partir do "ROTEIRO DE CRITICA DA INSCRICAO
ESTADUAL" oficial do Sintegra, cujos textos estao em regras/<estado>.txt.
O exemplo numerico de cada texto e usado como teste em testar() / --teste.

Uso como biblioteca:
    from validador_ie import validar, validar_todos
    validar("SP", "110.042.490.114")   # -> True
    validar_todos("110.042.490.114")   # -> ['SP', ...] UFs em que e valida

Uso na linha de comando:
    python3 validador_ie.py SP 110.042.490.114   # valida numa UF
    python3 validador_ie.py 110.042.490.114       # testa em TODAS as UFs
    python3 validador_ie.py --todos 11111114      # idem (forma explicita)
    python3 validador_ie.py --teste               # roda os auto-testes
    python3 validador_ie.py --listar              # lista UFs suportadas
"""
import functools
import re
import sys

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _digitos(ie):
    """Mantem apenas algarismos."""
    return re.sub(r"\D", "", str(ie))

def _norm(ie, *tamanhos):
    """Normaliza para um dos tamanhos canonicos preenchendo zeros a esquerda.

    IEs costumam ser armazenadas como inteiros, perdendo zeros a esquerda.
    Retorna a string preenchida ate o menor tamanho aceitavel >= len(n);
    se for maior que todos os tamanhos, devolve como esta (sera rejeitada).
    """
    n = _digitos(ie)
    for tam in sorted(tamanhos):
        if len(n) <= tam:
            return n.zfill(tam)
    return n

def _rejeita_lixo(fn):
    """Guarda comum a TODOS os validadores: uma IE sem nenhum digito ou
    composta apenas de zeros e sempre invalida (do contrario satisfaria o
    calculo, pois o digito verificador de um numero todo-zero e zero)."""
    @functools.wraps(fn)
    def wrapper(ie):
        n = _digitos(ie)
        if not n or set(n) == {"0"}:
            return False
        return fn(ie)
    return wrapper

def _tenta(ie, tamanhos, core):
    """Para formatos com mais de um tamanho valido: testa cada tamanho
    (preenchendo zeros a esquerda) e aceita se qualquer um validar."""
    n0 = _digitos(ie)
    for tam in sorted(tamanhos):
        if len(n0) <= tam and core(n0.zfill(tam)):
            return True
    return False

def _limpar_sp(ie):
    """Para SP: mantem 'P' (produtor rural) e algarismos, em maiusculo."""
    return re.sub(r"[^0-9P]", "", str(ie).upper())

def _soma_pesos(digs, pesos):
    """Soma produto a produto; digs e pesos alinhados da esquerda p/ direita."""
    return sum(int(d) * p for d, p in zip(digs, pesos))

def _dv_mod11(soma, resto_zero=(0, 1), trata_10_11_como_zero=True):
    """Digito verificador padrao modulo 11: 11 - (soma % 11)."""
    resto = soma % 11
    if resto in resto_zero:
        return 0
    dv = 11 - resto
    if trata_10_11_como_zero and dv >= 10:
        return 0
    return dv


# ---------------------------------------------------------------------------
# Validadores por estado
# Cada funcao recebe a IE (qualquer formatacao) e devolve True/False.
# ---------------------------------------------------------------------------

def acre(ie):
    n = _norm(ie, 13)
    if len(n) != 13 or n[:2] != "01":
        return False
    p1 = [4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    p2 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    d1 = _dv_mod11(_soma_pesos(n[:11], p1))
    d2 = _dv_mod11(_soma_pesos(n[:11] + str(d1), p2))
    return n[11:] == f"{d1}{d2}"

def alagoas(ie):
    n = _norm(ie, 9)
    if len(n) != 9 or n[:2] != "24":
        return False
    soma = _soma_pesos(n[:8], [9, 8, 7, 6, 5, 4, 3, 2])
    resto = (soma * 10) % 11
    dv = 0 if resto == 10 else resto
    return n[8] == str(dv)

def amazonas(ie):
    n = _norm(ie, 9)
    if len(n) != 9:
        return False
    soma = _soma_pesos(n[:8], [9, 8, 7, 6, 5, 4, 3, 2])
    if soma < 11:
        dv = 11 - soma
    else:
        resto = soma % 11
        dv = 0 if resto <= 1 else 11 - resto
    return n[8] == str(dv)

def amapa(ie):
    n = _norm(ie, 9)
    if len(n) != 9 or n[:2] != "03":
        return False
    base = int(n[:8])
    if base <= 3017000:
        p, d = 5, 0
    elif base <= 3019022:
        p, d = 9, 1
    else:
        p, d = 0, 0
    soma = p + _soma_pesos(n[:8], [9, 8, 7, 6, 5, 4, 3, 2])
    resto = soma % 11
    dv = 11 - resto
    if dv == 10:
        dv = 0
    elif dv == 11:
        dv = d
    return n[8] == str(dv)

def bahia(ie):
    def core(n):
        if len(n) == 8:
            base, dv_inf, seletor = n[:6], n[6:], n[0]
        else:
            base, dv_inf, seletor = n[:7], n[7:], n[1]
        mod = 10 if seletor in "0123458" else 11

        def calc(s):
            resto = _soma_pesos(s[::-1], range(2, 2 + len(s))) % mod
            if mod == 10:
                return (10 - resto) % 10
            return 0 if resto in (0, 1) else 11 - resto

        d2 = calc(base)
        d1 = calc(base + str(d2))
        return dv_inf == f"{d1}{d2}"
    return _tenta(ie, (8, 9), core)

def ceara(ie):
    n = _norm(ie, 9)
    if len(n) != 9:
        return False
    dv = _dv_mod11(_soma_pesos(n[:8], [9, 8, 7, 6, 5, 4, 3, 2]),
                   resto_zero=())
    return n[8] == str(dv)

def distrito_federal(ie):
    n = _norm(ie, 13)
    if len(n) != 13:
        return False
    p1 = [4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    p2 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    d1 = _dv_mod11(_soma_pesos(n[:11], p1))
    d2 = _dv_mod11(_soma_pesos(n[:11] + str(d1), p2))
    return n[11:] == f"{d1}{d2}"

def espirito_santo(ie):
    n = _norm(ie, 9)
    if len(n) != 9:
        return False
    resto = _soma_pesos(n[:8], [9, 8, 7, 6, 5, 4, 3, 2]) % 11
    dv = 0 if resto < 2 else 11 - resto
    return n[8] == str(dv)

def goias(ie):
    n = _norm(ie, 9)
    if len(n) != 9 or not (n[:2] in ("10", "11") or 20 <= int(n[:2]) <= 29):
        return False
    resto = _soma_pesos(n[:8], [9, 8, 7, 6, 5, 4, 3, 2]) % 11
    if resto == 0:
        dv = 0
    elif resto == 1:
        # Faixa especial documentada de Goias.
        dv = 1 if 10103105 <= int(n[:8]) <= 10119997 else 0
    else:
        dv = 11 - resto
    return n[8] == str(dv)

def maranhao(ie):
    n = _norm(ie, 9)
    if len(n) != 9 or n[:2] != "12":
        return False
    dv = _dv_mod11(_soma_pesos(n[:8], [9, 8, 7, 6, 5, 4, 3, 2]))
    return n[8] == str(dv)

def mato_grosso(ie):
    n = _norm(ie, 11)
    if len(n) != 11:
        return False
    pesos = [3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    dv = _dv_mod11(_soma_pesos(n[:10], pesos))
    return n[10] == str(dv)

def mato_grosso_do_sul(ie):
    n = _norm(ie, 9)
    if len(n) != 9 or n[:2] not in ("28", "50"):
        return False
    resto = _soma_pesos(n[:8], [9, 8, 7, 6, 5, 4, 3, 2]) % 11
    if resto == 0:
        dv = 0
    else:
        t = 11 - resto
        dv = 0 if t > 9 else t
    return n[8] == str(dv)

def minas_gerais(ie):
    n = _norm(ie, 13)
    if len(n) != 13:
        return False
    municipio, inscricao, ordem, dv_inf = n[:3], n[3:9], n[9:11], n[11:]

    # 1o digito: insere "0" apos o municipio, multiplica por 1,2,1,2...
    base1 = municipio + "0" + inscricao + ordem
    soma1 = 0
    for i, ch in enumerate(base1):
        prod = int(ch) * (1 if i % 2 == 0 else 2)
        soma1 += prod // 10 + prod % 10          # soma os algarismos do produto
    d1 = (10 - soma1 % 10) % 10

    # 2o digito: numero + d1, pesos 2..11 ciclicos da direita p/ esquerda
    base2 = municipio + inscricao + ordem + str(d1)
    pesos = list(range(2, 12))
    soma2 = sum(int(ch) * pesos[i % len(pesos)]
                for i, ch in enumerate(reversed(base2)))
    d2 = _dv_mod11(soma2)
    return dv_inf == f"{d1}{d2}"

def para(ie):
    n = _norm(ie, 9)
    if len(n) != 9 or n[:2] not in ("15", "75", "76", "77", "78", "79"):
        return False
    dv = _dv_mod11(_soma_pesos(n[:8], [9, 8, 7, 6, 5, 4, 3, 2]))
    return n[8] == str(dv)

def paraiba(ie):
    n = _norm(ie, 9)
    if len(n) != 9:
        return False
    dv = _dv_mod11(_soma_pesos(n[:8], [9, 8, 7, 6, 5, 4, 3, 2]),
                   resto_zero=())
    return n[8] == str(dv)

def parana(ie):
    n = _norm(ie, 10)
    if len(n) != 10:
        return False
    d1 = _dv_mod11(_soma_pesos(n[:8], [3, 2, 7, 6, 5, 4, 3, 2]))
    d2 = _dv_mod11(_soma_pesos(n[:8] + str(d1), [4, 3, 2, 7, 6, 5, 4, 3, 2]))
    return n[8:] == f"{d1}{d2}"

def pernambuco(ie):
    def core(n):
        if len(n) == 9:                   # formato atual (eFisco): 7 base + 2 DV
            base = n[:7]
            d1 = _dv_mod11(_soma_pesos(base, [8, 7, 6, 5, 4, 3, 2]))
            d2 = _dv_mod11(_soma_pesos(base, [9, 8, 7, 6, 5, 4, 3, 2]) + d1 * 2)
            return n[7:] == f"{d1}{d2}"
        # formato antigo CACEPE: 13 base + 1 DV
        pesos = [5, 4, 3, 2, 1, 9, 8, 7, 6, 5, 4, 3, 2]
        dig = 11 - _soma_pesos(n[:13], pesos) % 11
        if dig > 9:
            dig -= 10
        return n[13] == str(dig)
    return _tenta(ie, (9, 14), core)

def piaui(ie):
    n = _norm(ie, 9)
    if len(n) != 9:
        return False
    dv = _dv_mod11(_soma_pesos(n[:8], [9, 8, 7, 6, 5, 4, 3, 2]))
    return n[8] == str(dv)

def rio_de_janeiro(ie):
    n = _norm(ie, 8)
    if len(n) != 8:
        return False
    resto = _soma_pesos(n[:7], [2, 7, 6, 5, 4, 3, 2]) % 11
    dv = 0 if resto <= 1 else 11 - resto
    return n[7] == str(dv)

def rio_grande_do_norte(ie):
    def core(n):
        if n[:2] != "20":
            return False
        pesos = ([9, 8, 7, 6, 5, 4, 3, 2] if len(n) == 9
                 else [10, 9, 8, 7, 6, 5, 4, 3, 2])
        resto = (_soma_pesos(n[:-1], pesos) * 10) % 11
        dv = 0 if resto == 10 else resto
        return n[-1] == str(dv)
    return _tenta(ie, (9, 10), core)

def rio_grande_do_sul(ie):
    n = _norm(ie, 10)
    if len(n) != 10:
        return False
    dv = _dv_mod11(_soma_pesos(n[:9], [2, 9, 8, 7, 6, 5, 4, 3, 2]))
    return n[9] == str(dv)

def rondonia(ie):
    def core(n):
        if len(n) == 14:                  # formato atual: 13 base + 1 DV
            pesos = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
            base, dv_inf = n[:13], n[13]
        else:                             # formato antigo: 3 munic + 5 empresa + DV
            pesos = [6, 5, 4, 3, 2]
            base, dv_inf = n[3:8], n[8]
        dv = 11 - _soma_pesos(base, pesos) % 11
        if dv > 9:
            dv -= 10
        return dv_inf == str(dv)
    return _tenta(ie, (9, 14), core)

def roraima(ie):
    n = _norm(ie, 9)
    if len(n) != 9 or n[:2] != "24":
        return False
    dv = _soma_pesos(n[:8], [1, 2, 3, 4, 5, 6, 7, 8]) % 9
    return n[8] == str(dv)

def santa_catarina(ie):
    n = _norm(ie, 9)
    if len(n) != 9:
        return False
    dv = _dv_mod11(_soma_pesos(n[:8], [9, 8, 7, 6, 5, 4, 3, 2]))
    return n[8] == str(dv)

def sao_paulo(ie):
    s = _limpar_sp(ie)
    if s.startswith("P"):                 # Produtor rural: P0MMMSSSSD000
        d = re.sub(r"\D", "", s[1:])
        if len(d) != 12:
            return False
        soma = _soma_pesos(d[:8], [1, 3, 4, 5, 6, 7, 8, 10])
        dv = (soma % 11) % 10
        return d[8] == str(dv)
    n = _norm(s, 12)                      # Industrial/comercial: 12 digitos
    if len(n) != 12:
        return False
    d1 = (_soma_pesos(n[:8], [1, 3, 4, 5, 6, 7, 8, 10]) % 11) % 10
    if n[8] != str(d1):
        return False
    d2 = (_soma_pesos(n[:11], [3, 2, 10, 9, 8, 7, 6, 5, 4, 3, 2]) % 11) % 10
    return n[11] == str(d2)

def sergipe(ie):
    n = _norm(ie, 9)
    if len(n) != 9:
        return False
    dv = _dv_mod11(_soma_pesos(n[:8], [9, 8, 7, 6, 5, 4, 3, 2]))
    return n[8] == str(dv)

def tocantins(ie):
    def core(n):
        if len(n) == 9:
            # Formato atual: 8 digitos base + 1 verificador (modulo 11).
            base, dv_pos = n[:8], n[8]
        elif n[2:4] in ("01", "02", "03", "99"):
            # Formato antigo: posicoes 3 e 4 (tipo) nao entram no calculo.
            base, dv_pos = n[:2] + n[4:10], n[10]
        else:
            return False
        resto = _soma_pesos(base, [9, 8, 7, 6, 5, 4, 3, 2]) % 11
        dv = 0 if resto < 2 else 11 - resto
        return dv_pos == str(dv)
    return _tenta(ie, (9, 11), core)


# ---------------------------------------------------------------------------
# Registro / dispatcher
# ---------------------------------------------------------------------------

VALIDADORES = {
    "AC": acre, "AL": alagoas, "AM": amazonas, "AP": amapa, "BA": bahia,
    "CE": ceara, "DF": distrito_federal, "ES": espirito_santo, "GO": goias,
    "MA": maranhao, "MT": mato_grosso, "MS": mato_grosso_do_sul,
    "MG": minas_gerais, "PA": para, "PB": paraiba, "PR": parana,
    "PE": pernambuco, "PI": piaui, "RJ": rio_de_janeiro,
    "RN": rio_grande_do_norte, "RS": rio_grande_do_sul, "RO": rondonia,
    "RR": roraima, "SC": santa_catarina, "SP": sao_paulo, "SE": sergipe,
    "TO": tocantins,
}

# Aplica a guarda de lixo/zeros a cada validador e rebinda os nomes de modulo
# (acre, alagoas, ...) para as versoes protegidas, de modo que tanto
# validar("AC", x) quanto acre(x) rejeitem entradas todo-zero.
VALIDADORES = {uf: _rejeita_lixo(fn) for uf, fn in VALIDADORES.items()}
for _fn in VALIDADORES.values():
    globals()[_fn.__name__] = _fn


def validar(uf, numero):
    """Valida a IE 'numero' para a unidade federativa 'uf' (sigla, 2 letras).

    Levanta ValueError se a UF nao for reconhecida.
    """
    uf = str(uf).strip().upper()
    if uf not in VALIDADORES:
        raise ValueError(f"UF desconhecida: {uf!r}. Use uma de {sorted(VALIDADORES)}")
    return VALIDADORES[uf](numero)


def validar_todos(numero):
    """Testa 'numero' contra TODAS as UFs.

    Retorna uma lista (ordenada) das siglas em que o numero e uma IE valida.
    Util quando nao se sabe o estado de origem do numero.
    """
    return [uf for uf in sorted(VALIDADORES) if VALIDADORES[uf](numero)]


# ---------------------------------------------------------------------------
# Auto-testes (exemplos extraidos dos textos oficiais em /regras)
# ---------------------------------------------------------------------------

# Numeros validos. (*) = exemplo oficial do proprio roteiro do Sintegra;
# os demais foram construidos aplicando o algoritmo descrito no texto.
EXEMPLOS_VALIDOS = {
    "AC": "01.004.823/001-12",   # *
    "AL": "240000048",           # *
    "AM": "111111110",
    "AP": "030123459",           # *
    "BA": "123456-63",           # *  (8 digitos, modulo 10)
    "CE": "06000001-5",          # *
    "DF": "07300001001-09",      # *
    "ES": "999999990",           # *
    "GO": "10.987.654-7",        # *
    "MA": "120000385",           # *
    "MT": "0013000001-9",        # *
    "MS": "280000006",
    "MG": "062.307.904/0081",    # *
    "PA": "15999999-5",          # *
    "PB": "06000001-5",          # *
    "PR": "123.45678-50",        # *
    "PE": "032141840",           # *  (formato atual eFisco)
    "PI": "012345679",           # *
    "RJ": "11111114",
    "RN": "20.040.040-1",        # *  (9 digitos)
    "RS": "224/3658792",         # *
    "RO": "0000000062521-3",     # *  (formato atual)
    "RR": "24006153-6",          # *
    "SC": "251.040.852",         # *
    "SP": "110.042.490.114",     # *  (industrial/comercial)
    "SE": "27123456-3",          # *
    "TO": "29010227836",         # *
}

# Casos extras para cobrir formatos alternativos descritos nos textos.
EXEMPLOS_EXTRAS = {
    "BA": ["612345-57", "100000306"],     # * 8 dig modulo 11 / 9 dig modulo 10
    "RN": ["20.0.040.040-0"],              # * 10 digitos
    "RO": ["101625213"],                   # * formato antigo (9 digitos)
    "PE": ["18100100000049"],              # * CACEPE antigo (14 digitos)
    "SP": ["P011004243002"],               # * produtor rural
}


def testar(verbose=True):
    falhas = []

    def checar(uf, num, esperado):
        try:
            ok = validar(uf, num)
        except Exception as e:  # noqa: BLE001
            ok = f"ERRO: {e}"
        passou = ok is esperado
        if not passou:
            falhas.append((uf, num, esperado, ok))
        if verbose:
            marca = "ok " if passou else "FALHA"
            print(f"  [{marca}] {uf} {num!r:24} valido={ok} (esperado {esperado})")

    if verbose:
        print("== validos ==")
    for uf, num in EXEMPLOS_VALIDOS.items():
        checar(uf, num, True)
    for uf, nums in EXEMPLOS_EXTRAS.items():
        for num in nums:
            checar(uf, num, True)

    if verbose:
        print("== invalidos: lixo / todo-zero / vazio (todas as UFs) ==")
    for uf in VALIDADORES:
        for lixo in ("", "0", "00000000", "0" * 14, "Minas Gerais", "abc"):
            checar(uf, lixo, False)

    if verbose:
        print("== invalidos (ultimo digito trocado) ==")
    for uf, num in EXEMPLOS_VALIDOS.items():
        d = _digitos(num)
        errado = num.replace(d[-1], str((int(d[-1]) + 1) % 10), 1) if d else num
        # garante que realmente mudou o ultimo digito
        e = _digitos(errado)
        if e and e[-1] != d[-1]:
            checar(uf, e[:-1] + str((int(d[-1]) + 1) % 10), False)

    total_ok = "TODOS OS TESTES PASSARAM" if not falhas else f"{len(falhas)} FALHA(S)"
    if verbose:
        print(f"\n{total_ok}")
    return not falhas


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if argv[0] == "--teste":
        return 0 if testar() else 1
    if argv[0] == "--listar":
        print(", ".join(sorted(VALIDADORES)))
        return 0

    # Modo "todos os estados": um unico argumento (numero) ou flag --todos.
    if argv[0] == "--todos":
        argv = argv[1:]
    if len(argv) == 1:
        numero = argv[0]
        achados = validar_todos(numero)
        if achados:
            print(f"{numero}: válida em {', '.join(achados)}")
        else:
            print(f"{numero}: inválida em todos os estados")
        return 0 if achados else 1

    # Modo normal: <UF> <numero>
    uf, numero = argv[0], argv[1]
    try:
        ok = validar(uf, numero)
    except ValueError as e:
        print(e, file=sys.stderr)
        return 2
    print(f"{uf.upper()} {numero}: {'VALIDA' if ok else 'INVALIDA'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
