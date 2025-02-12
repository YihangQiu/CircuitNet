# Copyright 2022 CircuitNet. All rights reserved.

from __future__ import print_function

import os
import os.path as osp
import numpy as np

from tqdm import tqdm

from datasets.build_dataset import build_dataset
from metrics import build_metric, build_roc_prc_metric
from models.build_model import build_model
from utils.configs import Paraser


def test():
    argp = Paraser()
    arg = argp.parser.parse_args()
    arg_dict = vars(arg)

    arg_dict['ann_file'] = arg.ann_file_test if arg.pretrained else arg.ann_file_train
    arg_dict['test_mode'] = bool(arg.pretrained)

    print('===> Loading datasets')
    # Initialize dataset
    dataset = build_dataset(arg_dict)

    print('===> Building model')
    # Initialize model parameters
    model = build_model(arg_dict)
    model = model.cuda()

    # Build metrics
    metrics = {k:build_metric(k) for k in arg.eval_metric}
    avg_metrics = {k:0 for k in arg.eval_metric}

    count =0
    with tqdm(total=len(dataset)) as bar:
        for feature, label, label_path in dataset:
            input, target = feature.cuda(), label.cuda()

            prediction = model(input)
            for metric, metric_func in metrics.items():
                avg_metrics[metric] += metric_func(target.cpu(), prediction.squeeze(1).cpu())

            if arg.save_as_npy:
                save_path = osp.join(arg.save_path, 'test_result')
                if not os.path.exists(save_path):
                    os.makedirs(save_path)
                file_name = osp.splitext(osp.basename(label_path[0]))[0]
                save_path = osp.join(save_path, f'{file_name}.npy')
                output_final = prediction.float().detach().cpu().numpy()
                np.save(save_path, output_final)
                count +=1

            bar.update(1)
    
    for metric, avg_metric in avg_metrics.items():
        print("===> Avg. {}: {:.4f}".format(metric, avg_metric / len(dataset))) 

    # eval roc&prc
    if arg.save_as_npy:
        roc_metric, prc_metric = build_roc_prc_metric(**arg_dict)
        print("\n===> AUC of ROC. {:.4f}".format(roc_metric))
        print("===> AUC of PR. {:.4f}".format(prc_metric))


if __name__ == "__main__":
    test()
