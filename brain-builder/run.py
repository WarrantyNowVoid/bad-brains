import os
import json
import argparse
import datetime
import tarfile
import glob

import gpt_2_simple as gpt2

JARS_DIR = os.path.join(os.pardir, "jars")

def read_brain_conf():
    global BRAINS_LIST
    with open(os.path.join(JARS_DIR, "brains.json"), 'r') as bconf:
        BRAINS_LIST = json.loads(bconf.read())

def write_brain_conf():
    with open(os.path.join(JARS_DIR, "brains.json"), 'w') as bconf:
        bconf.write(json.dumps(BRAINS_LIST))

def main():
    parser = argparse.ArgumentParser(description="Create a terrible GPT-2 brain")
    parser.add_argument('brain_name', help="name of the brain to build, expects a matching .txt file in corpora/ if finetuning")
    parser.add_argument('--model', '-m', default='355M', dest='brain_model', help="which GPT-2 model to use, one of: 124M, 355M (default)")
    parser.add_argument('--steps', '-s', type=int, default=1000, dest='finetune_steps', help="how many steps to finetune (default: 1000)")
    parser.add_argument('--unpack', '-u', default=False, help="path to .tgz existing checkpoint to unpack instead of creating new")
    args = parser.parse_args()

    if args.brain_name == "models":
        raise ValueError("You can't name a brain `models` come on dude, be better")

    if args.brain_model not in ["124M", "355M"]:
        raise ValueError("Unknown model, must be one of: 124M, 355M")
    else:
        model_name = args.brain_model

    read_brain_conf()

    if args.brain_name in BRAINS_LIST.keys():
        raise ValueError("Already a brain with that name. Make a new one.")

    new_brain = {
        "name": args.brain_name,
        "model": model_name,
        "ready": False,
        "finetuned": 0
    }
    BRAINS_LIST[args.brain_name] = new_brain
    write_brain_conf()

    try:
        if args.unpack:
            print("Unpacking %s..." % args.brain_name)
            if tarfile.is_tarfile(args.unpack):
                checkpoint_dir = os.path.join(JARS_DIR, args.brain_name)
                tgz = tarfile.open(args.unpack)
                dir_contains_checkpoint = False
                innerpath = os.path.commonprefix(tgz.getnames())
                if not innerpath.startswith("checkpoint"):
                    checkpoint_dir = os.path.join(checkpoint_dir, "checkpoint")
                
                tgz.extractall(path=checkpoint_dir)
                checkpoint_dir = os.path.join(checkpoint_dir, "checkpoint")

                with open(glob.glob(os.path.join(checkpoint_dir, "**", "counter"))[0], 'r') as cfile:
                    finetuned = int(cfile.read().strip())
            else:
                raise ValueError("Not a valid tar file: %s" % args.unpack)
        else:
            model_dir = os.path.join(JARS_DIR, "models")
            checkpoint_dir = os.path.join(JARS_DIR, args.brain_name, "checkpoint")
            if not os.path.isdir(model_dir):
                print("Downloading %s model..." % model_name)
                gpt2.download_gpt2(model_dir=model_dir, model_name=model_name)

            corpus = os.path.join(os.pardir, "corpora", "%s.txt" % args.brain_name)

            print("Finetuning %s..." % args.brain_name)
            sess = gpt2.start_tf_sess()
            gpt2.finetune(sess,
                          corpus,
                          model_name=model_name,
                          model_dir=model_dir,
                          checkpoint_dir=checkpoint_dir,
                          steps=args.finetune_steps,
                          sample_every=0)
            finetuned = args.finetune_steps

        BRAINS_LIST[args.brain_name]["ready"] = int(finetuned) > 0
        BRAINS_LIST[args.brain_name]["finetuned"] = finetuned
        write_brain_conf()
    except BaseException as error:
        BRAINS_LIST.pop(args.brain_name, None)
        write_brain_conf()

        raise error

if __name__ == "__main__":
    BRAINS_LIST = {}
    main()