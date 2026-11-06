# Pasta Clara

**Veja o plano primeiro. Organize cópias depois.**

Um organizador de arquivos em Python que separa cópias por tipo, preserva os originais e evita sobrescrever o que já existe no destino. O modo padrão é **simulação**, sem criar pastas ou arquivos.

Projeto de estudo e portfólio. Os exemplos e testes usam apenas dados fictícios. Não representa um serviço realizado para cliente.

## Comece pela demonstração

Requisito: **Python 3.11 ou superior**. Não precisa instalar pacotes.

Na pasta do projeto:

```bash
python -B examples/demonstrar.py
```

O exemplo cria uma pequena pasta temporária com texto, CSV e SVG fictícios, mostra a simulação, aplica a cópia e confere os resultados. Ele também demonstra uma colisão de nomes. Ao terminar, remove somente o ambiente temporário que criou.

Em alguns sistemas, use `python3` ou `py` no lugar de `python`.

A opção `-B` evita que o próprio Python grave arquivos de cache no diretório do projeto.

## Como usar

Comece com uma pasta de teste e mantenha backup dos arquivos importantes.

```bash
python -B -m pasta_clara "entrada-demo" "saida-demo"
```

Esse comando **não grava nada**. Mostra o nome de cada arquivo e a categoria de destino. Para efetivamente criar as cópias:

```bash
python -B -m pasta_clara "entrada-demo" "saida-demo" --aplicar
```

O plano é recalculado quando o comando é executado novamente. Revise o que aparece no terminal. A origem e o destino precisam ser pastas separadas, sem uma estar dentro da outra.

Para consultar a ajuda:

```bash
python -B -m pasta_clara --help
```

## Organização por tipo

| Categoria | Exemplos de extensão |
| --- | --- |
| `documentos` | `.pdf`, `.txt`, `.docx`, `.md` |
| `planilhas` | `.csv`, `.xlsx`, `.ods` |
| `imagens` | `.jpg`, `.png`, `.svg`, `.webp` |
| `audio` | `.mp3`, `.wav`, `.flac` |
| `videos` | `.mp4`, `.mov`, `.mkv` |
| `compactados` | `.zip`, `.gz`, `.7z` |
| `codigo` | `.py`, `.js`, `.html`, `.json` |
| `sem_extensao` | arquivos sem extensão |
| `outros` | extensões não listadas |

A classificação considera a última extensão, sem diferenciar maiúsculas e minúsculas. Por exemplo, `foto.PNG` vai para `imagens` e `backup.tar.gz` vai para `compactados`. O conteúdo não é aberto para descobrir seu tipo.

## Proteções e comportamento

- A simulação não cria pastas nem arquivos.
- A aplicação **copia**, sem mover ou apagar os originais.
- Um nome já ocupado recebe um sufixo: `anotacoes__2.txt`, `anotacoes__3.txt` e assim por diante. Não há sobrescrita.
- Repetir a aplicação cria novas cópias. Não há deduplicação por conteúdo.
- Pastas, links simbólicos e arquivos ocultos são ignorados. Não há busca recursiva.
- Links simbólicos nos caminhos de origem, destino ou categorias são recusados.
- O programa compara identidade, tamanho e datas dos arquivos antes e durante a cópia para detectar alterações.
- A primeira falha interrompe a execução. Cópias completas anteriores permanecem; uma cópia parcial criada na falha normal é removida.

### Limites

Até **1.000 arquivos**, **5.000 entradas examinadas**, **50 MiB por arquivo** e **250 MiB no total**. Se a pasta ultrapassar um limite, o plano é recusado antes das cópias.

Só os bytes são copiados. Datas, permissões e outros metadados da origem não são preservados. O destino usa as permissões padrão do sistema.

Uma interrupção abrupta, como queda de energia, pode deixar uma cópia parcial. Pastas criadas e cópias concluídas não são desfeitas automaticamente. O programa não reserva espaço em disco.

**Use pastas sob seu controle e que não estejam sendo modificadas por outros programas.** As verificações reduzem erros acidentais, mas não protegem contra alterações maliciosas concorrentes no sistema de arquivos. A ferramenta não detecta dados confidenciais, não criptografa arquivos e não substitui backup ou antivírus. Um arquivo copiado pode continuar contendo informação privada.

## Testes

```bash
python -B -m unittest discover -s tests -v
python -m compileall -q pasta_clara examples
```

Os testes usam diretórios temporários e dados sintéticos. O registro de execução e as limitações verificadas estão em [docs/TESTES.md](docs/TESTES.md). O workflow de CI cobre Python 3.11, 3.12 e 3.13 no GitHub. Consulte a aba [Actions](https://github.com/felipericci1993/pasta-clara/actions) para o resultado de cada commit; a configuração sozinha não comprova aprovação.

## Estrutura

```text
pasta_clara/
  core.py          planejamento, validação e cópia
  __main__.py      comandos e mensagens de terminal
examples/
  demonstrar.py    demonstração isolada com dados fictícios
tests/             testes automatizados
docs/              caso de portfólio e evidências
```

[Caso de portfólio](docs/CASO-DE-PORTFOLIO.md) · [Resultados dos testes](docs/TESTES.md)

Não há licença de código aberto definida para este projeto.
