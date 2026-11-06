"""Interface em português: python -m pasta_clara ORIGEM DESTINO [--aplicar]."""
import argparse
import sys
from .core import OrganizationError, apply_plan, make_plan


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog='python -m pasta_clara',
        description='Organize cópias por tipo. O padrão é SIMULAÇÃO, sem alterações.',
        epilog='Não há recursão. Links, pastas e arquivos ocultos são ignorados. '
               'Limites: 1.000 arquivos, 50 MiB por arquivo e 250 MiB no total.',
        add_help=False, allow_abbrev=False)
    parser._positionals.title = 'argumentos posicionais'
    parser._optionals.title = 'opções'
    parser.add_argument('-h', '--help', action='help', help='mostrar esta ajuda e sair')
    parser.add_argument('origem', help='pasta contendo os arquivos originais')
    parser.add_argument('destino', help='pasta separada para receber as cópias')
    parser.add_argument('--aplicar', action='store_true', help='copiar os arquivos de verdade')
    args = parser.parse_args(argv)
    try:
        plan = make_plan(args.origem, args.destino)
        print('APLICAÇÃO: cópia de arquivos.' if args.aplicar else 'SIMULAÇÃO: nada será criado ou alterado.')
        for item in plan.items:
            print(f'{item.source.name!r} → {str(item.destination.relative_to(plan.destination))!r} ({item.size} bytes)')
        print(f'{len(plan.items)} arquivo(s), {plan.total_bytes} bytes; {plan.ignored} entrada(s) ignorada(s).')
        if args.aplicar:
            print(f'Concluído: {apply_plan(plan)} cópia(s). Originais preservados.')
        else:
            print('Para copiar, repita o comando com --aplicar. O plano será recalculado.')
        return 0
    except OrganizationError as exc:
        print(f'Erro: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
