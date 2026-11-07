def main(argv=None, *, tokenizer=None, model_loader=None):
    """Lazy dispatch; pure CPU fit/selection imports remain model-free."""
    from component_analysis.a3_direction_runtime import main as runtime_main
    return runtime_main(argv,tokenizer=tokenizer,model_loader=model_loader)
