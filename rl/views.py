# -- coding: utf-8 --
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.db import transaction
from django.contrib import messages
import nlpaug
import random
import string
import soundfile as sf
import nlpaug.augmenter.word as naw
import nlpaug.augmenter.char as nac
import nlpaug.augmenter.sentence as nas
import nlpaug.augmenter.audio as naa
import nltk
import librosa
from textaugment import EDA, Wordnet
import emoji
from .models import Parent, Positive, Negative
import decimal
import math
from django.conf import settings as django_settings
import os

positive_options = [
    "Text to emoji",
    "Synonym Augmentation",
    "ContextualWordEmbsAug Augmentation",
    "ContextualWordEmbsForSentenceAug Augmentation",
    "BackTranslationAug Augmentation",
    "ReservedAug Augmentation",
    "AbstSummAug Augmentation",
    "LambadaAug Augmentation"
]
negative_options = [
    "OCR Augmentation",
    "Antonym of text",
    "KeyBoard Augmentation",
    "Random Char insert",
    "Random Char swap",
    "Random Char delete",
    "SpellingAug Augmentation",
    "SplitAug Augmentation",
]


@transaction.atomic
def audio_form(request):
    positive_options = [
        "LoudnessAug",
        "PitchAug",
        "NormalizeAug",
        "SpeedAug",
        "VtlpAug",
        "PolarityInverseAug",
    ]

    negative_options = [
        "CropAug",
        "MaskAug",        
        "NoiseAug",
        "ShiftAug",
    ]

    if request.method == 'POST':
        pos_logics = request.POST.getlist('pos-logic')
        neg_logics = request.POST.getlist('neg-logic')

        upload_file = request.FILES['voice']
        wav, sr = librosa.load(upload_file)
        for logic in pos_logics:
            wav = apply_audio_pos_logic(wav, logic, sr) 
        
        for logic in neg_logics:
            wav = apply_audio_neg_logic(wav, logic, sr)

        if (pos_logics or neg_logics) and wav is not None:
            sf.write(os.path.join(django_settings.STATIC_ROOT,'augment_audio.wav'), wav, sr)
        
        return render(request, 'audio.html', { "input_text":"", "result":wav, "positive_options": positive_options, "negative_options": negative_options})

    return render(request, 'audio.html', { "input_text":"", "result":None, "positive_options": positive_options, "negative_options": negative_options})


@transaction.atomic
def my_form_post(request):
    if request.method == 'POST':
        text = request.POST.get('text')
        input_id = int(request.POST.get('input_id'))
        result = []
        pos_logics = request.POST.getlist('pos-logic')
        neg_logics = request.POST.getlist('neg-logic')

        # parent for the input text
        parent = Parent.objects.filter(sentence=text).last()
        if parent and parent.input_id!=input_id:
            messages.error(request,f'Invalid input id! Sentence exists with input id {parent.input_id}')
            return redirect('/index')
        elif not parent:
            parent = Parent.objects.create(sentence=text, input_id=input_id)

        source_text = text

        if pos_logics:
            t = None

            logics = []

            for logic in pos_logics:
                text = apply_pos_logic(logic, text, t) 
                logics.append(logic)

            if logics:
                last_positive = Positive.objects.filter(parent_id=parent.input_id).last()
                if not last_positive:
                    counter = int(parent.input_id) + 0.1
                    counter = f"P-{counter}"
                else:
                    current_counter = last_positive.positive_id.split("-")[1]
                    counter = get_next_counter(current_counter)
                    counter = f"P-{counter}"


                Positive.objects.create(sentence=text, parent_id=parent.input_id, positive_id=counter)
                parent.last_positive_id = counter
                parent.save()
                result.append([counter, text])


        elif neg_logics:
            t = None
            words = text.split(" ")
            half_txt = " ".join(words[:int(len(words) / 2)])
            rem_txt = " ".join(words[int(len(words) / 2):])
            n = int(len(words) / 2)

            logics = []
            for logic in neg_logics:
                if text:
                    text = evaluate_negative_augmentation(text, logic, t, half_txt, rem_txt, n, words)
                    if text:
                        words = text.split(" ")
                        if words:
                            half_txt = " ".join(words[:int(len(words) / 2)])
                            rem_txt = " ".join(words[int(len(words) / 2):])
                            n = int(len(words) / 2)
                            logics.append(logic)
                else:
                    text = source_text

            if logics:
                last_negative = Negative.objects.filter(parent_id=parent.input_id).last()
                if not last_negative:
                    counter = int(parent.input_id) + 0.1
                    counter = f"N-{counter}"
                else:
                    current_counter = last_negative.negative_id.split("-")[1]
                    counter = get_next_counter(current_counter)
                    counter = f"N-{counter}"

                Negative.objects.create(sentence=text, parent_id=parent.input_id, negative_id=counter)
                parent.last_negative_id = counter
                parent.save()
                result.append([counter, text])

        return render(request, 'index.html', {"input_text":source_text, "result":result, "positive_options": positive_options, "negative_options": negative_options})
    return render(request, 'index.html', {"input_text":"", "result":[], "positive_options": positive_options, "negative_options": negative_options})


