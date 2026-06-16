"""
analysis.py — circuit analysis & reporting utilities (model-agnostic).

Combines two pieces of functionality used by the two-phase pipeline:

  * NODE analysis  — `analyze_and_finalize_circuit` enforces hierarchical
    gate consistency, sets the model to deterministic "final circuit" mode,
    and returns per-granularity + prunable-parameter compression statistics.
    Works for both GPT-2 and Llama (see `_get_model_info`).

  * EDGE analysis  — extract surviving nodes from a node-pruned model, count
    the dense edges between them, and report active edges after edge pruning.

Vendored and de-duplicated from the original `utils.py` (node side) and
`edge_pruning/utils.py` (edge side).
"""

import json
import os
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Set, Tuple, Optional
from tqdm import tqdm

from l0 import HardConcreteGate


# ##############################################################################
# NODE-LEVEL ANALYSIS (GPT-2 / Llama)
# ##############################################################################

def _get_model_info(model):
    """
    Extract model-type-agnostic information from either GPT-2 or Llama models.
    Returns a dict with normalized keys regardless of architecture.
    """
    config = model.config
    model_type = getattr(config, 'model_type', 'gpt2')
    
    if model_type == 'llama':
        return {
            'model_type': 'llama',
            'hidden_size': config.hidden_size,
            'num_heads': config.num_attention_heads,
            'head_dim': config.hidden_size // config.num_attention_heads,
            'num_layers': config.num_hidden_layers,
            'intermediate_size': config.intermediate_size,
            'num_kv_heads': config.num_key_value_heads,
            'layers': model.model.layers,
            # Llama uses separate q/k/v/o projections (no bias)
            'attn_has_bias': False,
            'mlp_has_bias': False,
            # Llama SwiGLU has gate_proj + up_proj -> down_proj
            'num_mlp_projections': 3,
        }
    else:  # GPT-2
        return {
            'model_type': 'gpt2',
            'hidden_size': config.hidden_size,
            'num_heads': config.n_head,
            'head_dim': config.hidden_size // config.n_head,
            'num_layers': config.n_layer,
            'intermediate_size': config.n_inner if config.n_inner is not None else 4 * config.hidden_size,
            'num_kv_heads': config.n_head,  # GPT-2 has MHA (no GQA)
            'layers': model.transformer.h,
            'attn_has_bias': True,
            'mlp_has_bias': True,
            'num_mlp_projections': 2,
        }


