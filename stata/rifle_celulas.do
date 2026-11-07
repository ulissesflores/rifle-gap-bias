* rifle_celulas.do
* Reproduz no Stata, com o pacote oficial, as células centrais do artigo
* "O prefeito melhora a cidade além do acaso? Dado faltando na troca de prefeito faz o teste dizer que sim":
*   sem lacuna; lacuna no período 9 com a costura padrão; a mesma lacuna com nostitch.
*
* NÃO TESTADO: o autor não tinha Stata. É o confronto que o artigo deixa preparado (Seção 4.1 e
* direção futura i). O gerador do Stata não é o do numpy, então as taxas devem concordar com as do
* artigo dentro do erro de Monte Carlo, não bit a bit. Com 1.000 municípios e 500 bases, o artigo
* (tradução Python) dá: sem lacuna 2,2%; período 9 com costura 27,2%; com nostitch 4,6%.
*
* Requisitos: Stata 14 ou mais novo e o pacote:  ssc install rifle
* Rode da raiz do repositório:  do stata/rifle_celulas.do
*
* Dois cuidados que o código do pacote impõe (ver README e Seção 4.2):
*   1. o rifle agrupa o líder pelo identificador em TODAS as unidades ao mesmo tempo
*      (egen leaderid = group(leader)); por isso o líder aqui é o par município-prefeito;
*   2. o nostitch reconhece trechos contínuos por "period == period[_n-1] + 1"; por isso o
*      período é o número do meio-mandato, de 1 a 10, nunca o ano.

version 14
clear all
set more off

local bases   100                     // o artigo usa 500
local perm    1000
local rho     0.21696453979704527     // data/parametros.json, rho_gerador
local amostra 1000                    // municípios sorteados; 0 = painel inteiro (5.468)
set seed 20261103

import delimited using "data/mandatos.csv", clear stringcols(_all)
destring cod_ibge7 periodo, replace

* líder = par município-prefeito, único no painel inteiro
gen str12 lider_s = string(cod_ibge7, "%07.0f") + "-" + prefeito
egen long lider = group(lider_s)

* painel do artigo: prefeito nos dez períodos e ao menos dois prefeitos diferentes
bysort cod_ibge7: gen byte n = _N
bysort cod_ibge7 lider: gen byte primeiro = _n == 1
bysort cod_ibge7: egen byte nlid = total(primeiro)
keep if n == 10 & nlid >= 2
drop n primeiro nlid lider_s prefeito
egen long unidade = group(cod_ibge7)

if `amostra' > 0 {
    preserve
    keep unidade
    duplicates drop
    sample `amostra', count
    tempfile sorteio
    save `sorteio'
    restore
    merge m:1 unidade using `sorteio', keep(match) nogenerate
}
sort unidade periodo

tempname res
postfile `res' str12 celula int base double pval using "output/stata_celulas.dta", replace
forvalues b = 1/`bases' {
    * ruído AR(1) gaussiano estacionário de variância 1, por município, no calendário
    gen double e = rnormal() if periodo == 1
    by unidade: replace e = `rho' * e[_n-1] + sqrt(1 - `rho'^2) * rnormal() if periodo > 1

    quietly rifle e lider periodo unidade, permnum(`perm') nograph
    post `res' ("sem_lacuna") (`b') (pval)

    gen double y = e
    replace y = . if periodo == 9      // lacuna no período 9 (o 1º meio-mandato depois da eleição de 2020)
    quietly rifle y lider periodo unidade, permnum(`perm') nograph
    post `res' ("p9_costura") (`b') (pval)
    quietly rifle y lider periodo unidade, permnum(`perm') nograph nostitch
    post `res' ("p9_nostitch") (`b') (pval)

    drop e y
    display "base `b' de `bases'"
}
postclose `res'

use "output/stata_celulas.dta", clear
gen byte rejeita = pval <= .05
collapse (mean) taxa = rejeita (count) bases = rejeita, by(celula)
list, noobs
