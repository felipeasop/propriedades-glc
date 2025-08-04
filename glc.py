import re
from collections import defaultdict
import itertools

class Producao:
    """Representa uma produção da gramática, como 'A -> aB'."""
    def __init__(self, esquerda, direita):
        self.esquerda = esquerda.strip()
        self.direita = direita.strip()

    def __str__(self):
        return f"{self.esquerda} -> {self.direita}"

    def __repr__(self):
        return f"Producao({self.esquerda!r}, {self.direita!r})"

    def __eq__(self, other):
        return isinstance(other, Producao) and \
               self.esquerda == other.esquerda and \
               self.direita == other.direita

    def __hash__(self):
        return hash((self.esquerda, self.direita))

class Gramatica:
    """Representa uma gramática livre de contexto."""
    def __init__(self):
        self.variaveis = set()
        self.terminais = set()
        self.producoes = []
        self.simbolo_inicial = "S" 

    def adicionarProducao(self, esquerda, direita):
        """Adiciona uma nova produção e atualiza os conjuntos de símbolos."""
        if not self.producoes:
            self.simbolo_inicial = esquerda

        self.variaveis.add(esquerda)
        for char in direita:
            if 'A' <= char <= 'Z':
                self.variaveis.add(char)
            elif char != 'ε' and char.islower():
                self.terminais.add(char)

        self.producoes.append(Producao(esquerda, direita))

    def imprimir(self):
        """Exibe a gramática de forma legível."""
        print(f"Variáveis: {sorted(list(self.variaveis))}")
        print(f"Terminais: {sorted(list(self.terminais))}")
        print("Produções:")
        for prod in self.producoes:
            print(f"  {prod}")
        print(f"Símbolo Inicial: {self.simbolo_inicial}")

    def gerarNovaVariavel(self, prefixo='V'):
      """Gera um nome de variável único que não existe na gramática."""
      contador = 1
      while True:
          nova_var = f"{prefixo}{contador}"
          if nova_var not in self.variaveis:
              self.variaveis.add(nova_var)
              return nova_var
          contador += 1

class Simplificacao:
    """Agrupa os algoritmos de simplificação da gramática."""

    @staticmethod
    def removerSimbolosInuteis(gramatica):
        geradoras = set()
        mudou = True
        while mudou:
            mudou = False
            for p in gramatica.producoes:
                if p.esquerda not in geradoras:
                    if all(s in gramatica.terminais or s in geradoras for s in p.direita):
                        geradoras.add(p.esquerda)
                        mudou = True

        gramatica.variaveis = geradoras
        gramatica.producoes = [p for p in gramatica.producoes if p.esquerda in geradoras and
                               all(s in gramatica.terminais or s in geradoras for s in p.direita)]

        alcancaveis = {gramatica.simbolo_inicial}
        mudou = True
        while mudou:
            mudou = False
            for p in gramatica.producoes:
                if p.esquerda in alcancaveis:
                    for simbolo in p.direita:
                        if simbolo in gramatica.variaveis and simbolo not in alcancaveis:
                            alcancaveis.add(simbolo)
                            mudou = True

        gramatica.variaveis = alcancaveis
        gramatica.producoes = [p for p in gramatica.producoes if p.esquerda in alcancaveis]
        novos_terminais = set()
        for p in gramatica.producoes:
            for simbolo in p.direita:
                if simbolo in gramatica.terminais:
                    novos_terminais.add(simbolo)
        gramatica.terminais = novos_terminais


    @staticmethod
    def removerProducoesVazias(gramatica):
        anulaveis = set()
        mudou = True
        while mudou:
            mudou = False
            for p in gramatica.producoes:
                if p.direita == 'ε' or all(s in anulaveis for s in p.direita):
                    if p.esquerda not in anulaveis:
                        anulaveis.add(p.esquerda)
                        mudou = True

        novas_producoes = set()
        for p in gramatica.producoes:
            if p.direita != 'ε':
                indices_anulaveis = [i for i, s in enumerate(p.direita) if s in anulaveis]
                for i in range(1 << len(indices_anulaveis)):
                    nova_direita = list(p.direita)
                    for j, idx in enumerate(indices_anulaveis):
                        if (i >> j) & 1:
                            nova_direita[idx] = ''

                    nova_direita_str = "".join(nova_direita)
                    if nova_direita_str: 
                        novas_producoes.add(Producao(p.esquerda, nova_direita_str))
                novas_producoes.add(p)


        if gramatica.simbolo_inicial in anulaveis:
            novas_producoes.add(Producao(gramatica.simbolo_inicial, 'ε'))

        gramatica.producoes = list(novas_producoes)


    @staticmethod
    def substituirVariaveisUnitarias(gramatica):
        mudou = True
        while mudou:
            mudou = False
            novas_producoes = []
            removidas = []
            for p in gramatica.producoes:
                if len(p.direita) == 1 and p.direita in gramatica.variaveis:
                    removidas.append(p)
                    for p2 in gramatica.producoes:
                        if p2.esquerda == p.direita:
                            nova_prod = Producao(p.esquerda, p2.direita)
                            if nova_prod not in gramatica.producoes and nova_prod not in novas_producoes:
                                novas_producoes.append(nova_prod)
                                mudou = True

            gramatica.producoes = [p for p in gramatica.producoes if p not in removidas] + novas_producoes