def analyze_prunable_compression(model, layer_report_data, config, verbose=True):
    """
    Calculate compression based ONLY on prunable parameters:
    - Exclude: embeddings, positional embeddings, layer norms, LM head
    - Include: Only attention and MLP weight matrices that can be pruned
    Supports both GPT-2 and Llama models.
    """
    
    info = _get_model_info(model)
    hidden_size = info['hidden_size']
    num_heads = info['num_heads']
    head_dim = info['head_dim']
    intermediate_size = info['intermediate_size']
    num_layers = info['num_layers']
    num_kv_heads = info['num_kv_heads']
    
    # --- CALCULATE TOTAL PRUNABLE PARAMETERS ---
    total_prunable_params = 0
    bias_size = lambda n: n if info['attn_has_bias'] else 0
    mlp_bias = lambda n: n if info['mlp_has_bias'] else 0
    
    # Per layer prunable parameters
    for layer_idx in range(num_layers):
        if info['model_type'] == 'llama':
            # Llama: separate q_proj, k_proj, v_proj, o_proj (no bias)
            q_params = hidden_size * (num_heads * head_dim)
            k_params = hidden_size * (num_kv_heads * head_dim)
            v_params = hidden_size * (num_kv_heads * head_dim)
            o_params = (num_heads * head_dim) * hidden_size
            total_attention_params = q_params + k_params + v_params + o_params
            
            # Llama SwiGLU: gate_proj, up_proj, down_proj (no bias)
            gate_params = hidden_size * intermediate_size
            up_params = hidden_size * intermediate_size
            down_params = intermediate_size * hidden_size
            total_mlp_params = gate_params + up_params + down_params
        else:
            # GPT-2: c_attn (combined QKV), c_proj
            attention_qkv_params = hidden_size * 3 * hidden_size + bias_size(3 * hidden_size)
            attention_proj_params = hidden_size * hidden_size + bias_size(hidden_size)
            total_attention_params = attention_qkv_params + attention_proj_params
            
            # GPT-2: c_fc, c_proj
            mlp_fc_params = hidden_size * intermediate_size + mlp_bias(intermediate_size)
            mlp_proj_params = intermediate_size * hidden_size + mlp_bias(hidden_size)
            total_mlp_params = mlp_fc_params + mlp_proj_params
        
        total_prunable_params += total_attention_params + total_mlp_params
    
    if verbose:
        print(f"\n📍 PRUNABLE PARAMETER BREAKDOWN:")
        print(f"  - Layers: {num_layers}")
        print(f"  - Attention params per layer: {total_attention_params:,}")
        print(f"  - MLP params per layer: {total_mlp_params:,}")
        print(f"  - Total per layer: {total_attention_params + total_mlp_params:,}")
        print(f"  - TOTAL PRUNABLE: {total_prunable_params:,}")
    
    # --- CALCULATE ACTIVE PRUNABLE PARAMETERS ---
    active_prunable_params = 0
    
    for i, report in enumerate(layer_report_data):
        if not report['layer_active']:
            continue  # Skip entirely pruned layers
            
        block = info['layers'][i]
        layer_active_params = 0
        
        # Active attention parameters (no block gate = implicitly active)
        if report.get('attn_block', 'Active') == 'Active':
            if hasattr(block.attn, 'neuron_gates') and block.attn.neuron_gates!=None:
                active_attention_neurons = (block.attn.neuron_gates() > 0.5).sum().item()
            else:
                active_attention_neurons = hidden_size
            
            # QKV: hidden_size → 3 * active_attention_neurons
            active_qkv_params = hidden_size * 3 * active_attention_neurons + 3 * active_attention_neurons
            
            # Output projection: active_attention_neurons → hidden_size
            active_proj_params = active_attention_neurons * hidden_size + hidden_size
            
            layer_attention_params = active_qkv_params + active_proj_params
            layer_active_params += layer_attention_params
            
            if verbose:
                print(f"  Layer {i} Attention: {active_attention_neurons}/{hidden_size} neurons → {layer_attention_params:,} params")
        
        # Active MLP parameters (no block gate = implicitly active)
        if report.get('mlp_block', 'Active') == 'Active':
            if hasattr(block.mlp, 'hidden_gates') and block.mlp.hidden_gates!=None:
                active_hidden_neurons = (block.mlp.hidden_gates() > 0.5).sum().item()
            else:
                active_hidden_neurons = intermediate_size
                
            if hasattr(block.mlp, 'output_gates') and block.mlp.output_gates!=None:
                active_output_neurons = (block.mlp.output_gates() > 0.5).sum().item()
            else:
                active_output_neurons = hidden_size
            
            # FC: hidden_size → active_hidden_neurons
            active_fc_params = hidden_size * active_hidden_neurons + active_hidden_neurons
            
            # Projection: active_hidden_neurons → active_output_neurons
            active_mlp_proj_params = active_hidden_neurons * active_output_neurons + active_output_neurons
            
            layer_mlp_params = active_fc_params + active_mlp_proj_params
            layer_active_params += layer_mlp_params
            
            if verbose:
                print(f"  Layer {i} MLP: {active_hidden_neurons}/{intermediate_size} hidden, {active_output_neurons}/{hidden_size} output → {layer_mlp_params:,} params")
        
        active_prunable_params += layer_active_params
        
        if verbose and layer_active_params > 0:
            print(f"  Layer {i} TOTAL: {layer_active_params:,} params")
    
    # --- CALCULATE COMPRESSION METRICS ---
    pruned_params = total_prunable_params - active_prunable_params
    compression_ratio = total_prunable_params / active_prunable_params if active_prunable_params > 0 else float('inf')
    reduction_percentage = (pruned_params / total_prunable_params) * 100
    
    # Calculate effective model compression including fixed params
    total_model_params = sum(p.numel() for p in model.parameters())
    fixed_params = total_model_params - total_prunable_params
    effective_model_params = fixed_params + active_prunable_params
    effective_compression = total_model_params / effective_model_params if effective_model_params > 0 else float('inf')
    
    if verbose:
        print(f"\n" + "="*80)
        print("  PRUNABLE PARAMETER COMPRESSION ANALYSIS")
        print("="*80)
        print(f"Total prunable parameters: {total_prunable_params:,}")
        print(f"Active prunable parameters: {active_prunable_params:,}")
        print(f"Pruned parameters: {pruned_params:,}")
        print(f"Compression ratio: {compression_ratio:.2f}x")
        print(f"Parameter reduction: {reduction_percentage:.1f}%")
        
        print(f"\n📍 MODEL BREAKDOWN:")
        print(f"  - Total model parameters: {total_model_params:,}")
        print(f"  - Fixed parameters (embeddings, norms, etc.): {fixed_params:,} ({fixed_params/total_model_params*100:.1f}%)")
        print(f"  - Prunable parameters: {total_prunable_params:,} ({total_prunable_params/total_model_params*100:.1f}%)")
        print(f"  - Active prunable parameters: {active_prunable_params:,} ({active_prunable_params/total_model_params*100:.1f}%)")
        
        print(f"\n🎯 EFFECTIVE MODEL COMPRESSION:")
        print(f"  - Effective model size: {effective_model_params:,} parameters")
        print(f"  - Overall compression: {effective_compression:.2f}x")
        print(f"  - Overall reduction: {(total_model_params - effective_model_params)/total_model_params*100:.1f}%")
    
    return {
        'total_prunable_params': total_prunable_params,
        'active_prunable_params': active_prunable_params,
        'compression_ratio': compression_ratio,
        'reduction_percentage': reduction_percentage,
        'total_model_params': total_model_params,
        'fixed_params': fixed_params,
        'effective_model_params': effective_model_params,
        'effective_compression': effective_compression
    }


