"""Planejamento sem efeitos e cópia conservadora, sem recursão.

Não execute em pastas modificadas simultaneamente por outros processos. As
checagens reduzem riscos acidentais, mas não são uma barreira contra alterações
maliciosas concorrentes no sistema de arquivos.
"""
from dataclasses import dataclass
import os
from pathlib import Path
import stat

MAX_FILES = 1_000
MAX_ENTRIES = 5_000
MAX_FILE_BYTES = 50 * 1024 * 1024
MAX_TOTAL_BYTES = 250 * 1024 * 1024
CHUNK_SIZE = 1024 * 1024
GROUPS = {
    'imagens': {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp'},
    'documentos': {'.pdf', '.txt', '.doc', '.docx', '.odt', '.md', '.rtf'},
    'planilhas': {'.csv', '.xlsx', '.xls', '.ods', '.tsv'},
    'audio': {'.mp3', '.wav', '.ogg', '.flac', '.m4a'},
    'videos': {'.mp4', '.mov', '.avi', '.mkv', '.webm'},
    'compactados': {'.zip', '.gz', '.tar', '.7z', '.rar'},
    'codigo': {'.py', '.js', '.html', '.css', '.json', '.sql'},
}


class OrganizationError(Exception):
    """Falha segura; cópias anteriores completas podem permanecer no destino."""


@dataclass(frozen=True)
class CopyItem:
    source: Path
    destination: Path
    fingerprint: tuple[int, int, int, int, int]

    @property
    def size(self) -> int:
        return self.fingerprint[2]


@dataclass(frozen=True)
class Plan:
    source: Path
    destination: Path
    items: tuple[CopyItem, ...]
    ignored: int

    @property
    def total_bytes(self) -> int:
        return sum(item.size for item in self.items)


def _fingerprint(info: os.stat_result) -> tuple[int, int, int, int, int]:
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def _checked_path(value: str | Path) -> Path:
    # Do not resolve symlinks before examining every component.
    path = Path(os.path.abspath(os.fspath(value)))
    for component in [*reversed(path.parents), path]:
        if component.is_symlink():
            raise OrganizationError(f'Link simbólico não permitido no caminho: {component}')
        if component.exists() and not component.is_dir():
            raise OrganizationError(f'O caminho precisa ser uma pasta: {component}')
    return path


def _roots(source: str | Path, destination: str | Path) -> tuple[Path, Path]:
    src, dst = _checked_path(source), _checked_path(destination)
    if not src.is_dir():
        raise OrganizationError(f'A origem não existe ou não é uma pasta: {src}')
    if src == dst or src in dst.parents or dst in src.parents:
        raise OrganizationError('Origem e destino não podem ser iguais ou estar um dentro do outro.')
    return src, dst


def _category(path: Path) -> str:
    if not path.suffix:
        return 'sem_extensao'
    return next((name for name, extensions in GROUPS.items()
                 if path.suffix.lower() in extensions), 'outros')


def _available(path: Path, reserved: set[Path]) -> Path:
    candidate, number = path, 2
    while os.path.lexists(candidate) or candidate in reserved:
        if number > MAX_ENTRIES:
            raise OrganizationError(f'Excesso de colisões de nomes: {path.name}')
        candidate = path.with_name(f'{path.stem}__{number}{path.suffix}')
        number += 1
    reserved.add(candidate)
    return candidate


def make_plan(source: str | Path, destination: str | Path) -> Plan:
    """Valida tudo e retorna um plano; não cria nem altera arquivos/pastas."""
    try:
        src, dst = _roots(source, destination)
        entries = []
        with os.scandir(src) as scan:
            for entry in scan:
                entries.append(Path(entry.path))
                if len(entries) > MAX_ENTRIES:
                    raise OrganizationError(f'Limite de {MAX_ENTRIES} entradas na origem excedido.')
        items, reserved, ignored, total = [], set(), 0, 0
        for path in sorted(entries, key=lambda p: p.name):
            info = path.lstat()
            hidden = path.name.startswith('.') or bool(
                getattr(info, 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_HIDDEN', 2))
            if hidden or not stat.S_ISREG(info.st_mode):
                ignored += 1
                continue
            if info.st_size > MAX_FILE_BYTES:
                raise OrganizationError(f'Arquivo acima de 50 MiB: {path.name}')
            total += info.st_size
            if len(items) >= MAX_FILES or total > MAX_TOTAL_BYTES:
                raise OrganizationError('Limite de 1.000 arquivos ou 250 MiB por execução excedido.')
            folder = _checked_path(dst / _category(path))
            target = _available(folder / path.name, reserved)
            items.append(CopyItem(path, target, _fingerprint(info)))
        return Plan(src, dst, tuple(items), ignored)
    except OSError as exc:
        raise OrganizationError(f'Não foi possível examinar as pastas: {exc}') from exc


def _copy_bytes(source, destination, expected_size: int) -> None:
    remaining = expected_size
    while remaining:
        block = source.read(min(CHUNK_SIZE, remaining))
        if not block:
            raise OrganizationError('Arquivo de origem foi reduzido durante a cópia.')
        destination.write(block)
        remaining -= len(block)
    if source.read(1):
        raise OrganizationError('Arquivo de origem cresceu durante a cópia.')


def apply_plan(plan: Plan) -> int:
    """Copia explicitamente. Para no primeiro erro; não desfaz cópias completas.

    A cópia parcial criada nesta execução é removida em falhas normais. Uma
    interrupção abrupta (queda de energia, kill) pode deixar cópia parcial.
    Metadados/permissões da origem não são preservados, somente os bytes.
    """
    completed = 0
    try:
        _roots(plan.source, plan.destination)
        # Revalidate the full snapshot before any writes.
        for item in plan.items:
            if item.source.parent != plan.source or item.destination.parent.parent != plan.destination:
                raise OrganizationError('Plano com caminhos fora das pastas autorizadas.')
            _checked_path(item.destination.parent)
            info = item.source.lstat()
            if not stat.S_ISREG(info.st_mode) or _fingerprint(info) != item.fingerprint:
                raise OrganizationError(f'Origem alterada desde a simulação: {item.source.name}')
            if os.path.lexists(item.destination):
                raise OrganizationError(f'Destino já existe; faça uma nova simulação: {item.destination}')
        for item in plan.items:
            _checked_path(item.source.parent)
            _checked_path(item.destination.parent)
            flags = os.O_RDONLY | getattr(os, 'O_BINARY', 0) | getattr(os, 'O_NOFOLLOW', 0)
            with os.fdopen(os.open(item.source, flags), 'rb') as reader:
                if _fingerprint(os.fstat(reader.fileno())) != item.fingerprint:
                    raise OrganizationError(f'Origem alterada: {item.source.name}')
                item.destination.parent.mkdir(parents=True, exist_ok=True)
                _checked_path(item.destination.parent)
                created_identity = None
                try:
                    # Exclusive creation never truncates an existing file.
                    with item.destination.open('xb') as writer:
                        created = os.fstat(writer.fileno())
                        created_identity = (created.st_dev, created.st_ino)
                        _copy_bytes(reader, writer, item.size)
                        if (_fingerprint(os.fstat(reader.fileno())) != item.fingerprint
                                or _fingerprint(item.source.lstat()) != item.fingerprint):
                            raise OrganizationError(f'Origem alterada durante a cópia: {item.source.name}')
                    completed += 1
                except BaseException:
                    if created_identity is not None:
                        current = item.destination.lstat()
                        if (current.st_dev, current.st_ino) == created_identity:
                            item.destination.unlink()
                    raise
        return completed
    except (OSError, OrganizationError) as exc:
        raise OrganizationError(f'Operação interrompida após {completed} cópia(s) completa(s): {exc}') from exc
