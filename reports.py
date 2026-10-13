from __future__ import annotations

from pathlib import Path

from database import DEFAULT_DB_PATH


class ReportService:
    '''Camada responsável pelos relatórios do Estoqium.

    As exportações CSV e TXT serão implementadas nas próximas etapas.
    '''

    def __init__(self, db_path: Path | str = DEFAULT_DB_PATH) -> None:
        self.db_path = Path(db_path)