def analyze_and_finalize_circuit(model: nn.Module, verbose: bool = True):
    """
    Analyzes a trained model with HardConcreteGates, pedantically enforces hierarchical
    consistency, prints detailed pruning statistics, and keeps the model in its
    final, hard-pruned inference mode. FOCUSED ON PRUNABLE PARAMETERS.
    """
    print("\n" + "="*80)
    print("  ANALYZING AND FINALIZING THE DISCOVERED CIRCUIT (PEDANTIC MODE)")
    print("="*80)

    model.eval()
    # Set to final mode to read and enforce deterministic 0/1 gate values
    model.set_final_circuit_mode(True)

    # --- 1. INITIALIZATION (model-agnostic) ---
    info = _get_model_info(model)
    config = model.config
    hidden_size = info['hidden_size']
    num_heads = info['num_heads']
    head_dim = info['head_dim']
    num_layers = info['num_layers']
    intermediate_size = info['intermediate_size']
    layers = info['layers']

    granularity_stats = {
        'embedding': {'total': 1, 'active': 0},
        'layer_level': {'total': num_layers, 'active': 0},
        'attention_blocks': {'total': 0, 'active': 0},
        'mlp_blocks': {'total': 0, 'active': 0},
        'attention_heads': {'total': 0, 'active': 0},
        'attention_neurons': {'total': 0, 'active': 0},
        'mlp_hidden': {'total': 0, 'active': 0},
        'mlp_output': {'total': 0, 'active': 0}
    }
    layer_report_data = []

    with torch.no_grad():
        # --- 2. HIERARCHICAL CONSISTENCY ENFORCEMENT ---
        # This section modifies the gates in-place to ensure strict hierarchy.
        
        layer_gates_status = [True] * num_layers
        if hasattr(model, 'layer_gates') and model.layer_gates is not None:
            for i, layer_gate in enumerate(model.layer_gates):
                if layer_gate is not None and (layer_gate() < 0.5).item():
                    layer_gates_status[i] = False

        for i, block in enumerate(layers):
            if not layer_gates_status[i]:
                # If layer is pruned, force everything inside it to be pruned
                if hasattr(block, 'attention_block_gate') and block.attention_block_gate is not None:
                    block.attention_block_gate.log_alpha.data.fill_(-1e6)
                if hasattr(block, 'mlp_block_gate') and block.mlp_block_gate is not None:
                    block.mlp_block_gate.log_alpha.data.fill_(-1e6)
                if hasattr(block.attn, 'head_gates') and block.attn.head_gates is not None:
                    block.attn.head_gates.log_alpha.data.fill_(-1e6)
                if hasattr(block.attn, 'neuron_gates') and block.attn.neuron_gates is not None:
                    block.attn.neuron_gates.log_alpha.data.fill_(-1e6)
                if hasattr(block.mlp, 'hidden_gates') and block.mlp.hidden_gates is not None:
                    block.mlp.hidden_gates.log_alpha.data.fill_(-1e6)
                if hasattr(block.mlp, 'output_gates') and block.mlp.output_gates is not None:
                    block.mlp.output_gates.log_alpha.data.fill_(-1e6)
                continue

            # Top-Down: Block -> Children
            if hasattr(block, 'attention_block_gate') and block.attention_block_gate is not None and (block.attention_block_gate() < 0.5).item():
                if hasattr(block.attn, 'head_gates') and block.attn.head_gates is not None:
                    block.attn.head_gates.log_alpha.data.fill_(-1e6)
                if hasattr(block.attn, 'neuron_gates') and block.attn.neuron_gates is not None:
                    block.attn.neuron_gates.log_alpha.data.fill_(-1e6)
            
            if hasattr(block, 'mlp_block_gate') and block.mlp_block_gate is not None and (block.mlp_block_gate() < 0.5).item():
                if hasattr(block.mlp, 'hidden_gates') and block.mlp.hidden_gates is not None:
                    block.mlp.hidden_gates.log_alpha.data.fill_(-1e6)
                if hasattr(block.mlp, 'output_gates') and block.mlp.output_gates is not None:
                    block.mlp.output_gates.log_alpha.data.fill_(-1e6)

            # Top-Down: Head -> Neurons
            if (hasattr(block.attn, 'head_gates') and block.attn.head_gates is not None and 
                hasattr(block.attn, 'neuron_gates') and block.attn.neuron_gates is not None):
                head_gates_mask = block.attn.head_gates() < 0.5
                if head_gates_mask.any():
                    neuron_log_alpha = block.attn.neuron_gates.log_alpha.view(num_heads, head_dim)
                    neuron_log_alpha[head_gates_mask, :] = -1e6

            # Bottom-Up: Neurons -> Head -> Block
            if (hasattr(block.attn, 'head_gates') and block.attn.head_gates is not None and 
                hasattr(block.attn, 'neuron_gates') and block.attn.neuron_gates is not None):
                neuron_mask_by_head = (block.attn.neuron_gates() < 0.5).view(num_heads, head_dim)
                all_neurons_pruned_mask = neuron_mask_by_head.all(dim=1)
                if all_neurons_pruned_mask.any():
                    block.attn.head_gates.log_alpha.data[all_neurons_pruned_mask] = -1e6
            
            if (hasattr(block.attn, 'head_gates') and block.attn.head_gates is not None and 
                (block.attn.head_gates() < 0.5).all().item()):
                if hasattr(block, 'attention_block_gate') and block.attention_block_gate is not None:
                    block.attention_block_gate.log_alpha.data.fill_(-1e6)

            # Bottom-Up: MLP Neurons -> Block
            if (hasattr(block, 'mlp_block_gate') and block.mlp_block_gate is not None and 
                hasattr(block.mlp, 'hidden_gates') and block.mlp.hidden_gates is not None and 
                hasattr(block.mlp, 'output_gates') and block.mlp.output_gates is not None):
                all_mlp_pruned = (block.mlp.hidden_gates() < 0.5).all() and (block.mlp.output_gates() < 0.5).all()
                if all_mlp_pruned:
                    block.mlp_block_gate.log_alpha.data.fill_(-1e6)

        # --- 2.5. LAYER-LEVEL BOTTOM-UP CONSISTENCY ---
        # Check if both attention and MLP blocks are pruned, then prune the entire layer
        if hasattr(model, 'layer_gates') and model.layer_gates is not None:
            for i, block in enumerate(layers):
                if i >= len(model.layer_gates) or model.layer_gates[i] is None:
                    continue
                    
                attention_block_pruned = False
                mlp_block_pruned = False
                
                # Check if attention block is pruned
                if hasattr(block, 'attention_block_gate') and block.attention_block_gate is not None:
                    attention_block_pruned = (block.attention_block_gate() < 0.5).item()
                else:
                    # If no attention block gate, consider it active (fallback)
                    attention_block_pruned = False
                
                # Check if MLP block is pruned  
                if hasattr(block, 'mlp_block_gate') and block.mlp_block_gate is not None:
                    mlp_block_pruned = (block.mlp_block_gate() < 0.5).item()
                else:
                    # If no MLP block gate, consider it active (fallback)
                    mlp_block_pruned = False
                
                # If both major components are pruned, prune the entire layer
                if attention_block_pruned and mlp_block_pruned:
                    model.layer_gates[i].log_alpha.data.fill_(-1e6)
                    layer_gates_status[i] = False
                    if verbose:
                        print(f"  🔧 Layer {i}: Both attention and MLP blocks pruned → Pruning entire layer")

        # --- 3. STATISTICS GATHERING (POST-ENFORCEMENT) ---
        if (hasattr(model, 'embedding_gate') and model.embedding_gate is not None and 
            (model.embedding_gate() > 0.5).item()):
            granularity_stats['embedding']['active'] = 1
        embedding_gate_status = "Active" if granularity_stats['embedding']['active'] > 0 else "Pruned"
        
        granularity_stats['layer_level']['active'] = int(sum(layer_gates_status))

        for i, block in enumerate(layers):
            layer_stats = {'layer': i, 'layer_active': layer_gates_status[i]}
            
            if hasattr(block, 'attention_block_gate') and block.attention_block_gate is not None:
                granularity_stats['attention_blocks']['total'] += 1
                is_active = (block.attention_block_gate() > 0.5).item()
                layer_stats['attn_block'] = "Active" if is_active else "Pruned"
                if is_active: granularity_stats['attention_blocks']['active'] += 1

            if hasattr(block, 'mlp_block_gate') and block.mlp_block_gate is not None:
                granularity_stats['mlp_blocks']['total'] += 1
                is_active = (block.mlp_block_gate() > 0.5).item()
                layer_stats['mlp_block'] = "Active" if is_active else "Pruned"
                if is_active: granularity_stats['mlp_blocks']['active'] += 1
            
            if hasattr(block.attn, 'head_gates') and block.attn.head_gates is not None:
                active_count = (block.attn.head_gates() > 0.5).sum().item()
                layer_stats['attn_heads'] = f"{int(active_count)}/{num_heads}"
                granularity_stats['attention_heads']['total'] += num_heads
                if layer_gates_status[i]: granularity_stats['attention_heads']['active'] += active_count
            
            if hasattr(block.attn, 'neuron_gates') and block.attn.neuron_gates is not None:
                active_count = (block.attn.neuron_gates() > 0.5).sum().item()
                total_count = len(block.attn.neuron_gates.log_alpha)
                layer_stats['attn_neurons'] = f"{int(active_count)}/{total_count}"
                granularity_stats['attention_neurons']['total'] += total_count
                if layer_gates_status[i]: granularity_stats['attention_neurons']['active'] += active_count
            
            if hasattr(block.mlp, 'hidden_gates') and block.mlp.hidden_gates is not None:
                active_count = (block.mlp.hidden_gates() > 0.5).sum().item()
                layer_stats['mlp_hidden'] = f"{int(active_count)}/{intermediate_size}"
                granularity_stats['mlp_hidden']['total'] += intermediate_size
                if layer_gates_status[i]: granularity_stats['mlp_hidden']['active'] += active_count

            if hasattr(block.mlp, 'output_gates') and block.mlp.output_gates is not None:
                active_count = (block.mlp.output_gates() > 0.5).sum().item()
                layer_stats['mlp_output'] = f"{int(active_count)}/{hidden_size}"
                granularity_stats['mlp_output']['total'] += hidden_size
                if layer_gates_status[i]: granularity_stats['mlp_output']['active'] += active_count
            
            layer_report_data.append(layer_stats)

    # --- 4. PRUNABLE PARAMETER COMPRESSION ANALYSIS ---
    prunable_stats = analyze_prunable_compression(model, layer_report_data, config, verbose)

    # --- 5. REPORTING ---
    if verbose:
        print("\n" + "="*80)
        print("  HIERARCHICAL PRUNING REPORT (Consistency Enforced)")
        print("="*80)
        
        print(f"\n📍 GLOBAL COMPONENTS:")
        print(f"  - Embedding Gate: {embedding_gate_status}")
        
        if granularity_stats['layer_level']['total'] > 0:
            active = granularity_stats['layer_level']['active']
            total = granularity_stats['layer_level']['total']
            print(f"\n📍 LAYER-LEVEL PRUNING:")
            print(f"  - Active Layers: {active}/{total} ({(active/total)*100:.1f}%)")
            if active < total:
                print(f"  - Pruned Layer Indices: {' '.join([str(i) for i, act in enumerate(layer_gates_status) if not act])}")
        
        print(f"\n📍 DETAILED LAYER REPORT:")
        header = f"{'Layer':<6} | {'Status':<8} | {'Attn Block':<11} | {'MLP Block':<10} | {'Attn Heads':<12} | {'Attn Neurons':<15} | {'MLP Hidden':<15} | {'MLP Output':<15}"
        print(header)
        print("-" * len(header))
        
        for stats in layer_report_data:
            layer_status = "Active" if stats.get('layer_active', True) else "PRUNED"
            attn_block = stats.get('attn_block', 'N/A')
            mlp_block = stats.get('mlp_block', 'N/A')
            attn_heads = stats.get('attn_heads', 'N/A')
            attn_neurons = stats.get('attn_neurons', 'N/A')
            mlp_hidden = stats.get('mlp_hidden', 'N/A')
            mlp_output = stats.get('mlp_output', 'N/A')
            
            if layer_status == "PRUNED":
                print(f"\033[90m{stats['layer']:<6} | {layer_status:<8} | {'---':<11} | {'---':<10} | {'---':<12} | {'---':<15} | {'---':<15} | {'---':<15}\033[0m")
            else:
                print(f"{stats['layer']:<6} | {layer_status:<8} | {attn_block:<11} | {mlp_block:<10} | {attn_heads:<12} | {attn_neurons:<15} | {mlp_hidden:<15} | {mlp_output:<15}")

    print("\n" + "="*80)
    print("  PRUNING SUMMARY BY GRANULARITY")
    print("="*80)
    
    for G, S in granularity_stats.items():
        if S['total'] > 0:
            name = G.replace('_', ' ').title()
            pruned_pct = (S['total'] - S['active']) / S['total'] * 100 if S['total'] > 0 else 0
            print(f"\n{name}:")
            print(f"  - Active: {S['active']:,} / {S['total']:,}  ({(100-pruned_pct):.1f}%)")
            print(f"  - Pruned: {S['total'] - S['active']:,} ({pruned_pct:.1f}%)")

    print(f"\n🎯 PRUNABLE PARAMETER BOTTOM LINE:")
    print(f"  - Circuit uses {prunable_stats['active_prunable_params']:,} out of {prunable_stats['total_prunable_params']:,} prunable parameters")
    print(f"  - Prunable compression: {prunable_stats['compression_ratio']:.1f}x")
    print(f"  - Prunable reduction: {prunable_stats['reduction_percentage']:.1f}%")
    
    # Compare with component statistics for sanity check
    # print(f"\n🔍 SANITY CHECK (should align):")
    # print(f"  - Active layers: {granularity_stats['layer_level']['active']}/{granularity_stats['layer_level']['total']} ({granularity_stats['layer_level']['active']/granularity_stats['layer_level']['total']*100:.1f}%)")
    # print(f"  - Active attention neurons: {granularity_stats['attention_neurons']['active']}/{granularity_stats['attention_neurons']['total']} ({granularity_stats['attention_neurons']['active']/granularity_stats['attention_neurons']['total']*100:.1f}%)")
    # total_mlp_neurons = granularity_stats['mlp_hidden']['total'] + granularity_stats['mlp_output']['total']
    # active_mlp_neurons = granularity_stats['mlp_hidden']['active'] + granularity_stats['mlp_output']['active']
    # print(f"  - Active MLP neurons: {active_mlp_neurons}/{total_mlp_neurons} ({active_mlp_neurons/total_mlp_neurons*100:.1f}%)")
    
    print("="*80)
    print("\n✅ Model remains in 'Final Circuit Mode' for evaluation.")
    
    return {
        'granularity_stats': granularity_stats,
        'layer_report': layer_report_data,
        'prunable_compression': prunable_stats
    }


