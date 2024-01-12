import copy
import dill

import torch
from transformers import GPT2LMHeadModel, GPT2TokenizerFast

tokenizer = GPT2TokenizerFast.from_pretrained('distilgpt2')
model = GPT2LMHeadModel.from_pretrained('distilgpt2')
model.eval()


class PredictNode:

    def __init__(self, tokenizer_d, model_d):
        self.tokenizer = copy.copy(tokenizer_d)
        self.model = copy.copy(model_d)

    def predict(self, sentence):
        input_ids = self.tokenizer.encode(sentence, return_tensors='pt')
        with torch.no_grad():
            outputs = self.model.generate(input_ids, max_length=100, num_return_sequences=1, no_repeat_ngram_size=2)
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)


with open('gpt-2.pkl', 'wb') as f:
    dill.dump(PredictNode(tokenizer, model), f)
