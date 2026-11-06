"""Demonstração inteiramente temporária; não recebe caminhos pessoais."""
from pathlib import Path
import subprocess
import sys
import tempfile


def snapshot(root):
    return {str(path.relative_to(root)): path.read_bytes()
            for path in root.rglob('*') if path.is_file()}


def main():
    project = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix='pasta-clara-demo-') as temporary:
        root = Path(temporary)
        source, target = root / 'entrada-demo', root / 'saida-demo'
        source.mkdir()
        (source / 'anotacoes.txt').write_text('Exemplo fictício de organização.\n', encoding='utf-8')
        (source / 'vendas.csv').write_text('produto;quantidade\nProduto demo;3\n', encoding='utf-8')
        (source / 'icone.svg').write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20">'
            '<rect width="20" height="20" fill="#2563eb"/></svg>\n', encoding='utf-8')
        (source / '.rascunho.txt').write_text('Exemplo oculto, deve ser ignorado.\n', encoding='utf-8')
        (source / 'subpasta').mkdir()
        (source / 'subpasta' / 'ignorado.txt').write_text('Não percorrer subpastas.\n', encoding='utf-8')
        (target / 'documentos').mkdir(parents=True)
        (target / 'documentos' / 'anotacoes.txt').write_text('Arquivo de destino preexistente.\n', encoding='utf-8')
        original = snapshot(source)
        before = snapshot(root)
        command = [sys.executable, '-B', '-m', 'pasta_clara', str(source), str(target)]

        print('1. Simulação com dados fictícios', flush=True)
        subprocess.run(command, cwd=project, check=True)
        if snapshot(root) != before:
            raise RuntimeError('A simulação alterou arquivos.')

        print('\n2. Aplicação somente no ambiente temporário', flush=True)
        subprocess.run(command + ['--aplicar'], cwd=project, check=True)
        expected = {
            'documentos/anotacoes__2.txt': original['anotacoes.txt'],
            'planilhas/vendas.csv': original['vendas.csv'],
            'imagens/icone.svg': original['icone.svg'],
        }
        for name, content in expected.items():
            if (target / name).read_bytes() != content:
                raise RuntimeError(f'Conteúdo divergente: {name}')
        if snapshot(source) != original:
            raise RuntimeError('A origem foi alterada.')
        if (target / 'documentos/anotacoes.txt').read_bytes() != before['saida-demo/documentos/anotacoes.txt']:
            raise RuntimeError('O destino preexistente foi alterado.')
        print('\nVerificado: 3 cópias corretas, originais e destino preexistente preservados.')
        print('Os arquivos temporários desta demonstração serão removidos agora.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
