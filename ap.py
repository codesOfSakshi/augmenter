import nlpaug.augmenter.word as naw

naw.ContextualWordEmbsAug(model_path='bert-base-uncased').augment("sdsdsd sdsdsds sdsd", n=1)