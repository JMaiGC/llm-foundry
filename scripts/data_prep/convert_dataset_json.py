# Copyright 2022 MosaicML LLM Foundry authors
# SPDX-License-Identifier: Apache-2.0
"""Streaming dataset conversion scripts for json files."""
from argparse import ArgumentParser, Namespace

from llmfoundry.command_utils import convert_dataset_json_from_args


def parse_args() -> Namespace:
    """Parse commandline arguments."""
    parser = ArgumentParser(
        description=
        'Convert dataset into MDS format, optionally concatenating and tokenizing',
    )
    parser.add_argument('--path', type=str, required=True)
    parser.add_argument('--out_root', type=str, required=True)
    parser.add_argument('--compression', type=str, default=None)

    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument(
        '--concat_tokens',
        type=int,
        help='Convert text to tokens and concatenate up to this many tokens',
    )
    parser.add_argument('--split', type=str, default='train')

    parser.add_argument('--tokenizer', type=str, required=False, default=None)
    parser.add_argument('--bos_text', type=str, required=False, default=None)
    parser.add_argument('--eos_text', type=str, required=False, default=None)
    parser.add_argument('--no_wrap', default=False, action='store_true')

    parsed = parser.parse_args()
    return parsed


if __name__ == '__main__':
    args = parse_args()
    convert_dataset_json_from_args(
        path=args.path,
        out_root=args.out_root,
        compression=args.compression,
        concat_tokens=args.concat_tokens,
        split=args.split,
        tokenizer=args.tokenizer,
        bos_text=args.bos_text,
        eos_text=args.eos_text,
        no_wrap=args.no_wrap,
    )
