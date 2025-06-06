# Copyright 2024 MosaicML LLM Foundry authors
# SPDX-License-Identifier: Apache-2.0

import pathlib
from typing import Optional

import pytest
from composer import Trainer
from composer.models.huggingface import maybe_get_underlying_model
from transformers import PreTrainedModel, PreTrainedTokenizerBase

from llmfoundry.utils.builders import build_composer_model, build_tokenizer


@pytest.mark.world_size(2)
@pytest.mark.gpu
@pytest.mark.parametrize(
    'peft_config',
    [
        None,
        {
            'peft_type': 'LORA',
            'task_type': 'CAUSAL_LM',
            'lora_alpha': 32,
            'lora_dropout': 0.05,
            'r': 16,
            'target_modules': [
                'q_proj',
                'k_proj',
                'v_proj',
            ],
        },
    ],
)
@pytest.mark.parametrize('init_device', ['cpu', 'mixed', 'meta'])
def test_fsdp_weight_tying(
    peft_config: Optional[dict],
    tmp_path: pathlib.Path,
    init_device: str,
    tiny_codellama_model: PreTrainedModel,
    tiny_codellama_tokenizer: PreTrainedTokenizerBase,
):
    save_path = tmp_path / 'hf-save'
    tiny_codellama_model.save_pretrained(save_path)
    tiny_codellama_tokenizer.save_pretrained(save_path)

    model_cfg = {
        'name': 'hf_causal_lm',
        'pretrained_model_name_or_path': str(save_path),
        'config_overrides': {
            'num_hidden_layers': 2,
            'hidden_size': 32,
            'intermediate_size': 64,
            'tie_word_embeddings': True,
        },
        'pretrained': False,
        'init_device': init_device,
    }
    tokenizer_name = save_path

    assert model_cfg is not None
    assert tokenizer_name is not None
    if peft_config is not None:
        model_cfg['peft_config'] = peft_config

    fsdp_config = {
        'sharding_strategy': 'FULL_SHARD',
        'mixed_precision': 'PURE',
        'activation_checkpointing': False,
        'activation_checkpointing_reentrant': False,
        'activation_cpu_offload': False,
        'limit_all_gathers': True,
        'state_dict_type': 'full',
        'sync_module_states': True,
    }

    tokenizer = build_tokenizer(
        tokenizer_name=str(tokenizer_name),
        tokenizer_kwargs={'model_max_length': 32},
    )

    name = model_cfg.pop('name')
    original_model = build_composer_model(
        name=name,
        cfg=model_cfg,
        tokenizer=tokenizer,
    )

    underlying_model = maybe_get_underlying_model(original_model.model)
    lm_head = underlying_model.lm_head
    embedding_layer = underlying_model.model.embed_tokens if peft_config is None else underlying_model.model.embed_tokens  # type: ignore

    lm_head_id = id(lm_head.weight)  # type: ignore
    embedding_layer_id = id(embedding_layer.weight)  # type: ignore

    assert lm_head_id == embedding_layer_id

    trainer = Trainer(
        model=original_model,
        device='gpu',
        parallelism_config={'fsdp': fsdp_config},
        train_dataloader=[],
        device_train_microbatch_size=1,
    )

    model = trainer.state.model

    lm_head = model.model.lm_head if peft_config is None else model.model.base_model.model.lm_head  # type: ignore
    embedding_layer = model.model.model.embed_tokens if peft_config is None else model.model.base_model.model.model.embed_tokens  # type: ignore

    lm_head_id = id(lm_head.weight)  # type: ignore
    embedding_layer_id = id(embedding_layer.weight)  # type: ignore

    assert lm_head_id == embedding_layer_id
