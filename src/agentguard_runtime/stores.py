from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from agentguard_runtime.core import ExecutionReceipt


class ReceiptStore:
    def append(self, receipt: ExecutionReceipt) -> None:
        raise NotImplementedError

    def read_all(self) -> list[ExecutionReceipt]:
        raise NotImplementedError


class JsonlReceiptStore(ReceiptStore):
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def append(self, receipt: ExecutionReceipt) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(receipt.to_json() + "\n")

    def read_all(self) -> list[ExecutionReceipt]:
        if not self.path.exists():
            return []
        receipts = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                receipts.append(ExecutionReceipt(**json.loads(line)))
        return receipts


class SQLiteReceiptStore(ReceiptStore):
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def append(self, receipt: ExecutionReceipt) -> None:
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                """
                INSERT INTO receipts (
                    receipt_id, agent, tool, target, mode, status, reasons,
                    evidence_score, cost_usd, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    receipt.receipt_id,
                    receipt.agent,
                    receipt.tool,
                    receipt.target,
                    receipt.mode,
                    receipt.status,
                    json.dumps(receipt.reasons, ensure_ascii=False),
                    receipt.evidence_score,
                    receipt.cost_usd,
                    receipt.created_at,
                ),
            )

    def read_all(self) -> list[ExecutionReceipt]:
        if not self.path.exists():
            return []
        with sqlite3.connect(self.path) as connection:
            rows = connection.execute(
                """
                SELECT receipt_id, agent, tool, target, mode, status, reasons,
                       evidence_score, cost_usd, created_at
                FROM receipts
                ORDER BY rowid ASC
                """
            ).fetchall()
        return [
            ExecutionReceipt(
                receipt_id=row[0],
                agent=row[1],
                tool=row[2],
                target=row[3],
                mode=row[4],
                status=row[5],
                reasons=json.loads(row[6]),
                evidence_score=row[7],
                cost_usd=row[8],
                created_at=row[9],
            )
            for row in rows
        ]

    def _init_schema(self) -> None:
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS receipts (
                    receipt_id TEXT NOT NULL,
                    agent TEXT NOT NULL,
                    tool TEXT NOT NULL,
                    target TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    status TEXT NOT NULL,
                    reasons TEXT NOT NULL,
                    evidence_score REAL NOT NULL,
                    cost_usd REAL NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.execute("CREATE INDEX IF NOT EXISTS idx_receipts_agent ON receipts(agent)")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_receipts_status ON receipts(status)")


def open_receipt_store(path: str | Path, store_format: str = "jsonl") -> ReceiptStore:
    if store_format == "jsonl":
        return JsonlReceiptStore(path)
    if store_format == "sqlite":
        return SQLiteReceiptStore(path)
    raise ValueError(f"unsupported store format: {store_format}")
