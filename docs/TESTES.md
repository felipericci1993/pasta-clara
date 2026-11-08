# Verificação do Pasta Clara

## Validação do commit atual

Situação conferida em **08/11/2026** para o commit [735d7a1](https://github.com/felipericci1993/pasta-clara/commit/735d7a1a85f350dafb596c24daf8431ff13138c6), que corrigiu a validação de caminhos com `..`.

- **CI aprovado em 07/11/2026:** [execução 42386911346](https://github.com/felipericci1993/pasta-clara/actions/runs/42386911346), no mesmo commit. Os três jobs Ubuntu, com Python 3.11, 3.12 e 3.13, concluíram os **30 testes** e a compilação de `pasta_clara` com sucesso.
- **Verificação local repetida em 08/11/2026:** Linux, Python 3.12.14, em uma cópia dos arquivos desse commit. Passaram os 30 testes, a execução separada das 9 regressões de caminhos, a demonstração, a ajuda da CLI e a compilação de módulos, exemplo e testes. Todos os comandos terminaram com código 0.
- Os 30 testes são os **21 anteriores mais 9 regressões**; a execução separada não representa testes adicionais. Foram usados somente diretórios temporários e dados fictícios.

### Caso corrigido

A versão anterior simplificava `..` antes de procurar links simbólicos. Isso podia esconder um link e selecionar uma pasta diferente da indicada pelo caminho original. Por exemplo, se `atalho` aponta para `outra/subpasta`, o sistema interpreta `atalho/../saida` como `outra/saida`; remover `atalho/..` antes da verificação selecionaria `saida`.

A validação agora examina os componentes originais antes de normalizar o caminho. Recusa links simbólicos, arquivos usados como pastas e pastas inexistentes antes de `..`. Caminhos com `..` passando por pastas reais continuam aceitos, e origem e destino iguais ou sobrepostos continuam recusados.

As [9 regressões](../tests/test_paths.py) cobrem origem e destino, caminhos absolutos e relativos, links válidos e quebrados, componentes inválidos, uso permitido de `..`, sobreposição e recusa pela CLI com `--aplicar` sem criar o destino nem copiar arquivos.

### Repetir a verificação

Na raiz de uma cópia do projeto com o commit indicado:

```bash
python -B -m unittest discover -s tests -p test_paths.py -v
python -B -m unittest discover -s tests -v
python -B examples/demonstrar.py
python -B -m pasta_clara --help
python -m compileall -q pasta_clara examples tests
```

`compileall` cria caches Python. Na verificação local desta revisão, `PYTHONPYCACHEPREFIX` apontou para uma pasta temporária, removida depois da compilação. Os arquivos do projeto permaneceram iguais aos do commit durante os testes.

### Limites desta validação

Windows e macOS continuam sem execução real. Python 3.11 e 3.13 foram verificados somente no CI Linux. Não foram simuladas falhas reais de hardware, queda de energia, falta de espaço em disco ou concorrência contínua. Esta correção não é uma auditoria de segurança nem uma garantia contra alterações maliciosas concorrentes; use pastas sob seu controle e sem modificação simultânea.

## Registro inicial de 06/11/2026

O registro abaixo foi preservado. A contagem de 21 testes e os arquivos `test-results.txt` e `demo-results.txt` documentam a revisão inicial, não a execução atual de 30 testes.

Data: 06/11/2026. Ambiente verificado: Linux, Python 3.12.14. Todos os arquivos de teste foram criados em diretórios temporários com conteúdo fictício.

## Resultado

- **21 testes automatizados aprovados** com `unittest`.
- Demonstração completa executada: simulação, aplicação de três cópias, comparação dos bytes e preservação dos originais e do arquivo preexistente.
- Compilação dos módulos Python sem erro.
- Ajuda de linha de comando conferida.

Registros: [saída dos testes](test-results.txt) e [saída da demonstração](demo-results.txt).

Comandos para repetir:

```bash
python -B -m unittest discover -s tests -v
python -B examples/demonstrar.py
python -m compileall -q pasta_clara examples tests
```

`compileall` grava caches Python no diretório do projeto. Esses caches não fazem parte do pacote de entrega.

## Cobertura

1. Simulação sem criação de destino ou alteração dos bytes existentes.
2. Classificação por extensão, letras maiúsculas, tipo desconhecido e arquivo sem extensão.
3. Ignorar ocultos, diretórios, links simbólicos e entradas não regulares.
4. Cópia de conteúdo binário e preservação da origem.
5. Colisões de nomes e execução repetida sem sobrescrita.
6. Recusa de origens inválidas, origem/destino iguais ou sobrepostos.
7. Links simbólicos na origem, destino ou ancestrais.
8. Limites de entradas, quantidade, tamanho individual e total, sem gravação antes da recusa.
9. Mudança da origem após o plano e substituição por link simbólico.
10. Destino criado ou substituído por link após o plano.
11. Falha de escrita e mutação da origem durante a cópia, com remoção da parcial e preservação das cópias completas anteriores.
12. Recusa de reaplicação do mesmo plano desatualizado.
13. CLI em simulação por padrão, aplicação explícita, código de erro e rejeição de abreviações como `--a`.

## Revisão adicional

Uma revisão do código e reproduções sintéticas identificaram que o analisador de argumentos aceitava abreviações de `--aplicar`. Esse comportamento foi desativado e coberto por um teste. Não foi encontrada perda ou sobrescrita nas verificações realizadas.

Isso não é uma auditoria de segurança completa. Mudanças concorrentes maliciosas de diretórios não são suportadas, e as verificações de caminhos não eliminam todas as condições de corrida possíveis.

## Ainda não verificado

- Execução real em Windows e macOS.
- Execução fora do CI em Python 3.11 ou 3.13.
- Falhas reais de hardware, queda de energia, falta de espaço em disco e concorrência contínua.

## CI no GitHub

Na publicação inicial, a suíte e a compilação passaram em Linux com Python 3.11, 3.12 e 3.13. [Execução verificada](https://github.com/felipericci1993/pasta-clara/actions/runs/42296035570), correspondente ao commit `f639c316d4230ed5f28bea3dd59b3f8dc165ad0d`.

O workflow executa a suíte em Linux com Python 3.11, 3.12 e 3.13. O resultado remoto de cada commit está na [aba Actions](https://github.com/felipericci1993/pasta-clara/actions). As evidências locais acima não substituem esse resultado nem comprovam compatibilidade com Windows ou macOS.

A classificação é pelo nome, não pelo conteúdo. Não há deduplicação, preservação de metadados, criptografia, sincronização ou restauração automática do conjunto.