# ##############################################################################
# EDGE-LEVEL ANALYSIS
# ##############################################################################

# ==============================================================================
# NODE EXTRACTION
# ==============================================================================

def extract_active_nodes(node_pruned_model) -> Tuple[Dict[int, List[int]], Set[int]]:
    """
    Extract active attention heads and MLP blocks from a node-pruned model
    (after analyze_and_finalize_circuit has been called).

    Returns:
        active_heads: {layer_idx: [head_indices]} for active attention heads
        active_mlps:  set of layer indices with active MLP blocks
    """
    node_pruned_model.eval()

    active_heads = {}
    active_mlps = set()

    # Determine which module list holds the blocks
    if hasattr(node_pruned_model, 'transformer'):
        layers = node_pruned_model.transformer.h
    elif hasattr(node_pruned_model, 'model') and hasattr(node_pruned_model.model, 'layers'):
        layers = node_pruned_model.model.layers
    else:
        raise ValueError("Cannot locate transformer layers in the model")

    with torch.no_grad():
        for l, block in enumerate(layers):
            # -- Attention block --
            attn_active = True
            if hasattr(block, 'attention_block_gate') and block.attention_block_gate is not None:
                attn_active = (block.attention_block_gate() > 0.5).item()

            if attn_active and hasattr(block.attn, 'head_gates') and block.attn.head_gates is not None:
                mask = block.attn.head_gates() > 0.5
                heads = mask.nonzero(as_tuple=True)[0].tolist()
                if heads:
                    active_heads[l] = heads

            # -- MLP block --
            mlp_active = True
            if hasattr(block, 'mlp_block_gate') and block.mlp_block_gate is not None:
                mlp_active = (block.mlp_block_gate() > 0.5).item()
            if mlp_active:
                active_mlps.add(l)

    return active_heads, active_mlps