class Melhorias:
    """Agrupa algoritmos de melhoria como fatoração e remoção de recursão."""

    @staticmethod
    def removerRecursaoEsquerda(gramatica):
        variaveis = sorted(list(gramatica.variaveis))
        novas_producoes = list(gramatica.producoes)

        for i in range(len(variaveis)):
            Ai = variaveis[i]
            for j in range(i):
                Aj = variaveis[j]
                producoes_Ai = [p for p in novas_producoes if p.esquerda == Ai]
                for p_ai in producoes_Ai:
                    if p_ai.direita.startswith(Aj):
                        alpha = p_ai.direita[len(Aj):]
                        novas_producoes.remove(p_ai)
                        for p_aj in [p for p in novas_producoes if p.esquerda == Aj]:
                            novas_producoes.append(Producao(Ai, p_aj.direita + alpha))
            
            recursivas, nao_recursivas = [], []
            for p in [p for p in novas_producoes if p.esquerda == Ai]:
                if p.direita.startswith(Ai):
                    recursivas.append(p)
                else:
                    nao_recursivas.append(p)

            if recursivas:
                Ai_prime = gramatica.gerarNovaVariavel(Ai)
                novas_producoes = [p for p in novas_producoes if p.esquerda != Ai]
                for p in nao_recursivas:
                    novas_producoes.append(Producao(Ai, p.direita + Ai_prime))
                for p in recursivas:
                    alpha = p.direita[len(Ai):]
                    novas_producoes.append(Producao(Ai_prime, alpha + Ai_prime))
                novas_producoes.append(Producao(Ai_prime, 'ε'))
        
        gramatica.producoes = novas_producoes


    @staticmethod
    def fatorarAEsquerda(gramatica):
        houve_mudanca = True
        while houve_mudanca:
            houve_mudanca = False
            variaveis = list(gramatica.variaveis)
            for A in variaveis:
                producoes_A = [p for p in gramatica.producoes if p.esquerda == A]
                prefixos = defaultdict(list)
                for p in producoes_A:
                    for i in range(1, len(p.direita) + 1):
                         prefixos[p.direita[:i]].append(p)

                for prefixo, prods in prefixos.items():
                    if len(prods) > 1:
                        for p in prods:
                            if not p.direita.startswith(prefixo):
                                e_fatoravel = False
                                break
                        if not e_fatoravel: continue
                        
                        tem_prefixo_maior = False
                        for p_check in prods:
                            if len(p_check.direita) > len(prefixo):
                                for outro_prefixo in prefixos:
                                    if len(outro_prefixo) > len(prefixo) and p_check.direita.startswith(outro_prefixo) and len(prefixos[outro_prefixo]) > 1:
                                        tem_prefixo_maior = True
                                        break
                            if tem_prefixo_maior: break
                        if tem_prefixo_maior: continue


                        houve_mudanca = True
                        A_prime = gramatica.gerarNovaVariavel(A)
                        
                        for p_removida in prods:
                            gramatica.producoes.remove(p_removida)
                            
                        gramatica.adicionarProducao(A, prefixo + A_prime)

                        for p in prods:
                            sufixo = p.direita[len(prefixo):]
                            if not sufixo:
                                sufixo = 'ε'
                            gramatica.adicionarProducao(A_prime, sufixo)
                        
                        break 
                if houve_mudanca:
                    break 

