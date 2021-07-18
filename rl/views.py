# -- coding: utf-8 --
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from .forms import *
from django.db import transaction
import nlpaug
import random
import string
import nlpaug.augmenter.word as naw
import nlpaug.augmenter.char as nac
import nltk
from textaugment import EDA, Wordnet
import emoji
from .models import Parent, Positive, Negative
import decimal

positive_options = [
    "Random word swap",
    "Random word delete",
    "Random word insert",
    "Synonym Augmentation",
    "OCR Augmentation",
    "KeyBoard Augmentation",
    "Random Char insert",
    "Random Char swap",
    "Random Char delete",
]
negative_options = [
    "Text to emoji",
    "Antonym of text",
    "Insert sentence",
    "Special character insertion",
    "Swap in the sentence",
    "Sentence insertion",
]

@transaction.atomic
def my_form_post(request):
    if request.method == 'POST':
        text = request.POST.get('text')
        result = []
        pos_logics = request.POST.getlist('pos-logic')
        neg_logics = request.POST.getlist('neg-logic')

        # parent for the input text
        parent, _ = Parent.objects.get_or_create(sentence=text)

        if pos_logics:
            t = EDA()
            last_positive = Positive.objects.filter(parent_id=parent.id).last()
            counter = round(last_positive.positive_id, 1) if last_positive else 1.0
            new_records = []

            for logic in pos_logics:
                logic_res = apply_pos_logic(logic, text, t)
                counter+=0.1
                new_records.append(Positive(sentence=logic_res, parent_id=parent.id, positive_id=counter))
                result.append([logic, logic_res])
            Positive.objects.bulk_create(new_records)
            parent.last_positive_id = counter
            parent.save()

        elif neg_logics:
            t = EDA()
            words = text.split(" ")
            half_txt = " ".join(words[:int(len(words) / 2)])
            rem_txt = " ".join(words[int(len(words) / 2):])
            n = int(len(words) / 2)
            
            last_negative = Negative.objects.filter(parent_id=parent.id).last()
            counter = round(last_negative.negative_id, 1) if last_negative else 1.0
            new_records = []
            for logic in neg_logics:
                logic_res = evaluate_negative_augmentation(text, logic, t, half_txt, rem_txt, n, words)
                if logic_res:
                    counter+=0.1
                    new_records.append(Negative(sentence=logic_res, parent_id=parent.id, negative_id=counter))
                    result.append([logic, logic_res])
            Negative.objects.bulk_create(new_records)
            parent.last_negative_id = counter
            parent.save()

        return render(request, 'index.html', {"input_text":text, "result":result, "positive_options": positive_options, "negative_options": negative_options})
    return render(request, 'index.html', {"input_text":"", "result":[], "positive_options": positive_options, "negative_options": negative_options})


# helper functions are below

def evaluate_negative_augmentation(text, neg_logic, t, half_txt, rem_txt, n, words):
    # 0. replace with emojis
    if neg_logic == "Text to emoji":
        return text_to_emoji(text)
    # 1. make antonym of whole text
    elif neg_logic == "Antonym of text":
        return naw.AntonymAug().augment(text, n=1)
    # 2. insert n words in the half sentence, where n = half of size of sentence
    elif neg_logic == "Insert sentence":
        try:
            rand_index = random.randint(0, n)
            return t.random_insertion(sentence=words[rand_index], n=n) + " " + rem_txt
        except:
            pass
    # 3. make antonym of whole text and insert a special character at any position
    elif neg_logic == "Special character insertion":
        return get_with_special_char(text)
    # 4. swap half of the sentence
    elif neg_logic == "Swap in the sentence":
        return t.random_swap(half_txt) + " " + rem_txt
    # 5. insert one random word in half text
    elif neg_logic == "Sentence insertion":
        return t.random_insertion(half_txt) + " " + rem_txt


def get_with_special_char(text):
    """
    replace char in text
    """
    # get random indexes to be replaced with special characters which will be 35% of sentence but not more than 15 chars
    indexes = random.sample(range(0, len(text)), min(round(len(text) * 35 / 100), 15))
    for index in indexes:
        text = text[:index] + random.choice(string.punctuation) + text[index + 1:]

    return text


def text_to_emoji(text):
    """
    Replaces words with possible emojis.
    """
    text = text.replace(",", "").replace(".", "")
    new_sentence = " ".join([":" + s + ":" for s in text.split(" ")])
    emojized = emoji.emojize(new_sentence, use_aliases=True).split(" ")

    sent = []
    for each in emojized:
        if each in emoji.UNICODE_EMOJI['en']:
            sent.append(each)
        else:
            sent.append(each.replace(":", ""))
    return " ".join(sent)


def apply_pos_logic(logic, text, t):
    if logic == "Random word swap":
        return t.random_swap(text)
    elif logic == "Random word delete":
        return t.random_deletion(text, p=0.3)
    elif logic == "Random word insert":
        return t.random_insertion(text)
    elif logic == "Synonym Augmentation":
        return naw.SynonymAug(aug_src='wordnet').augment(text, n=1)
    elif logic == "OCR Augmentation":
        return nac.OcrAug().augment(text, n=1)
    elif logic == "KeyBoard Augmentation":
        return nac.KeyboardAug().augment(text, n=1)
    elif logic == "Random Char insert":
        return nac.RandomCharAug('insert').augment(text, n=1)
    elif logic == "Random Char swap":
        return nac.RandomCharAug('swap').augment(text, n=1)
    elif logic == "Random Char delete":
        return nac.RandomCharAug('delete').augment(text, n=1)


