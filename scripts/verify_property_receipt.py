#!/usr/bin/env python3
"""Offline independent reconstruction of PROPERTY-LAB/1 finite fixtures.

Checks internal bytes/semantics; never attests that a browser executed.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

PROTOCOL = 'PROPERTY-LAB/1'
FORMAT = 'PROPERTY-LAB-RECEIPT/1'
MASK = 0xffffffff
LIMITATIONS = [
    'The property sample is finite, not a proof of arbitrary JavaScript behaviour.',
    'The wraparound defect is deliberately injected inside this lab, not found in deployed evolve().',
    'The legacy mutable-fingerprint witness is a real public-API ownership counterexample.',
    'The guarded snapshot API is opt-in and does not make legacy buildAutomaton immutable.',
    'An exported SHA-256 receipt identifies payload bytes, not authentic browser execution.',
]


class ReceiptError(ValueError):
    pass


def strict_pairs(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ReceiptError('duplicate JSON key: ' + key)
        out[key] = value
    return out


def reject_float(value):
    raise ReceiptError('floating-point or nonfinite JSON value not allowed')


def read_json(text):
    try:
        return json.loads(text, object_pairs_hook=strict_pairs,
                          parse_float=reject_float, parse_constant=reject_float)
    except (ValueError, UnicodeError, RecursionError) as error:
        raise ReceiptError('invalid JSON: ' + str(error)) from error


def rng(seed):
    state = seed
    while True:
        state ^= (state << 13) & MASK
        state ^= state >> 17
        state ^= (state << 5) & MASK
        state &= MASK
        yield state


def cases(seed, count):
    next_int = rng(seed)
    out = []
    for _ in range(count):
        width = 1 + next(next_int) % 8
        rule = next(next_int) % 256
        mask = next(next_int) % (1 << width)
        out.append({'width': width, 'rule': rule, 'mask': mask})
    return out


def fnv1a(bits):
    h = 0x811c9dc5
    for bit in bits:
        h = ((h ^ bit) * 0x01000193) & MASK
    return f'{h:08x}'


def evolve(bits, rule):
    out = []
    for i, center in enumerate(bits):
        left = bits[i - 1] if i > 0 else 0
        right = bits[i + 1] if i + 1 < len(bits) else 0
        out.append((rule >> (4 * left + 2 * center + right)) & 1)
    return out


def model(rule, seed, width, height):
    next_int = rng(seed)
    state = [next(next_int) & 1 for _ in range(width)]
    state[width // 2] = 1
    cells = []
    for _ in range(height):
        cells.extend(state)
        state = evolve(state, rule)
    return cells


def expected_report(seed, trials):
    if type(seed) is not int or not 1 <= seed <= MASK or type(trials) is not int or not 1 <= trials <= 512:
        raise ReceiptError('unsupported seed/trial range')
    original = model(30, 314159, 8, 8)
    old_hash = fnv1a(original)
    changed = original[:]
    changed[0] ^= 1
    new_hash = fnv1a(changed)
    if old_hash == new_hash:
        raise ReceiptError('legacy counterexample unexpectedly absent')
    return {
        'protocol': PROTOCOL,
        'schema_version': 1,
        'seed': seed,
        'trials': trials,
        'generated_cases': cases(seed, trials),
        'generated_status': 'FINITE_GENERATED_CASES_PASSED',
        'mutant': {
            'kind': 'DELIBERATELY_INJECTED_WRAPAROUND',
            'original': {'width': 8, 'rule': 110, 'mask': 255},
            'minimized': {'width': 1, 'rule': 4, 'mask': 1},
            'candidates_checked': 10,
            'ordering': 'width,rule,mask',
            'status': 'INJECTED_MUTANT_COUNTEREXAMPLE',
        },
        'ownership': {
            'status': 'LEGACY_MUTABILITY_COUNTEREXAMPLE',
            'original': {'columns': 8, 'rows': 8, 'rule': 30, 'seed': 314159},
            'minimized': {'columns': 1, 'rows': 1, 'rule': 0, 'seed': 1},
            'legacy_stored': old_hash,
            'legacy_after_mutation': new_hash,
            'guarded_status': 'DEFENSIVE_COPY_CONFIRMED',
        },
        'limitations': LIMITATIONS,
        'proof_status': 'NOT_A_FORMAL_PROOF',
    }


def strict_equal(left, right):
    if type(left) is not type(right):
        return False
    if isinstance(right, dict):
        return left.keys() == right.keys() and all(strict_equal(left[key], value) for key, value in right.items())
    if isinstance(right, list):
        return len(left) == len(right) and all(strict_equal(a, b) for a, b in zip(left, right))
    return left == right


def verify(envelope):
    if type(envelope) is not dict or set(envelope) != {'format', 'algorithm', 'sha256', 'payload_text'}:
        raise ReceiptError('unexpected receipt envelope')
    if envelope['format'] != FORMAT or envelope['algorithm'] != 'SHA-256/UTF-8':
        raise ReceiptError('unsupported receipt format')
    payload = envelope['payload_text']
    sha = envelope['sha256']
    if type(payload) is not str or len(payload.encode('utf-8')) > 250_000:
        raise ReceiptError('invalid or excessive payload')
    if type(sha) is not str or re.fullmatch('[0-9a-f]{64}', sha) is None:
        raise ReceiptError('invalid SHA-256 syntax')
    if hashlib.sha256(payload.encode('utf-8')).hexdigest() != sha:
        raise ReceiptError('payload SHA-256 mismatch')
    record = read_json(payload)
    if type(record) is not dict:
        raise ReceiptError('report must be object')
    expected = expected_report(record.get('seed'), record.get('trials'))
    if not strict_equal(record, expected):
        raise ReceiptError('generated fixtures, witness or proof status mismatch')
    return {'valid': True, 'generated_cases': record['trials'], 'mutant_shrunk_to': [1, 4, 1],
            'ownership_counterexample': 'CONFIRMED_BY_REFERENCE_FIXTURE',
            'execution_attestation': 'NOT_INDEPENDENTLY_ESTABLISHED', 'sha256': sha}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('receipt', type=Path)
    args = parser.parse_args(argv)
    try:
        if args.receipt.stat().st_size > 350_000:
            raise ReceiptError('receipt file too large')
        result = verify(read_json(args.receipt.read_text(encoding='utf-8')))
    except (OSError, UnicodeError, ReceiptError, TypeError) as error:
        print('FAIL: ' + str(error), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
