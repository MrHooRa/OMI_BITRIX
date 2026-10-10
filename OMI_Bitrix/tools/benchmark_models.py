"""Repeatable local benchmark on anonymous engineering cases, not production accuracy."""
import argparse
import json
import os
import socket
import statistics
import sys
from pathlib import Path
from time import perf_counter
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'tests')]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--precision',choices=('fp32','int8'),default='fp32')
    parser.add_argument('--threads',type=int,default=None)
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    output=Path(args.output).resolve()
    if output.exists():raise ValueError('Choose a new output file to preserve prior measurements')
    if args.threads is not None:
        if not 1<=args.threads<=32:raise ValueError('threads must be 1..32')
        os.environ['TASK_TORCH_THREADS']=str(args.threads)
    os.environ['TASK_RERANKER_PRECISION']=args.precision
    os.environ['TASK_MODEL_MODE']='semantic'
    from semantic_engine import get_encoder,get_reranker,inference_threads
    from recommendation_matching import RelevanceIndex
    from semantic_cases import records,QUERIES
    with patch.object(socket.socket,'connect',side_effect=AssertionError('No outbound benchmark connections')):
        load=perf_counter();encoder=get_encoder();reranker=get_reranker();load_ms=(perf_counter()-load)*1000
        if encoder is None or reranker is None:raise RuntimeError('Both prepared local models are required')
        encoder.cache.clear();reranker.cache.clear()
        start=perf_counter();index=RelevanceIndex(records());build_ms=(perf_counter()-start)*1000
        timings=[];orders=[]
        for query,truth in QUERIES:
            start=perf_counter();matches=index.related(query);timings.append((perf_counter()-start)*1000)
            orders.append({'expected_subject':truth,'top_ids':[m['task']['id'] for m in matches[:3]],
                'top_subject':matches[0]['task']['group_truth'] if matches else None})
        cold=dict(reranker.stats);warm=[]
        for query,_ in QUERIES:
            start=perf_counter();index.related(query);warm.append((perf_counter()-start)*1000)
        result={'fixture_records':20,'fixture_queries':8,'precision':reranker.precision,'threads':inference_threads(),
            'startup_ms':round(load_ms,2),'build_ms':round(build_ms,2),
            'cold_total_ms':round(sum(timings),2),'cold_median_ms':round(statistics.median(timings),2),
            'warm_median_ms':round(statistics.median(warm),2),'reranker':cold,
            'warm_added_forward_items':reranker.stats['forward_items']-cold['forward_items'],
            'orders':orders,'note':'Anonymous engineering fixtures. Latency depends on hardware and other load. Not production accuracy.'}
        output.parent.mkdir(parents=True,exist_ok=True)
        output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