def save_active_nodes(active_heads, active_mlps, path):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump(
            {
                "active_heads": {str(k): v for k, v in active_heads.items()},
                "active_mlps": sorted(active_mlps),
            },
            f,
            indent=2,
        )
    print(f"Saved active nodes to {path}")


def load_active_nodes(path):
    with open(path) as f:
        data = json.load(f)
    active_heads = {int(k): v for k, v in data["active_heads"].items()}
    active_mlps = set(data["active_mlps"])
    print(f"Loaded active nodes from {path}")
    print(f"  Active heads: {sum(len(v) for v in active_heads.values())} across {len(active_heads)} layers")
    print(f"  Active MLPs: {len(active_mlps)} layers")
    return active_heads, active_mlps


# ==============================================================================
# DENSE EDGE COUNTING (no edge pruning, just surviving nodes)
# ==============================================================================

def count_dense_edges(
    active_heads: Dict[int, List[int]],
    active_mlps: Set[int],
    num_layers: int = 12,
    num_heads_per_layer: int = 12,
    verbose: bool = True,
) -> dict:
    """
    Count edges assuming dense connections between all surviving nodes.
    Mirrors the logic in edgepercent.py.

    Returns dict with total/category edge counts for both full and pruned models.
    """
    total_components_per_layer = num_heads_per_layer + 1  # heads + MLP

    # -- Full model edges --
    full_output_edges = num_layers * total_components_per_layer
    full_mlp_edges, full_qkv_edges = 0, 0
    for j in range(1, num_layers):
        n = j * total_components_per_layer
        full_mlp_edges += n
        full_qkv_edges += num_heads_per_layer * 3 * n

    total_full_original = full_output_edges + full_mlp_edges + full_qkv_edges
    total_full_extra = 1 + num_layers + num_layers * num_heads_per_layer * 6
    total_full = total_full_original + total_full_extra

    # -- Pruned model edges (dense between survivors) --
    # Matches edgepercent.py convention:
    #   "Original" edges: inter-layer connections (sources before layer j)
    #   "Extra" edges: embedding→output, MLP internal, head internal (same-layer)
    head_counts = {l: len(active_heads.get(l, [])) for l in range(num_layers)}

    # Cumulative active sources before each layer
    src_before = {}
    cum = 0
    for i in range(num_layers):
        src_before[i] = cum
        if i in active_mlps:
            cum += 1
        cum += head_counts[i]

    # Count per category
    rem_out_heads = sum(head_counts.values())
    rem_out_mlps = len(active_mlps)
    rem_output = rem_out_heads + rem_out_mlps

    rem_mlp, rem_q, rem_k, rem_v = 0, 0, 0, 0
    for j in range(num_layers):
        n = src_before[j]
        nh = head_counts[j]
        if j in active_mlps:
            rem_mlp += n
        rem_q += nh * n
        rem_k += nh * n
        rem_v += nh * n

    total_rem_original = rem_output + rem_mlp + rem_q + rem_k + rem_v

    rem_extra = 1 + len(active_mlps) + sum(head_counts.values()) * 6
    total_rem = total_rem_original + rem_extra

    result = {
        "full_total": total_full,
        "full_original": total_full_original,
        "full_extra": total_full_extra,
        "dense_total": total_rem,
        "dense_original": total_rem_original,
        "dense_extra": rem_extra,
        "dense_output": rem_output,
        "dense_mlp": rem_mlp,
        "dense_q": rem_q,
        "dense_k": rem_k,
        "dense_v": rem_v,
    }

    if verbose:
        print("\n" + "=" * 60)
        print("  DENSE EDGE COUNT (between surviving nodes)")
        print("=" * 60)
        print(f"Full model edges:  {total_full:,}")
        print(f"Dense edges:       {total_rem:,} / {total_full:,} ({total_rem / total_full:.2%})")
        print(f"  To output:  {rem_output}")
        print(f"  To MLP:     {rem_mlp}")
        print(f"  To Q:       {rem_q}")
        print(f"  To K:       {rem_k}")
        print(f"  To V:       {rem_v}")
        print(f"  Extra:      {rem_extra}")

    return result


