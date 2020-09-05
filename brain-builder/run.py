import os
import argparse

import gpt_2_simple as gpt2

def main():
    parser = argparse.ArgumentParser(description="Create a terrible GPT-2 brain")
    parser.add_argument('brain_name', help="name of the brain to build, expects a matching .txt file in corpora/")
    parser.add_argument('--model', '-m', default='355M', dest='brain_model', help="which GPT-2 model to use, one of: 124M, 355M (default)")
    parser.add_argument('--steps', '-s', type=int, default=1000, dest='finetune_steps', help="how many steps to finetune (default: 1000)")
    args = parser.parse_args()

    if args.brain_model not in ["124M", "355M"]:
        raise("Unknown model, must be one of: 124M, 355M")
    else:
        model_name = args.brain_model

    model_dir = os.path.join(os.pardir, "jars", args.brain_name, "models")
    if not os.path.isdir(model_dir):
        print(f"Downloading {args.brain_model} model...")
        gpt2.download_gpt2(model_dir=model_dir, model_name=model_name)

    corpus = os.path.join(os.pardir, "corpora", "%s.txt" % args.brain_name)

    sess = gpt2.start_tf_sess()
    gpt2.finetune(sess,
                  corpus,
                  model_name=model_name,
                  steps=args.finetune_steps)
    gpt2.generate(sess)

if __name__ == "__main__":
    main()