class FormasNormais:
    """Agrupa os algoritmos de conversão para formas normais."""

    @staticmethod
    def paraChomsky(gramatica):
        """Converte a gramática para a Forma Normal de Chomsky."""
        Simplificacao.removerProducoesVazias(gramatica)
        Simplificacao.substituirVariaveisUnitarias(gramatica)
        Simplificacao.removerSimbolosInuteis(gramatica)

        mapa_terminais = {}
        novas_producoes = []
        for p in gramatica.producoes:
            if len(p.direita) > 1:
                nova_direita = ""
                for simbolo in p.direita:
                    if simbolo in gramatica.terminais:
                        if simbolo not in mapa_terminais:
                            nova_var = gramatica.gerarNovaVariavel(f"T_{simbolo.upper()}")
                            mapa_terminais[simbolo] = nova_var
                            novas_producoes.append(Producao(nova_var, simbolo))
                        nova_direita += mapa_terminais[simbolo]
                    else:
                        nova_direita += simbolo
                novas_producoes.append(Producao(p.esquerda, nova_direita))
            else:
                novas_producoes.append(p)
        gramatica.producoes = novas_producoes

        houve_mudanca = True
        while houve_mudanca:
            houve_mudanca = False
            producoes_a_adicionar = []
            producoes_a_remover = []
            for p in gramatica.producoes:
                if len(p.direita) > 2:
                    houve_mudanca = True
                    producoes_a_remover.append(p)
                    
                    var_esq = p.esquerda
                    simbolos_dir = list(p.direita)
                    
                    while len(simbolos_dir) > 2:
                        primeiro = simbolos_dir.pop(0)
                        nova_var = gramatica.gerarNovaVariavel('X')
                        producoes_a_adicionar.append(Producao(var_esq, primeiro + nova_var))
                        var_esq = nova_var
                    
                    producoes_a_adicionar.append(Producao(var_esq, "".join(simbolos_dir)))
                    break 

            gramatica.producoes = [p for p in gramatica.producoes if p not in producoes_a_remover] + producoes_a_adicionar


    @staticmethod
    def paraGreibach(gramatica):
        """Converte a gramática para a Forma Normal de Greibach."""
        FormasNormais.paraChomsky(gramatica)
        Melhorias.removerRecursaoEsquerda(gramatica)
        Simplificacao.removerProducoesVazias(gramatica)

        variaveis = sorted(list(gramatica.variaveis))
        mapa_ordem = {var: i for i, var in enumerate(variaveis)}

        mudou = True
        while mudou:
            mudou = False
            novas_producoes = list(gramatica.producoes)
            
            for p in list(novas_producoes):
                primeiro_simbolo = p.direita[0]
                if primeiro_simbolo in gramatica.variaveis:
                    producoes_subst = [sub for sub in gramatica.producoes if sub.esquerda == primeiro_simbolo]
                    
                    if any(sub.direita[0] in gramatica.variaveis for sub in producoes_subst):
                        continue

                    mudou = True
                    novas_producoes.remove(p)
                    sufixo = p.direita[1:]
                    for p_sub in producoes_subst:
                        novas_producoes.append(Producao(p.esquerda, p_sub.direita + sufixo))

            gramatica.producoes = novas_producoes

def main():
    """Função principal que orquestra a execução do programa."""
    gramatica = Gramatica()

    print("Digite as produções da gramática (ex: S -> aAb | c). Deixe uma linha vazia para encerrar:")
    while True:
        linha = input().strip()
        if not linha:
            break

        partes = linha.split("->")
        if len(partes) != 2:
            print("Formato inválido. Use 'Variavel -> producao'.")
            continue

        esquerda = partes[0].strip()
        direitas = [p.strip() for p in partes[1].split("|")]

        for direita in direitas:
            gramatica.adicionarProducao(esquerda, direita)

    print("\n--- Gramática Original ---")
    gramatica.imprimir()

    print("\n\n--- Etapa de Simplificação ---")
    Simplificacao.removerSimbolosInuteis(gramatica)
    print("\n1. Após remover símbolos inúteis/inalcançáveis:")
    gramatica.imprimir()

    Simplificacao.removerProducoesVazias(gramatica)
    print("\n2. Após remover produções vazias:")
    gramatica.imprimir()
    
    Simplificacao.substituirVariaveisUnitarias(gramatica)
    print("\n3. Após substituir produções unitárias:")
    gramatica.imprimir()

    print("\n\n--- Etapa de Melhorias ---")
    Melhorias.removerRecursaoEsquerda(gramatica)
    Simplificacao.removerProducoesVazias(gramatica)
    Simplificacao.substituirVariaveisUnitarias(gramatica)
    print("\n1. Após remover recursão à esquerda:")
    gramatica.imprimir()
    
    Melhorias.fatorarAEsquerda(gramatica)
    print("\n2. Após fatoração à esquerda:")
    gramatica.imprimir()

    print("\n\n--- Etapa de Normalização ---")
    opcao = ""
    while opcao.upper() not in ["C", "G"]:
        opcao = input("\nDeseja converter para qual Forma Normal? (C = Chomsky, G = Greibach): ")

    if opcao.upper() == 'C':
        FormasNormais.paraChomsky(gramatica)
        print("\n--- Gramática Final na Forma Normal de Chomsky ---")
    else:
        FormasNormais.paraGreibach(gramatica)
        print("\n--- Gramática Final na Forma Normal de Greibach ---")
    
    gramatica.imprimir()


if __name__ == "__main__":
    main()