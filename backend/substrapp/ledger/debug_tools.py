import json
from substrapp.ledger.connection import get_hfc
from pathlib import Path


def get_transactions(start_block, end_block):
    for block_number in range(start_block, end_block + 1):
        block = get_block(block_number)
        for tx_index, tx in enumerate(block['data']['data']):
            if "actions" not in tx['payload']['data']:
                # not an invoke
                continue
            input = tx['payload']['data']['actions'][0]['payload']['chaincode_proposal_payload']['input']
            if ('ApproveChaincode' not in str(input)):
                print(f"block: {block_number}, tx_index: {tx_index}")
                yield block_number, tx_index, tx


def get_block(block_number):
    with get_hfc('mychannel') as (loop, client, user):
        block = loop.run_until_complete(client.query_block(
            user,
            'mychannel',
            ['peer'],
            str(block_number),
            decode=True))
        return block


def dump_all_blocks(start_block, end_block, out_folder):
    """Dump all the blocks from `start_block` to `end_block` as JSON files in `out_folder`.
    Files are named "{block_number}.{transaction_index}.json", e.g. "0123,0.json"
    """
    for block_number, tx_index, tx in get_transactions(start_block, end_block):
        dump_block(block_number, tx_index, tx, out_folder)


def dump_block(block_number, tx_index, tx, out_folder):
    path = Path(out_folder)
    path.mkdir(parents=True, exist_ok=True)
    with open(path / f"{block_number:04},{tx_index}.json", "w") as json_file:
        json.dump(_make_jsonifiable(tx), json_file, indent=2)


def _make_jsonifiable(x):
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
