def main(argv=None, *, tokenizer=None, model_loader=None):
    """Lazy stage boundary; partial implementations must not silently succeed."""
    import argparse
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--experiment',required=True,choices=('directions',))
    parser.parse_known_args(argv)
    try:
        from component_analysis.a3_direction_pipeline import main as dispatch
    except ModuleNotFoundError as error:
        if error.name!='component_analysis.a3_direction_pipeline': raise
        raise ValueError('A3 direction stages are not implemented; complete runtime required') from error
    return dispatch(argv,tokenizer=tokenizer,model_loader=model_loader)
