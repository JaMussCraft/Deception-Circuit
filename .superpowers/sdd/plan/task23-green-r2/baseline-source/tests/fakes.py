"""Fakes shared by the deception-task tests.

`FakeWordTokenizer` is a whitespace-level stand-in for the Llama tokenizer: every
whitespace-separated chunk is one token, ids are assigned on first sight from a
small contiguous vocabulary. That is enough to exercise the alignment
assertions (equal length, exactly one differing position) and the dataset /
filter plumbing on CPU without an 8B tokenizer download.

`ScriptedModel` returns logits scripted per forward call, so the behavioral and
prior-balance filters can be tested against known model behavior.
"""

from __future__ import annotations

from types import SimpleNamespace

import torch

FAKE_VOCAB_SIZE = 256


class FakeWordTokenizer:
    """Whitespace-level tokenizer. Deterministic within one instance."""

    pad_token = "<pad>"
    pad_token_id = 0
    eos_token = "<eos>"
    eos_token_id = 1

    def __init__(self):
        # 0/1 reserved for pad/eos.
        self.vocab = {"<pad>": 0, "<eos>": 1}

    def _id(self, piece: str) -> int:
        if piece not in self.vocab:
            if len(self.vocab) >= FAKE_VOCAB_SIZE:
                raise RuntimeError("FakeWordTokenizer vocabulary exhausted")
            self.vocab[piece] = len(self.vocab)
        return self.vocab[piece]

    def encode(self, text, add_special_tokens=False):
        return [self._id(p) for p in text.split()]

    def decode(self, ids, **kwargs):
        if isinstance(ids, int):
            ids = [ids]
        if torch.is_tensor(ids):
            ids = ids.reshape(-1).tolist()
        inv = {v: k for k, v in self.vocab.items()}
        return " ".join(inv.get(int(i), "<unk>") for i in ids)

    def __call__(self, text, padding=None, max_length=None, truncation=False,
                 add_special_tokens=False, return_tensors=None):
        ids = self.encode(text)
        if truncation and max_length is not None:
            ids = ids[:max_length]
        mask = [1] * len(ids)
        if padding == "max_length" and max_length is not None:
            pad = max_length - len(ids)
            ids = ids + [self.pad_token_id] * pad
            mask = mask + [0] * pad
        out = {"input_ids": ids, "attention_mask": mask}
        if return_tensors == "pt":
            out = {k: torch.tensor(v, dtype=torch.long).unsqueeze(0)
                   for k, v in out.items()}
        return out


class ScriptedModel:
    """Model stub whose logits are dictated per (call index, row).

    `script` is a list of per-forward-call lists; each inner list holds one
    {token_id: logit} dict per row of that batch. Every unlisted token gets
    logit -10. Calls are consumed in order, so tests must use a batch size that
    covers the whole dataset (one clean call, then one corrupt call).
    """

    def __init__(self, script, vocab_size=FAKE_VOCAB_SIZE):
        self.script = list(script)
        self.vocab_size = vocab_size
        self.calls = 0

    def eval(self):
        return self

    def __call__(self, input_ids=None, attention_mask=None, **kwargs):
        rows = self.script[self.calls]
        self.calls += 1
        b, l = input_ids.shape
        assert b == len(rows), f"scripted {len(rows)} rows, batch has {b}"
        logits = torch.full((b, l, self.vocab_size), -10.0)
        for i, spec in enumerate(rows):
            for tok, val in spec.items():
                logits[i, :, tok] = val
        return SimpleNamespace(logits=logits)