# ==============================================================================
# EDGE CIRCUIT ANALYSIS
# ==============================================================================

def analyze_edge_circuit(model, verbose=True) -> dict:
    """
    Analyze edge pruning results. Sets model to final mode, counts active edges
    per category, and prints a detailed report.
    """
    model.eval()
    model.set_final_circuit_mode(True)

    stats = {
        "q_edges": {"total": 0, "active": 0},
        "k_edges": {"total": 0, "active": 0},
        "v_edges": {"total": 0, "active": 0},
        "mlp_edges": {"total": 0, "active": 0},
        "output_edges": {"total": 0, "active": 0},
    }
    per_receiver = {}  # key -> {q_active, k_active, v_active, total}

    with torch.no_grad():
        for key, gate in model.attn_q_gates.items():
            m = gate()
            n, a = m.numel(), int((m > 0.5).sum().item())
            stats["q_edges"]["total"] += n
            stats["q_edges"]["active"] += a
            per_receiver.setdefault(key, {})["q"] = f"{a}/{n}"

        for key, gate in model.attn_k_gates.items():
            m = gate()
            n, a = m.numel(), int((m > 0.5).sum().item())
            stats["k_edges"]["total"] += n
            stats["k_edges"]["active"] += a
            per_receiver.setdefault(key, {})["k"] = f"{a}/{n}"

        for key, gate in model.attn_v_gates.items():
            m = gate()
            n, a = m.numel(), int((m > 0.5).sum().item())
            stats["v_edges"]["total"] += n
            stats["v_edges"]["active"] += a
            per_receiver.setdefault(key, {})["v"] = f"{a}/{n}"

        for key, gate in model.mlp_edge_gates.items():
            m = gate()
            n, a = m.numel(), int((m > 0.5).sum().item())
            stats["mlp_edges"]["total"] += n
            stats["mlp_edges"]["active"] += a
            per_receiver[key] = {"mlp": f"{a}/{n}"}

        if model.output_edge_gates is not None:
            m = model.output_edge_gates()
            n, a = m.numel(), int((m > 0.5).sum().item())
            stats["output_edges"]["total"] = n
            stats["output_edges"]["active"] = a

    total_edges = sum(s["total"] for s in stats.values())
    active_edges = sum(s["active"] for s in stats.values())

    if verbose:
        print("\n" + "=" * 70)
        print("  EDGE PRUNING ANALYSIS")
        print("=" * 70)

        print(f"\nTotal edges:  {total_edges:,}")
        print(f"Active edges: {active_edges:,}")
        if total_edges > 0:
            print(f"Edge reduction: {(total_edges - active_edges) / total_edges * 100:.1f}%")
            print(f"Edge compression: {total_edges / active_edges:.2f}x" if active_edges > 0 else "Edge compression: inf")

        print(f"\nBy category:")
        for cat, s in stats.items():
            name = cat.replace("_", " ").title()
            pct = f"{s['active'] / s['total'] * 100:.1f}%" if s["total"] > 0 else "N/A"
            print(f"  {name}: {s['active']:,} / {s['total']:,} ({pct})")

        print(f"\nPer-receiver detail:")
        for key in sorted(per_receiver.keys()):
            info = per_receiver[key]
            parts = [f"{k.upper()}={v}" for k, v in sorted(info.items())]
            print(f"  {key}: {', '.join(parts)}")

    return {
        "stats": stats,
        "per_receiver": per_receiver,
        "total_edges": total_edges,
        "active_edges": active_edges,
    }


