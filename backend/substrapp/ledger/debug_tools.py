import json
from substrapp.ledger.connection import get_hfc
from pathlib import Path
from django.conf import settings
from typing import Generator, Dict, List


def dump_all_transactions(channel_name: str, start_block: int, end_block: int, out_folder: str) -> None:
    """Dump all the blocks from `start_block` to `end_block` as JSON files in `out_folder`.
    Files are named "{block_number},{transaction_index}.json", e.g. "0123,0.json"
    """
    for block_number, tx_index, tx in get_transactions(channel_name, start_block, end_block):
        dump_transaction(block_number, tx_index, tx, out_folder)


def get_mvcc_transactions(channel_name: str, start_block: int, end_block: int) -> List[Dict]:
    """Get the list of transactions which have a MVCC conflict.

    Example usage:

      end_block = get_ledger_height('mychannel')
      txs = get_mvcc_transactions('mychannel', 0, end_block)
      txs[0]
      # {
      #     'block_number': 43,
      #     'tx_index': 1,
      #     'tx_id': 'fd31631d86e961caf97800d9ff5fae4b12b59ca20c364dc4868408f3c89e6c58'
      # }
    """
    res = []
    for block_number in range(start_block, end_block + 1):
        block = get_block(channel_name, block_number)
        for tx_index, tx in enumerate(block['data']['data']):
            tx_id = tx['payload']['header']['channel_header']['tx_id']
            if not tx_id:
                continue
            tx = get_transaction(channel_name, tx_id)
            if tx['validation_code'] == 11:  # MVCC_READ_CONFLICT = 11
                res.append({
                    'block_number': block_number,
                    'tx_index': tx_index,
                    'tx_id': tx_id
                })
    return res


def get_ledger_height(channel_name: str) -> int:
    """Return the highest block number in the ledger (aka ledger height)"""
    with get_hfc(channel_name) as (loop, client, user):
        info = loop.run_until_complete(client.query_info(
            user,
            channel_name,
            [settings.LEDGER_PEER_NAME],
            decode=True))
        return info.height


def get_transactions(channel_name: str, start_block: int, end_block: int) -> Generator:
    for block_number in range(start_block, end_block + 1):
        block = get_block(channel_name, block_number)
        for tx_index, tx in enumerate(block['data']['data']):
            if "actions" not in tx['payload']['data']:
                # not an invoke
                continue
            input = tx['payload']['data']['actions'][0]['payload']['chaincode_proposal_payload']['input']
            if ('ApproveChaincode' not in str(input)):
                print(f"block: {block_number}, tx_index: {tx_index}")
                yield block_number, tx_index, tx


def get_block(channel_name: str, block_number: int) -> Dict:
    with get_hfc(channel_name) as (loop, client, user):
        block = loop.run_until_complete(client.query_block(
            user,
            channel_name,
            [settings.LEDGER_PEER_NAME],
            str(block_number),
            decode=True))
        return block


def get_transaction(channel_name: str, tx_id: str) -> Dict:
    with get_hfc(channel_name) as (loop, client, user):
        transaction = loop.run_until_complete(client.query_transaction(
            user,
            channel_name,
            [settings.LEDGER_PEER_NAME],
            tx_id=tx_id,
            decode=True))
        return transaction


def dump_transaction(block_number: int, tx_index: int, tx: Dict, out_folder: str) -> None:
    path = Path(out_folder)
    path.mkdir(parents=True, exist_ok=True)
    with open(path / f"{block_number:04},{tx_index}.json", "w") as json_file:
        json.dump(_make_jsonifiable(tx), json_file, indent=2)


def _make_jsonifiable(x: Dict) -> Dict:
    if type(x) == bytes:
        return str(x)
    if type(x) == dict:
        res = {}
        for k, v in x.items():
            res[k] = _make_jsonifiable(v)
        return res
    if type(x) == list:
        res = []
        for _, v in enumerate(x):
            res.append(_make_jsonifiable(v))
        return res
    else:
        return str(x)