# helper functions are below

def evaluate_negative_augmentation(text, neg_logic, t, half_txt, rem_txt, n, words):

    if neg_logic == "OCR Augmentation":
        return nac.OcrAug().augment(text, n=1)
    elif neg_logic == "Antonym of text":
        return naw.AntonymAug().augment(text, n=1)
    elif neg_logic == "KeyBoard Augmentation":
        return nac.KeyboardAug().augment(text, n=1)
    elif neg_logic == "Random Char insert":
        return nac.RandomCharAug('insert').augment(text, n=1)
    elif neg_logic == "Random Char swap":
        return nac.RandomCharAug('swap').augment(text, n=1)
    elif neg_logic == "Random Char delete":
        return nac.RandomCharAug('delete').augment(text, n=1)
    elif neg_logic == "SpellingAug Augmentation":
        return naw.SpellingAug().augment(text, n=1)
    elif neg_logic == "SplitAug Augmentation":
        return naw.SplitAug().augment(text, n=1)


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
    if logic == 'Text to Emoji':
        return text_to_emoji(text)
    elif logic == "Synonym Augmentation":
        return naw.SynonymAug(aug_src='wordnet').augment(text, n=1)
    elif logic == "ContextualWordEmbsAug Augmentation":
        return naw.ContextualWordEmbsAug(model_path='bert-base-uncased').augment(text, n=1)
    elif logic == "ContextualWordEmbsForSentenceAug Augmentation":
        return nas.ContextualWordEmbsForSentenceAug(max_length=10).augment(text, n=1)
    elif logic == "BackTranslationAug Augmentation":
        return naw.BackTranslationAug().augment(text, n=1)
    elif logic == "ReservedAug Augmentation":
        return naw.ReservedAug(reserved_tokens=[]).augment(text, n=1) 
    elif logic == "AbstSummAug Augmentation":
        return nas.AbstSummAug(max_length=15).augment(text, n=1) 
    elif logic == "LambadaAug Augmentation":
        return nas.LambadaAug(model_dir='gpt2', max_length=15).augment(text, n=1)           


def apply_audio_pos_logic(wav, logic, sr):
    if logic == "LoudnessAug":
        return naa.LoudnessAug().augment(wav)
    elif logic == "PitchAug":
        return naa.PitchAug(sampling_rate=sr).augment(wav)
    elif logic == "NormalizeAug":
        return naa.NormalizeAug().augment(wav)
    elif logic == "SpeedAug":
        return naa.SpeedAug().augment(wav)
    elif logic == "VtlpAug":
        return naa.VtlpAug(sampling_rate=sr).augment(wav)
    elif logic == "PolarityInverseAug":
        return naa.PolarityInverseAug().augment(wav)


def apply_audio_neg_logic(wav, logic, sr):

    if logic == "CropAug":
        return naa.CropAug(sampling_rate=sr).augment(wav)
    elif logic == "MaskAug":
        return naa.MaskAug(mask_with_noise=False).augment(wav)
    elif logic == "ShiftAug":
        return naa.ShiftAug(sampling_rate=sr).augment(wav)
    elif logic == "NoiseAug":
        return naa.NoiseAug().augment(wav)

def get_next_counter(counter):

    int_part, dec_part = counter.split(".")
    dec_part = int(dec_part)+1
    size = len(str(dec_part))
    dec_part = dec_part/(10**size)
    counter =  format(int(int_part) + dec_part, f'.{size}f')
    return counter