# ==============================================================================
# COMBINED REPORT
# ==============================================================================

def print_combined_report(
    node_stats: dict,
    dense_edge_stats: dict,
    edge_stats: dict,
):
    """Print the three-level compression report."""
    print("\n" + "=" * 70)
    print("  COMBINED COMPRESSION REPORT")
    print("=" * 70)

    # 1. Node compression
    if "granularity_stats" in node_stats:
        gs = node_stats["granularity_stats"]
        ah = gs.get("attention_heads", {})
        mb = gs.get("mlp_blocks", {})
        print(f"\n1. NODE COMPRESSION (from node pruning):")
        if ah.get("total", 0) > 0:
            print(f"   Attention heads: {ah['active']}/{ah['total']} active")
        if mb.get("total", 0) > 0:
            print(f"   MLP blocks:      {mb['active']}/{mb['total']} active")
        if "prunable_compression" in node_stats:
            pc = node_stats["prunable_compression"]
            print(f"   Parameter reduction: {pc['reduction_percentage']:.1f}%")

    # 2. Dense edges
    print(f"\n2. DENSE EDGE COUNT (surviving nodes, no edge pruning):")
    print(f"   Dense edges: {dense_edge_stats['dense_total']:,} / {dense_edge_stats['full_total']:,} "
          f"({dense_edge_stats['dense_total'] / dense_edge_stats['full_total']:.2%} of full model)")

    # 3. Edge compression
    print(f"\n3. EDGE COMPRESSION (after edge pruning):")
    te = edge_stats["total_edges"]
    ae = edge_stats["active_edges"]
    print(f"   Active edges: {ae:,} / {te:,}")
    if te > 0:
        print(f"   Edge reduction: {(te - ae) / te * 100:.1f}%")
    if ae > 0:
        print(f"   Edge compression: {te / ae:.2f}x")
    # Relative to full model
    full = dense_edge_stats["full_total"]
    print(f"   vs full model:  {ae:,} / {full:,} ({ae / full:.2%})")

    print("=" * 70)


# ==============================================================================
# DROPOUT UTILITY
# ==============================================================================

def disable_dropout(model: nn.Module):
    for module in model.modules():
        if isinstance(module, nn.Dropout):
            module.p = 0.0
