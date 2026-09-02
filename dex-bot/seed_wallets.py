"""Import the supplied public wallet pool into PostgreSQL."""

import csv
import logging
from collections import defaultdict
from pathlib import Path

from wallets import save_wallets


logger = logging.getLogger(__name__)
DEFAULT_CSV = Path(__file__).with_name("wallets.csv")


def load_wallets(csv_path: Path) -> dict[str, list[str]]:
    wallets: dict[str, list[str]] = defaultdict(list)
    with csv_path.open(newline="", encoding="utf-8") as csv_file:
        for row in csv.DictReader(csv_file):
            blockchain = (row.get("blockchain") or "").strip()
            address = (row.get("address") or "").strip()
            if blockchain and address and row.get("active", "").lower() == "true":
                wallets[blockchain].append(address)
    return dict(wallets)


def main() -> None:
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )
    wallets = load_wallets(DEFAULT_CSV)
    total = 0
    for blockchain, addresses in wallets.items():
        saved = save_wallets(blockchain, addresses)
        total += saved
        logger.info("Imported %s active wallet(s) for %s", saved, blockchain)
    logger.info("Imported %s active wallet(s) across %s chain(s)", total, len(wallets))


if __name__ == "__main__":
    main()