# Verificação do Pasta Clara

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
- Execução local em Python 3.11 ou 3.13; a matriz de CI está apenas preparada.
- Falhas reais de hardware, queda de energia, falta de espaço em disco e concorrência contínua.

## CI no GitHub

O workflow executa a suíte em Linux com Python 3.11, 3.12 e 3.13. O resultado remoto de cada commit está na [aba Actions](https://github.com/felipericci1993/pasta-clara/actions). As evidências locais acima não substituem esse resultado nem comprovam compatibilidade com Windows ou macOS.

A classificação é pelo nome, não pelo conteúdo. Não há deduplicação, preservação de metadados, criptografia, sincronização ou restauração automática do conjunto.
